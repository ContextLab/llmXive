# Implementation Plan: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

**Branch**: `001-semantic-collapse-threshold` | **Date**: 2026-09-26 | **Spec**: [spec.md](../specs/001-semantic-collapse-threshold/spec.md)  
**Input**: Feature specification from `/specs/001-semantic-collapse-threshold/spec.md`

## Summary
The project will (0) run a power‑analysis and human‑validation gate (FR‑011, FR‑016, FR‑032); (1) download a stratified ≥ 50 000‑clip subset of **Voices‑in‑the‑Wild‑2M** (FR‑001); (2) generate 54 compound distortion scenarios per clip on a paid GPU cluster (FR‑002, FR‑024); (3) compute Semantic Similarity Scores (SSS) with `all‑MiniLM‑L6‑v2` and fall back to phoneme‑edit distance for high‑reverb clips (FR‑022); (4) (FR‑018) **cannot be satisfied** because the DNS‑Challenge dataset lacks a verified source; we will instead use a small subset of naturally reverberant clips from Voices‑in‑the‑Wild‑2M as a proxy and note the limitation; (5) fit splines to each stress curve, extract inflection points and apply the deterministic CCM algorithm (FR‑012, FR‑020, FR‑021, FR‑053, FR‑036, FR‑010); (6) train a hierarchical mixed‑effects regression model to predict inflection steps from acoustic parameters and transcript‑difficulty (FR‑005, FR‑025, FR‑028); (7) evaluate regression performance (R² ≥ 0.6) and run a permutation baseline (FR‑027); (8) test non‑linear interaction significance with Benjamini‑Hochberg correction (FR‑013, FR‑008); (9) conduct a sensitivity analysis over SSS thresholds and WER multipliers (FR‑006, SC‑002); (10) compute partial‑correlations controlling for baseline WER (FR‑035); (11) assess universality of the critical interaction vectors across ASR models (FR‑051); (12) validate all Parquet outputs against JSON schemas (FR‑030, FR‑031, FR‑034); (13) generate a reproducible report with strictly associational language (FR‑007).

All CPU‑tractable analyses run on the free‑tier GitHub Actions runner; GPU‑only distortion generation is off‑loaded to a paid 4‑node V100 cluster (real CUDA work, no CPU approximation).  

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `datasets`, `pyroomacoustics`, `torch`, `transformers`, `scikit‑learn`, `statsmodels`, `pyarrow`, `pandas`, `shap`, `hydra-core`, `mlflow`  
- **Storage**: File‑system Parquet files under `data/derived/`  
- **Testing**: `pytest` with a `tests/unit/` suite (includes contract validation)  
- **Target Platform**: Linux GitHub Actions runner (CPU‑first) + paid GPU cluster for distortion generation  
- **Performance Goals**: Full stress‑test pipeline ≤ 48 h on the GPU cluster; downstream analysis ≤ 6 h on CI CPU runner (< 7 GB RAM)  
- **Constraints**: FR‑007 (associational framing), FR‑008 (Benjamini‑Hochberg FDR ≤ 0.05), FR‑010 (absolute SSS ≤ 0.5), FR‑016 (human‑validation gate), FR‑017 (log missing scenarios), FR‑023 (pre‑defined parameters), FR‑028 (transcript‑difficulty covariate), FR‑032 (power analysis), FR‑036 (universal intensity), FR‑051 (universality test), FR‑053 (spline inflection), FR‑054 (not present).  

## Constitution Check
| Principle | Check |
|-----------|-------|
| I. Reproducibility | Random seeds pinned; dataset URLs fixed; pipeline orchestrated via Hydra config |
| II. Verified Accuracy | All citations limited to the two verified datasets (Voices‑in‑the‑Wild‑2M, DNS‑Challenge – note DNS not verified, see FR‑018 limitation) |
| III. Data Hygiene | Checksums recorded; transformations produce new files; no PII |
| IV. Single Source of Truth | `data-model.md` is the authoritative schema; every figure/table traces back to a row in `data/derived/*` and a line in `code/` |
| V. Versioning Discipline | Artifact hashes stored in `state/projects/…yaml` |
| VI. Non‑Linear Interaction Characterization | Interaction terms explicitly modeled and reported |
| VII. CPU‑Tractability and Diagnostic Efficiency | Regression, SHAP, statistical tests run on CPU; distortion generation runs on genuine GPU cluster (off‑loaded) |

All principles satisfied → **Gate passed**.

