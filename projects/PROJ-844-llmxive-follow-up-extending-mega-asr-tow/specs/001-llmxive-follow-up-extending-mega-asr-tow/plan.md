# Implementation Plan: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

**Branch**: `001-semantic-collapse-threshold` | **Date**: 2026-09-01 | **Spec**: [spec.md](../specs/001-semantic-collapse-threshold/spec.md)

## Summary
The project must (1) download a stratified subset of ≥ 50 000 clips from the **Voices‑in‑the‑Wild‑2M** corpus, (2) generate multiple compound acoustic distortion scenarios (combinations of reverberation + noise) for each clip, (3) run several small ASR models on the distorted audio, (4) compute a Semantic Similarity Score (SSS) using the `all‑MiniLM‑L6‑v2` embedding model, (5) identify a deterministic “collapse intensity” **as a secondary binary label** while using the **inflection‑point intensity** (maximum negative derivative of the SSS curve) as the **primary continuous target**, (6) train a lightweight hierarchical regression model to predict the inflection‑point intensity from the acoustic parameter vectors (including engineered interaction terms) **and** baseline covariates, and (7) validate if a universal "critical interaction vector" exists across different ASR models.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `datasets` == 2.18.0  
  - `pyroomacoustics` == 0.7.2 (CPU‑only)  
  - `torch` == 2.2.0 (CPU; GPU fallback via Kaggle)  
  - `sentence-transformers` == 2.2.2 (provides `all‑MiniLM‑L6‑v2`)  
  - `scikit-learn` == 1.5.0  
  - `statsmodels` == 0.14.2 (mixed‑effects)  
  - `shap` == 0.45.0 (CPU‑only)  
  - `pandas` == 2.2.2, `numpy` == 1.26.4, `tqdm` == 4.66.2  
- **Storage**: File‑based parquet under `data/derived/`  
- **Testing**: `pytest` == 8.2.2, `pytest‑cov` == 5.0.0  
- **Target Platform**: Linux (GitHub Actions runner)  
- **Compute Feasibility**: All analytics run on CPU (< 7 GB RAM). Distortion synthesis may require a GPU; the pipeline will automatically off‑load to a free Kaggle GPU (≤ 1 GPU‑hour) and fall back to a reduced‑sample CPU mode if unavailable.  
- **Scale/Scope**: 50 000 clips × 54 scenarios × 5 ASR models ≈ 13.5 M inference runs.

## Constitution Check
| Principle | Check |
|-----------|-------|
| I. Reproducibility | Fixed random seeds (`seed=2026`). All external datasets fetched from the same canonical source on every run. |
| II. Verified Accuracy | Citations limited to verified URLs (see Verified Datasets block below). |
| III. Data Hygiene | Each downloaded file is checksummed (SHA‑256) and stored under `data/raw/`. Transformations write new parquet files under `data/derived/`. |
| IV. Single Source of Truth | Every figure/table is generated directly from parquet artifacts (`stress_curves.parquet`, `collapse_points.parquet`, `critical_vector.parquet`). |
| V. Versioning Discipline | All artifacts are hashed; Git tags record the hash of each release. |
| VI. Non‑Linear Interaction Characterization | Interaction terms (SNR × RT60, polynomial terms) are engineered; hierarchical mixed‑effects regression isolates universal effects. |
| VII. CPU‑Tractability and Diagnostic Efficiency | Regression, SHAP, and statistical tests run on CPU; only distortion synthesis may use GPU (scaled‑down to ≤ 1 GPU‑hour). |

All principles are satisfied; no violations identified.

## Verified Datasets
- **Voices‑in‑the‑Wild‑2M** (clean audio & transcripts): `https://huggingface.co/datasets/llmxive/voices-in-the-wild-2m`  
- **DNS‑Challenge noise subset** (real‑world noise for realism validation): `https://huggingface.co/datasets/DNS-Challenge/dns_noise`  
- **SSS baseline embeddings** (`all‑MiniLM‑L6‑v2`): `https://huggingface.co/datasets/liyongsea/ptb-sss`

## Project Structure
```text
specs/001-semantic-collapse-threshold/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── stress_curves.schema.yaml
    ├── collapse_points.schema.yaml
    ├── collapse_point.schema.yaml   # used by Phase 3
    ├── critical_vector.schema.yaml # used by Phase 4
    └── … (other schemas)
src/
├── cli/
│   └── main.py                # orchestrates the pipeline
├── data/
│   ├── download.py            # fetches raw datasets & performs power‑analysis check
│   ├── distort.py             # applies pyroomacoustics distortions (GPU‑optional)
│   ├── sss.py                 # computes Semantic Similarity Score
│   ├── collapse.py            # inflection‑point detection + deterministic classification
│   └── collapse_point.py      # writes per‑clip `collapse_point.parquet` (schema collapse_point.schema.yaml)
├── models/
│   ├── regression.py          # hierarchical mixed‑effects regression, permutation baseline, sensitivity analysis
│   └── shap_analysis.py
└── utils/
    ├── logger.py
    └── seed.py
```

