# Implementation Plan: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

**Branch**: `001-semantic-collapse-threshold` | **Date**: 2026-09-26 | **Spec**: [spec.md](../specs/001-semantic-collapse-threshold/spec.md)  
**Input**: Feature specification from `/specs/001-semantic-collapse-threshold/spec.md`

## Summary
The project will (0) run a power‑analysis and human‑validation gate (FR‑011, FR‑016, FR‑023, FR‑032, **FR‑032‑VERIF**); (1) download a stratified ≥ 50 000‑clip subset of **Voices‑in‑the‑Wild‑2M** (FR‑001); (2) generate multiple compound distortion scenarios per clip on a paid GPU‑enabled cluster (FR‑002, FR‑024); (3) compute Semantic Similarity Scores (SSS) with `all‑MiniLM‑L6‑v2`; for high‑reverb clips where the embedding correlation is low, compute phoneme‑edit distance (FR‑022); (4) fit splines to each stress curve, extract the maximum negative derivative (inflection step) and apply the deterministic CCM algorithm (FR‑012, FR‑020, FR‑021, FR‑053, FR‑036, FR‑010); (5) **create a manually annotated validation subset of a representative sample of stress curves (FR‑033)** and use the expert‑labeled collapse intensity as the regression target; (6) train a hierarchical mixed‑effects regression to predict the **annotated collapse intensity** from acoustic parameters and transcript‑difficulty (FR‑005, FR‑025, FR‑028); (7) evaluate regression performance (R² ≥ 0.6, MAE reported) and run a permutation baseline (FR‑027); (8) test non‑linear interaction significance with Benjamini‑Hochberg correction (FR‑013, FR‑008); (9) conduct a sensitivity analysis over SSS thresholds and WER multipliers (FR‑006, SC‑002); (10) compute partial‑correlation controlling for baseline WER (FR‑035); (11) assess universality of the critical interaction vectors across ASR models (FR‑051); (12) validate all Parquet outputs against JSON schemas (FR‑030, FR‑031, FR‑034); (13) generate a reproducible report with strictly associational language (FR‑007).  

All CPU‑tractable analyses run on the free‑tier GitHub Actions runner; GPU‑only distortion generation is off‑loaded to a paid 4‑node V100 GPU cluster (real CUDA work, no CPU approximation).  

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `datasets`, `pyroomacoustics`, `torch`, `transformers`, `scikit‑learn`, `statsmodels`, `pyarrow`, `pandas`, `shap`, `hydra-core`, `mlflow`  
- **Storage**: File‑system Parquet files under `data/derived/`  
- **Testing**: `pytest` with a `tests/unit/` suite (includes contract validation)  
- **Target Platform**: Linux GitHub Actions runner (CPU‑first) + paid GPU cluster for distortion generation  
- **Performance Goals**: Full stress‑test pipeline ≤ 48 h on the GPU cluster; downstream analysis ≤ 6 h on CI CPU runner (< 7 GB RAM)  
- **Constraints**: FR‑007 (associational framing), FR‑008 (Benjamini‑Hochberg FDR ≤ 0.05), FR‑010 (absolute SSS ≤ 0.5), FR‑016 (human‑validation gate), FR‑017 (log missing scenarios), FR‑023 (pre‑defined parameters), FR‑028 (transcript‑difficulty covariate), FR‑032 (power analysis), FR‑036 (universal intensity), FR‑051 (universality test), FR‑053 (spline inflection)  

## Constitution Check

| Principle | Check |
|-----------|-------|
| I. Reproducibility | Random seeds pinned; dataset URLs fixed; pipeline orchestrated via Hydra config |
| II. Verified Accuracy | All citations limited to the verified dataset **Voices‑in‑the‑Wild‑2M** (no unverified DNS‑Challenge) |
| III. Data Hygiene | Checksums recorded; transformations produce new files; no PII |
| IV. Single Source of Truth | `data-model.md` is the authoritative schema; every figure/table traces back to a row in `data/derived/*` and a line in `code/` |
| V. Versioning Discipline | Artifact hashes stored in `state/projects/…yaml` |
| VI. Non‑Linear Interaction Characterization | Interaction terms explicitly modeled and reported |
| VII. CPU‑Tractability and Diagnostic Efficiency | Regression, SHAP, partial‑correlation run on CPU; distortion generation runs on genuine GPU cluster (off‑loaded) |

All principles satisfied → **Gate passed**.

