# Implementation Plan: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

**Branch**: `001-semantic-collapse-threshold` | **Date**: 2026-09-26 | **Spec**: [spec.md](../specs/001-semantic-collapse-threshold/spec.md)  
**Input**: Feature specification from `/specs/001-semantic-collapse-threshold/spec.md`

## Summary
The project will (0) **perform a power analysis and human‑validation gate** (FR‑011, FR‑016, FR‑032); (1) **download** a stratified **≥ 50,000**‑clip subset of the **Voices‑in‑the‑Wild‑2M** dataset (FR‑001); (2) **generate** **54** compound acoustic distortion scenarios per clip using a **paid multi‑node V100 GPU cluster** (FR‑002, FR‑003, FR‑024); (3) **compute** Semantic Similarity Scores (SSS) with `all‑MiniLM‑L6‑v2` and fall back to phoneme‑edit distance when embedding correlation < 0.85 (FR‑022); (4) **validate** synthetic distortions against real‑world DNS‑Challenge clips via LMSD ≤ 0.15 (FR‑018); (5) **fit a smooth spline** to each stress curve, **extract the maximum negative derivative** (inflection step) and **early‑collapse flag** (FR‑012, FR‑053); (6) **identify deterministic collapse points** using the Composite Collapse Metric (CCM) and deterministic interpolation (FR‑021, FR‑020); (7) **compute** **Universal Collapse Intensity** where absolute SSS ≤ 0.5 (FR‑010, FR‑036); (8) **train a hierarchical mixed‑effects regression model** to predict the **inflection step** and **early‑collapse flag** (not the deterministic intensity) from acoustic parameter vectors (including engineered interaction terms) while controlling for baseline WER and transcript‑difficulty (FR‑005, FR‑025, FR‑028); (9) **evaluate** regression performance on a stratified held‑out test set (80/20 split) with 5‑fold CV, report R² ≥ 0.6 and MAE, and run a permutation baseline test (ΔR² ≥ 0.20) (FR‑027); (10) **conduct** a non‑linear interaction significance test against an additive model, applying Benjamini‑Hochberg FDR ≤ 0.05 (FR‑013, FR‑008); (11) **perform** a sensitivity analysis over SSS thresholds and WER multipliers, reporting coefficient‑of‑variation ≤ 0.10 (FR‑006, SC‑002); (12) **compute** partial‑correlation between acoustic predictors and inflection step while controlling for baseline WER (FR‑035); (13) **assess universality** of the **critical interaction vectors** derived from regression coefficients across models using cosine similarity ≥ 0.80 and a permutation test on model labels (FR‑051); (14) **validate** all output Parquet artifacts against their JSON schemas (FR‑030, FR‑031, FR‑034); (15) **generate** reproducible figures and a manuscript with explicit **associational framing** (FR‑007). All CPU‑only steps run on the free‑tier GitHub Actions runner; GPU‑only distortion generation runs on a paid 4‑node V100 cluster (≤ 48 h).  

## Technical Context

- **Language/Version**: Python 3.11
- **Primary Dependencies**: `datasets`, `pyroomacoustics`, `torch`, `transformers`, `scikit‑learn`, `statsmodels`, `pyarrow`, `pandas`, `shap`, `hydra-core`, `mlflow`
- **Storage**: File‑system Parquet files under `data/derived/`
- **Testing**: `pytest` with a `tests/unit/` suite (includes contract validation)
- **Target Platform**: Linux GitHub Actions runner (CPU‑first) + paid GPU cluster for distortion generation
- **Performance Goals**: Complete the full stress‑test pipeline within **48 h** on the 4‑node GPU cluster; all downstream analysis must run on the CI CPU runner (<7 GB RAM, ≤6 h)
- **Constraints**: Must obey FR‑007 (associational framing), FR‑008 (Benjamini‑Hochberg FDR ≤ 0.05), FR‑010 (absolute SSS ≤ 0.5), FR‑016 (gate on human validation), FR‑017 (log missing scenarios), FR‑018 (real‑world validation), FR‑023 (pre‑defined parameters), FR‑028 (baseline WER covariate), FR‑032 (power analysis), FR‑036 (universal intensity), FR‑051 (universality test), FR‑053 (spline inflection), FR‑054 (not present).

## Constitution Check

| Principle | Check |
|-----------|-------|
| I. Reproducibility | All random seeds pinned; dataset URLs fixed; pipeline orchestrated via Hydra config |
| II. Verified Accuracy | All external citations limited to the “Verified Datasets” table |
| III. Data Hygiene | Checksums recorded; every transformation writes a new file; no PII |
| IV. Single Source of Truth | **`data-model.md`** is designated as the authoritative description of all derived tables; every figure/table traces back to a row in `data/derived/*` and a line in `code/` |
| V. Versioning Discipline | Artifact hashes stored in `state/projects/…yaml` |
| VI. Non‑Linear Interaction Characterization | Interaction terms explicitly modeled and reported |
| VII. CPU‑Tractability and Diagnostic Efficiency | Regression, SHAP, and statistical tests run on CPU; distortion generation runs on paid GPU cluster |

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
    ├── collapse_points.schema.yaml
    ├── critical_vector.schema.yaml
    ├── dataset.schema.yaml
    ├── regression_input.schema.yaml
    ├── regression_result.schema.yaml
    ├── stress_curve.schema.yaml
    └── stress_curves.schema.yaml