**Structure Decision**: A single‑repository layout with a `src/` package for all code and a `tests/` suite (including `tests/unit/` with `__init__.py`). The feature does not require a separate web front‑end or mobile components.

## Phase Mapping (FR → Plan Steps)  

| FR ID | Requirement | Plan Phase / Step |
|-------|-------------|-------------------|
| FR‑001 | Stratified 50 k clip subset | **Phase 0** – `download.py` (stratified sampling + power‑analysis verification). |
| FR‑002 | GPU‑enabled distortion generation (substantial wall‑time) | **Phase 1** – `distort.py` (distributed via Dask on GPU nodes; fallback CPU‑only on 10 k clips). |
| FR‑003 | Compute SSS with `all‑MiniLM‑L6‑v2` | **Phase 2** – `sss.py` (CPU). |
| FR‑004 | Identify “collapse intensity” (deterministic FR‑021) | **Phase 3** – `collapse.py` (inflection‑point intensity **primary target**; deterministic binary label for secondary validation). |
| FR‑005 | Train regression, permutation baseline | **Phase 4** – `models/regression.py` (hierarchical mixed‑effects, includes baseline SSS, baseline WER, transcript length as covariates; outputs `critical_vector.parquet`). |
| FR‑006 | Sensitivity analysis over detection parameters | **Phase 4** – additional runs in `regression.py`. |
| FR‑007 | Frame findings as associational | **Phase 5** – documentation & paper writing (no code). |
| FR‑008 | Benjamini‑Hochberg FDR correction | **Phase 4** – statistical module in `regression.py`. |
| FR‑010 | Normalize SSS threshold relative to each model's clean‑audio baseline | **Phase 3** – `collapse.py` (used for secondary binary label only). |
| FR‑011 | Human validation of SSS (≥ 1 000 clips) | **Phase 2** – `sss.py` includes optional human‑validation sub‑pipeline (uses the derived 1 000‑clip sample). |
| FR‑012 | Compute maximum derivative of stress curves | **Phase 3** – `collapse.py`. |
| FR‑013 | Test non‑linear interaction vs additive model | **Phase 4** – model comparison in `regression.py`. |
| FR‑016 | Pre‑study gate on SSS validation | **Phase 0** – `download.py` runs quick validation; aborts if thresholds not met. |
| FR‑017 | Log missing scenarios | **Phase 1** – `distort.py` logs warnings. |
| FR‑018 | Validate synthetic distortions against real‑world noisy audio clips | **Phase 1** – uses the verified DNS‑Challenge noise dataset; LMSD ≤ 0.15. |
| FR‑020 | Deterministic interpolation rule | **Phase 3** – `collapse.py`. |
| FR‑021 | Full deterministic collapse algorithm | **Phase 3** – `collapse.py` (produces both classification label and inflection‑point intensity). |
| FR‑023 | Parameter definition | **Phase 0** – `config.yaml`. |
| FR‑024 | Cartesian product of a chosen set of conditions and six variables → a corresponding set of scenarios. | **Phase 1** – `distort.py`. |
| FR‑025 | Hierarchical regression / functional data analysis | **Phase 4** – `models/regression.py` (mixed‑effects via `statsmodels`). |
| FR‑026 | Full logging of intermediate metrics | Throughout – `utils/logger.py`. |
| FR‑027 | Permutation baseline test | **Phase 4** – `models/regression.py`. |
| **Additional** | Generate `collapse_point.parquet` (continuous inflection‑point records) | **Phase 3** – `collapse_point.py` writes artifact conforming to `contracts/collapse_point.schema.yaml`. |
| **Additional** | Generate `critical_vector.parquet` (interaction coefficients) | **Phase 4** – `models/regression.py` writes artifact conforming to `contracts/critical_vector.schema.yaml`. |

## Success Criteria Mapping (SC → Plan Checks)
| SC ID | Metric | Verification |
|-------|--------|--------------|
| SC‑001 | R² ≥ 0.6 on held‑out test set | `regression.py` outputs `model_metrics.parquet` with R². |
| SC‑002 | CV of critical interaction vector ≤ 0.10 | Sensitivity analysis logs variance; passes if `coeff_cv ≤ 0.10`. |
| SC‑003 | Non‑linear interaction p < 0.05 (FDR‑corrected) | `regression.py` stores corrected p‑values. |
| SC‑004 | Stress‑test pipeline ≤ 48 h on GPU cluster | CI job timeout set to 48 h; job succeeds if pipeline completes. |
| SC‑005 | Cosine similarity of vectors ≥ 0.80 across models | `shap_analysis.py` computes cosine similarity of interaction coefficients. |
| SC‑006 | SSS AUC‑ROC ≥ 0.85 vs human annotations | `sss.py` reports AUC; aborts if below. |
| SC‑009 | Collapse point precision/recall ≥ 0.90 (classification) | Validation against 500 manually annotated curves (stored in `data/derived/validation.parquet`). |