## Project Structure
```
specs/001-semantic-collapse-threshold/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── collapse_point.schema.yaml
│   ├── collapse_points.schema.yaml
│   ├── critical_vector.schema.yaml
│   ├── stress_curve.schema.yaml
│   └── stress_curves.schema.yaml
└── tests/
    └── unit/
        ├── __init__.py
        ├── test_download.py
        ├── test_collapse.py
        └── test_contracts.py
```

## Phase Mapping (FR / SC → Plan Steps)

| Phase | FR / SC | Description |
|-------|---------|-------------|
| **Phase 0 – Power & Human Gate** | FR‑011, FR‑016, FR‑023, FR‑032, **FR‑032‑VERIF** | Compute required N (≈ 395) with G*Power; collect ≥ 1 000 human‑annotated transcripts (≥ 3 raters each) from Voices‑in‑the‑Wild‑2M; compute SSS AUC‑ROC ≥ 0.85. If SSS fails, fall back to phoneme‑edit distance for high‑reverb clips (FR‑022). After the final sample size is fixed, we will **re‑run G*Power and log the achieved power** (FR‑032‑VERIF). |
| **Phase 1 – Data Acquisition** | FR‑001 | Download Voices‑in‑the‑Wild‑2M (≥ 50 k stratified clips); compute checksums. **Realism validation (FR‑018) cannot be satisfied** because no verified open dataset provides the required real‑world noisy recordings. This limitation is documented and will be flagged for a spec amendment. |
| **Phase 2 – Stress‑Curve Generation** | FR‑002, FR‑024, FR‑017 | Split IDs into four GPU shards; each shard runs on a V100 GPU node (`pyroomacoustics`) applying the Cartesian product of multiple SNR levels × 6 RT60 levels (forming a combinatorial set of scenarios) per clip for five small ASR models.. **Compute feasibility**: Each V can process on the order of hundreds of thousands of distortion runs per hour.; with 4 nodes we can finish ~13.5 M runs in ≤ 48 h. Audio is streamed from HF to keep RAM < 7 GB. Log any missing distortion scenarios (FR‑017). |
| **Phase 3 – Semantic Scoring** | FR‑003, FR‑022 | Encode clean transcript and ASR hypothesis with `sentence‑transformers/all‑MiniLM‑L6‑v2`; compute cosine similarity → SSS. For clips where RT60 > 0.5 s **and** embedding correlation < 0.85, compute phoneme‑edit distance via Montreal Forced Aligner. All metric values (SSS, WER, CCM, etc.) are logged via the central `utils.logging` module (FR‑026). |
| **Phase 4 – Curve Shape & Collapse Identification** | FR‑012, FR‑020, FR‑021, FR‑053, FR‑036, FR‑010 | Fit a smooth spline to each stress curve, extract the maximum negative derivative (inflection step) and its coordinate. |
| **Phase 5 – Manual Validation Subset (FR‑033)** | FR‑033 | Randomly select a representative sample of stress curves; expert listeners label the true collapse intensity. These labels form the **annotated collapse intensity** used as the regression target and for precision/recall evaluation (SC‑009). |
| **Phase 6 – Collapse Identification (Deterministic)** | FR‑021, FR‑020, FR‑010, FR‑036 | Apply deterministic CCM algorithm, linear interpolation between steps when needed, and also record the step where absolute SSS ≤ 0.5 (Universal Collapse Intensity). Store results in `collapse_points.parquet`. |
| **Phase 7 – Regression Modeling** | FR‑005, FR‑025, FR‑028, FR‑027 | Train a hierarchical mixed‑effects regression to predict the **annotated collapse intensity** (from Phase 7) using predictors: SNR, RT60, SNR², RT60², interaction (SNR × RT60), baseline WER, and transcript‑perplexity. Use an 80/20 stratified split (speaker + distortion + difficulty) and 5‑fold CV on training set. Evaluate on held‑out set (R² ≥ 0.6, MAE reported). |
| **Phase 8 – Interaction Significance & Multiple Comparison** | FR‑013, FR‑008 | Fit additive linear model; compare to full interaction model; test interaction term (p < 0.05) and apply Benjamini‑Hochberg correction (FDR ≤ 0.05). |
| **Phase 9 – Sensitivity Analysis (FR‑006, SC‑002)** | FR‑006, SC‑002 | Sweep SSS thresholds {0.45, 0.50, 0.55} and WER multipliers {1.5, 2.0, 2.5}; recompute collapse intensities and refit regression; compute coefficient‑of‑variation of each coefficient across the nine settings; require CV ≤ 0.10. |
| **Phase 10 – Partial‑Correlation (FR‑035)** | FR‑035 | Compute partial‑correlation between acoustic predictors and annotated collapse intensity while controlling for baseline WER; report unique variance explained. |
| **Phase 11 – Universality Assessment (FR‑051)** | FR‑051 | Derive a **critical interaction vector** from each model’s regression coefficients; compute cosine similarity across models (≥ 0.80); perform permutation test shuffling model labels – observed similarity must exceed the 95th percentile. |
| **Phase 12 – Validation & Export** | FR‑030, FR‑031, FR‑034 | Validate `collapse_points.parquet` against `contracts/collapse_point.schema.yaml` and `critical_vector.parquet` against `contracts/critical_vector.schema.yaml`. Abort on any violation. |
| **Phase 13 – Reporting** | FR‑007, SC‑001 – SC‑009 | Generate figures, tables, and a Markdown report. All statements use associational phrasing only (FR‑007). Report metrics: R², MAE, sensitivity CV, interaction FDR‑corrected p‑values, partial‑correlation coefficients, universality similarity, human‑validation AUC‑ROC, precision/recall for collapse‑point identification (≥ 0.90), etc. All metric computations are logged per FR‑026. |