src/
├── pipeline/
│   ├── __init__.py
│   ├── download.py
│   ├── distort.py
│   ├── sss.py
│   �├── collapse.py
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
| **Phase 0 – Power & Human Gate** | FR‑011, FR‑016, FR‑023, FR‑032 | Compute required N (≈ 395) using G*Power (effect = 0.02, α = 0.05, power = 0.80) → confirms 50 k ≫ 395. Collect ≥ 1 000 human‑annotated transcripts (≥ 3 raters each) from Voices‑in‑the‑Wild‑2M. Compute SSS AUC‑ROC; if `< 0.85`, switch to phoneme‑edit distance for high‑reverb clips (FR‑022). Abort if both fail. |
| **Phase 1 – Data Acquisition** | FR‑001, FR‑018 | Download Voices‑in‑the‑Wild‑2M (≥ 50 k stratified clips) and DNS‑Challenge (≥ 50 real‑world noisy clips). Verify checksums; compute speaker/environment stratification. |
| **Phase 2 – Stress‑Curve Generation** | FR‑002, FR‑003, FR‑022, FR‑024, FR‑017, FR‑018 | Split the 50 k IDs into **four** GPU‑node shards (≈ 12.5 k clips each). Each shard runs on a V100 node (`pyroomacoustics`) applying the 54 distortion vectors (9 SNR × 6 RT60) per clip across five small ASR models. Compute SSS with `all‑MiniLM‑L6‑v2`; for clips where RT60 > 0.5 s **and** embedding AUC‑ROC < 0.85, compute phoneme‑edit distance (FR‑022). Log any missing distortion scenarios (FR‑017). |
| **Phase 3 – Curve Shape & Collapse Identification** | FR‑012, FR‑020, FR‑021, FR‑053, FR‑036, FR‑010 | Fit a smooth spline to each stress curve, extract the **maximum negative derivative** (inflection step) and its coordinate (FR‑053). Apply deterministic CCM algorithm and interpolation rule (FR‑021, FR‑020) to obtain **collapse_intensity** and **early_collapse_flag**. Compute **Universal Collapse Intensity** where absolute SSS ≤ 0.5 (FR‑010, FR‑036). Store results in `data/derived/collapse_points.parquet`. |
| **Phase 4 – Regression Modeling** | FR‑005, FR‑025, FR‑028, FR‑027 | Train a **hierarchical mixed‑effects regression** (random intercepts per ASR model) to predict **inflection_step** and **early_collapse_flag** using predictors: SNR, RT60, SNR², RT60², interaction (SNR × RT60), baseline WER, transcript‑perplexity (FR‑028). Use an 80/20 stratified split (speaker + distortion + difficulty) and 5‑fold CV within training. Evaluate on held‑out set (R² ≥ 0.6, MAE reported). Perform permutation baseline (shuffle acoustic vectors) and require ΔR² ≥ 0.20 (FR‑027). |
| **Phase 5 – Interaction Significance, Sensitivity, Partial Correlation, Universality** | FR‑006, FR‑008, FR‑013, FR‑035, FR‑051 | (a) Sensitivity grid over SSS thresholds {low, medium, high} and WER multipliers {1.5, 2, 2.5}; compute coefficient‑of‑variation ≤ 0.10 (SC‑002). (b) Fit additive linear model; compare to full interaction model; test interaction term significance (p < 0.05) and apply Benjamini‑Hochberg FDR ≤ 0.05 (FR‑013, FR‑008). (c) Partial‑correlation of acoustic predictors with inflection_step controlling for baseline WER (FR‑035). (d) Universality: compute a **critical interaction vector** from regression coefficients for each ASR model, compute cosine similarity across models (≥ 0.80) and run permutation test shuffling model labels (observed > 95th percentile) (FR‑051). |
| **Phase 6 – Validation & Export** | FR‑030, FR‑031, FR‑034 | Validate `collapse_points.parquet` against `contracts/collapse_point.schema.yaml` and `critical_vector.parquet` against `contracts/critical_vector.schema.yaml`. Abort on any schema violation. |
| **Phase 7 – Reporting** | FR‑007, SC‑001 – SC‑009 | Generate figures, tables, and a Markdown report. All language explicitly frames findings as **associational** (FR‑007). Report performance metrics (R², MAE, sensitivity CV, interaction FDR‑corrected p‑values, partial‑correlation coefficients, universality similarity). |

### Additional Cross‑Referenced Steps

- **FR‑006** (Sensitivity analysis) is executed in Phase 5 and its results feed the robustness check for SC‑002.
- **FR‑008** (Benjamini‑Hochberg FDR) is applied to all interaction‑effect tests in Phase 5.
- **FR‑010** (Absolute SSS threshold) is enforced in Phase 3 for Universal Collapse Intensity.
- **FR‑013** (Non‑linear interaction validation) is performed in Phase 5.
- **FR‑018** (Real‑world validation) is part of Phase 2.
- **FR‑020** (Deterministic interpolation) is part of Phase 3.
- **FR‑021** (Deterministic collapse algorithm) is core of Phase 3.
- **FR‑022** (Phoneme fallback) is integrated in Phase 2.
- **FR‑023** (Parameter definition) is documented in Phase 0.
- **FR‑024** (Cartesian product) is part of Phase 2.
- **FR‑025** (Hierarchical regression) is Phase 4.
- **FR‑028** (Covariates) is Phase 4 (baseline WER retained, baseline SSS removed to avoid leakage).
- **FR‑030 / FR‑031** (Artifact paths) are Phase 6.
- **FR‑034** (Schema validation) is Phase 6.
- **FR‑035** (Partial‑correlation) is Phase 5.
- **FR‑036** (Universal intensity) is Phase 3/4.
- **FR‑051** (Universality assessment) is Phase 5.
- **FR‑053** (Spline inflection) is Phase 3.

All functional requirements (FR‑001 – FR‑036, FR‑051, FR‑053) and success criteria (SC‑001 – SC‑009) are covered by the above phases.

---