## Project Structure
```
specs/001-semantic-collapse-threshold/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── collapse_point.schema.yaml
    ├── critical_vector.schema.yaml
    └── stress_curve.schema.yaml

src/
├── pipeline/
│   ├── __init__.py
│   ├── download.py
│   ├── distort.py
│   ├── sss.py
│   ├── collapse.py
│   ├── train_regressor.py
│   └── evaluate.py
└── utils/
    └── logging.py

tests/
├── unit/
│   ├── __init__.py
│   ├── test_download.py
│   ├── test_collapse.py
│   └── test_contracts.py
└── conftest.py
```

## Phase Mapping (FR / SC → Plan Steps)

| Phase | FR / SC | Description |
|-------|---------|-------------|
| **Phase 0 – Power & Human Gate** | FR‑011, FR‑016, FR‑023, FR‑032 | Compute required N via G*Power (≈ 395); collect ≥ 1 000 human‑annotated transcripts (≥ 3 raters each) from Voices‑in‑the‑Wild‑2M; compute SSS AUC‑ROC ≥ 0.85; abort if both SSS and phoneme‑edit fallback fail (FR‑016). |
| **Phase 1 – Data Acquisition** | FR‑001, FR‑018 (limited) | Download Voices‑in‑the‑Wild‑2M (≥ 50 k stratified clips); compute checksums. **FR‑018**: DNS‑Challenge not verified → use a proxy subset of naturally reverberant clips from Voices‑in‑the‑Wild‑2M; document limitation. |
| **Phase 2 – Stress‑Curve Generation** | FR‑002, FR‑003, FR‑022, FR‑024, FR‑017 | Split 50 k IDs into four GPU shards; each shard runs on a V100 node (`pyroomacoustics`) applying the 54 SNR × RT60 vectors to each clip for five ASR models. Compute SSS with `all‑MiniLM‑L6‑v2`; for clips with RT60 > 0.5 s and low embedding correlation, compute phoneme‑edit distance (FR‑022). Log missing distortion scenarios (FR‑017). |
| **Phase 3 – Curve Shape & Collapse Identification** | FR‑012, FR‑020, FR‑021, FR‑053, FR‑036, FR‑010 | Fit a smooth spline to each stress curve, extract maximum negative derivative (inflection step) and its coordinate (FR‑053). Apply deterministic CCM algorithm and linear interpolation (FR‑021, FR‑020). Record Universal Collapse Intensity where absolute SSS ≤ 0.5 (FR‑036, FR‑010). Store results in `collapse_points.parquet`. |
| **Phase 4 – Regression Modeling** | FR‑005, FR‑025, FR‑028, FR‑027 | Train a hierarchical mixed‑effects regression to predict **inflection_step** (target) from SNR, RT60, quadratic & interaction terms, baseline WER, and transcript‑perplexity. Use an 80/20 stratified split (speaker + distortion + difficulty) and 5‑fold CV. Evaluate on held‑out set (R² ≥ 0.6, MAE reported). Perform permutation baseline (ΔR² ≥ 0.20). |
| **Phase 5 – Interaction Significance, Sensitivity, Partial Correlation, Universality** | FR‑006, FR‑008, FR‑013, FR‑035, FR‑051 | (a) Sweep SSS thresholds {0.45, 0.50, 0.55} and WER multipliers {1.5, 2.0, 2.5}; compute coefficient‑of‑variation ≤ 0.10 (SC‑002). (b) Fit additive linear model; compare to full interaction model; test interaction term (p < 0.05) and apply Benjamini‑Hochberg FDR ≤ 0.05 (FR‑013, FR‑008). (c) Partial‑correlation of acoustic predictors with inflection_step controlling for baseline WER (FR‑035). (d) Derive a **critical interaction vector** per ASR model from regression coefficients; compute cosine similarity ≥ 0.80 across models and permutation test (observed > 95th percentile) (FR‑051). |
| **Phase 6 – Validation & Export** | FR‑030, FR‑031, FR‑034 | Validate `collapse_points.parquet` against `contracts/collapse_point.schema.yaml` and `critical_vector.parquet` against `contracts/critical_vector.schema.yaml`. Abort on any schema violation. |
| **Phase 7 – Reporting** | FR‑007, SC‑001 – SC‑009 | Generate figures, tables, and a Markdown report. All statements use associational phrasing only (FR‑007). Report metrics: R², MAE, sensitivity CV, interaction FDR‑corrected p‑values, partial‑correlation coefficients, universality similarity, human‑validation AUC‑ROC, etc. |

All functional requirements (FR‑001 – FR‑036, FR‑051, FR‑053) and success criteria (SC‑001 – SC‑009) are covered.

---