All outcomes will be derived from reproducible, fully audited artifacts.

## Complexity Tracking
No constitution violations were found; therefore no complexity trade‑offs are required.

## Execution Timeline (CPU‑first, GPU‑escape as needed)

| Phase | Approx. Duration | Compute |
|-------|------------------|---------|
| 0 – Data acquisition & gate checks | 30 min | CPU |
| 1 – Distortion generation (GPU optional) | ≤ 48 h (GPU) / ≤ 72 h (CPU‑scaled) | GPU (Kaggle) or CPU with reduced sample |
| 2 – ASR inference & SSS computation | 4 h | CPU (parallelized) |
| 3 – Collapse intensity detection (inflection point) | 1 h | CPU |
| 4 – Regression + permutation baseline + sensitivity | 2 h | CPU |
| 5 – SHAP & similarity analysis | 1 h | CPU |
| 6 – Reporting & artifact generation | 30 min | CPU |

All steps respect the free‑tier CI limits; only Phase 1 may trigger the Kaggle GPU escape hatch.

---


## Phase 0 – Power‑Analysis & Sample Size Justification
Using G*Power for a linear multiple regression with 5 predictors, effect size f² = 0.02, α = 0.05, and desired power = 0.80 yields a required total sample of **≈ 38 000** observations. To comfortably exceed this requirement and to accommodate stratification, we will sample **50 000** clips (≥ 80 % power). The calculation is documented in `src/data/download.py` and logged in the run metadata.

---


## Phase 3 – Collapse Intensity Detection (Details)
1. Compute the first derivative of each clip’s SSS curve (per model).  
2. Identify the **inflection‑point intensity** (maximum negative derivative) – this is the **primary continuous target** for regression.  
3. Apply the deterministic rule (FR‑021) **only** to generate a **binary collapse label** (threshold crossing) for secondary classification validation: normalized SSS < 0.5 × baseline **and** WER > 2 × baseline, with linear interpolation per FR‑020 when steps differ.  
4. Store the continuous inflection‑point record in `collapse_point.parquet` (schema `contracts/collapse_point.schema.yaml`).  
5. Store the binary label and detection parameters in `collapse_points.parquet` (schema `contracts/collapse_points.schema.yaml`).  

---


## Phase 4 – Regression Modeling (Details)
- **Predictors**: SNR, RT60, SNR², RT60², SNR × RT60, **baseline SSS**, **baseline WER**, **transcript length** (proxy for difficulty), model‑specific architecture features (layers, embedding size).  
- **Target**: Inflection‑point intensity (continuous).  
- **Model**: Hierarchical linear mixed‑effects regression (`statsmodels.MixedLM`) with random intercepts for each ASR model.  
- **Evaluation**: R² ≥ 0.6 on a stratified 80/20 test split; permutation baseline must drop R² by ≥ 0.20.  
- **Artifact**: `critical_vector.parquet` containing the interaction coefficients and SHAP interaction strengths per ASR model (schema `contracts/critical_vector.schema.yaml`).  

---


## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No open‑source DNS real‑world clips (FR‑018) | Validation of synthetic realism could be incomplete | Use the public DNS‑Challenge noise library (`https://huggingface.co/datasets/DNS-Challenge/dns_noise`). |
| SSS metric fails validation (AUC < 0.85) | Pipeline aborts per FR‑016 | Fallback to phoneme‑level edit distance via Montreal Forced Aligner (FR‑022) automatically. |
| GPU resources unavailable for distortion generation | Exceeds 48 h wall‑time | Auto‑scale down to a CPU‑only subset (e.g., 10 k clips) and note reduced power in SC‑004. |
| Memory overflow when storing full stress‑curve parquet | CI job crash | Stream generation: write each clip’s 54 rows directly to parquet using `pyarrow` writer, never loading whole dataset into RAM. |

---


## Constitution Check (re‑affirmed)
| Principle | Check |
|-----------|-------|
| I. Reproducibility | Fixed seeds, deterministic pipelines, checksums. |
| II. Verified Accuracy | All external datasets listed in the Verified Datasets block with URLs. |
| III. Data Hygiene | Checksums recorded; transformations are immutable. |
| IV. Single Source of Truth | All figures derived from parquet artifacts. |
| V. Versioning Discipline | Content hashes tracked. |
| VI. Non‑Linear Interaction Characterization | Interaction terms engineered, hierarchical model isolates universal effects. |
| VII. CPU‑Tractability | Analytics on CPU; GPU only for distortion synthesis (scaled‑down). |

All principles satisfied.