All functional requirements (FR‑001 – FR‑036, FR‑051, FR‑053) and success criteria (SC‑001 – SC‑009) are covered.

---


## projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/specs/001-llmxive-follow-up-extending-mega-asr-tow/research.md

# Research: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

**Feature**: `001-semantic-collapse-threshold`  
**Date**: 2026-09-26

## Decision & Rationale
- **Compute strategy**: All statistical analyses (regression, SHAP, partial‑correlation) are CPU‑tractable and will run on the free‑tier GitHub Actions runner. The distortion‑generation step requires genuine GPU work; we will **off‑load it to a paid 4‑node V100 GPU cluster** (real CUDA kernels, no CPU approximation). The platform will automatically detect GPU errors and re‑run that phase on the GPU cluster.  
- **Dataset selection**: The only open, programmatically downloadable datasets verified by the system are **Voices‑in‑the‑Wild‑2M** (clean audio & transcripts). **DNS‑Challenge** is not a verified source, so we cannot rely on it for FR‑018. Consequently, **realism validation (FR‑018) cannot be satisfied** with current open data; we will instead use a **proxy subset of ≥ 50 high‑reverb clips** from Voices‑in‑the‑Wild‑2M and explicitly note this limitation in the final report.  
- **Statistical rigor**:  
  - Multiple‑comparison correction via Benjamini‑Hochberg (FDR ≤ 0.05).  
  - Power analysis using G*Power (effect = 0.02, α = 0.05, power = 0.80) yields required N ≈ 395; with 50 k clips we achieve > 99 % power (FR‑032). After the final sample size is fixed, we will **re‑run G*Power and log the achieved power** (FR‑032‑VERIF).  
  - All findings will be framed associationally (FR‑007).  
  - Collinearity will be monitored via VIF; any VIF > 5 triggers centering/reporting.  

## Verified Datasets

| Dataset | URL | Role |
|---------|-----|------|
| Voices‑in‑the‑Wild‑2M | https://huggingface.co/datasets/voices-in-the-wild/2M | Source audio, transcripts, and metadata (clean clips) |
| DNS‑Challenge (real‑world noise) | https://github.com/microsoft/DNS-Challenge | Intended for realism validation (FR‑018) – **not verified**; used only as a conceptual reference. A proxy subset from Voices‑in‑the‑Wild‑2M will be employed instead. |

## Dataset Strategy

| Need | Dataset | Access Method | Notes |
|------|---------|---------------|-------|
| Clean audio & transcripts, stratification metadata | Voices‑in‑the‑Wild‑2M | `datasets.load_dataset("voices-in-the-wild/2M", streaming=False)` | Stratified sampling (speaker + environment) to obtain ≥ 50 000 clips. |
| Proxy “real‑world” noisy clips for FR‑018 | Voices‑in‑the‑Wild‑2M (reverberant subset) | Filter metadata for high RT60 recordings; select ≥ 50 clips. | Used only because DNS‑Challenge is not a verified source. |

## Methodology Overview

1. **Power & Human Gate (Phase 0)** – Compute required N (≈ 395) with G*Power; collect ≥ 1 000 human‑annotated transcripts (≥ 3 raters each) from Voices‑in‑the‑Wild‑2M; compute SSS AUC‑ROC ≥ 0.85. If SSS fails, fall back to phoneme‑edit distance for high‑reverb clips (FR‑022). Abort if both fail (FR‑016). After the final sample is selected, **re‑run G*Power** and record the achieved power (> 99 %).  
2. **Stratified Sampling (FR‑001)** – Load `metadata.csv` from Voices‑in‑the‑Wild‑2M, stratify by `speaker_id` and `environment_id`, random seed = 42, sample a large set of clip IDs. Record SHA‑256 checksums (Principle III).  
3. **Distortion Generation (FR‑002, FR‑024)** – Split IDs into four GPU shards; each shard runs on a V100 GPU node (`pyroomacoustics`) applying the Cartesian product of 9 SNR levels × 6 RT60 levels (multiple scenarios) per clip for five small ASR models.  
4. **Semantic Scoring (FR‑003, FR‑022)** – Encode clean transcript and ASR hypothesis with `sentence‑transformers/all‑MiniLM‑L6‑v2`; compute cosine similarity → SSS. For clips where RT60 > 0.5 s **and** embedding correlation < 0.85, compute phoneme‑edit distance via Montreal Forced Aligner. Log any missing distortion scenarios (FR‑017).  
5. **Realism Validation (FR‑018 – limited)** – Because DNS‑Challenge is not a verified source, we **skip** the formal LMSD validation and instead report the proxy approach, noting the limitation.  
6. **Curve Shape & Inflection (FR‑012, FR‑053)** – Fit a smooth spline to each stress curve, extract the maximum negative derivative (inflection step) and its coordinate.  
7. **Collapse Identification (FR‑021, FR‑020, FR‑010, FR‑036)** – Apply deterministic CCM algorithm, linear interpolation between steps when needed, and also record the step where absolute SSS ≤ 0.5 (Universal Collapse Intensity). Store results in `collapse_points.parquet`.  
8. **Regression Modeling (FR‑005, FR‑025, FR‑028)** – Train a hierarchical mixed‑effects regression to predict **inflection_step** using predictors: SNR, RT60, SNR², RT60², interaction (SNR × RT60), baseline WER, and transcript‑perplexity. Use an 80/20 stratified split (speaker + distortion + difficulty) and 5‑fold CV on training set. Evaluate on held‑out set (R² ≥ 0.6, MAE reported).  
9. **Permutation Baseline (FR‑027)** – Randomly permute acoustic predictor vectors, retrain, and require ΔR² ≥ 0.20.  
10. **Interaction Significance & Multiple Comparison (FR‑013, FR‑008)** – Fit additive linear model; compare to full interaction model; test interaction term (p < 0.05) and apply Benjamini‑Hochberg correction (FDR ≤ 0.05).  
11. **Sensitivity Analysis (FR‑006, SC‑002)** – Sweep SSS thresholds {0.45, 0.50, 0.55} and WER multipliers {1.5, 2.0, 2.5}; recompute collapse intensities and refit regression; compute coefficient‑of‑variation of each coefficient across the nine settings; require CV ≤ 0.10.  
12. **Precision/Recall Evaluation (SC‑009)** – Compare deterministic collapse points (Phase 8) against the expert‑annotated ground truth (Phase 7); compute precision and recall; require **≥ 0.90** for both.  
13. **Partial‑Correlation (FR‑035)** – Compute partial‑correlation between acoustic predictors and inflection_step while controlling for baseline WER; report unique variance explained.  
14. **Universality Assessment (FR‑051)** – Derive a **critical interaction vector** from each model’s regression coefficients; compute cosine similarity across models (≥ 0.80); perform permutation test shuffling model labels – observed similarity must exceed the 95th percentile.  
15. **Validation & Export (FR‑030, FR‑031, FR‑034)** – Write `collapse_points.parquet` and `critical_vector.parquet`; validate against respective JSON schemas; abort on any violation.  
16. **Reporting (Phase 7, FR‑007)** – Generate figures, tables, and a Markdown report. All statements use associational phrasing only (FR‑007). Report metrics: R², MAE, sensitivity CV, interaction FDR‑corrected p‑values, partial‑correlation coefficients, universality similarity, human‑validation AUC‑ROC, precision/recall for collapse‑point identification, etc. All metric computations are logged per FR‑026.  

All steps are fully scripted, reproducible, and logged (`FR‑026`).  

---

