# Implementation Plan: Investigating the Relationship Between Pupil Dilation and Cognitive Load During Visual Search

**Branch**: `001-pupil-dilation-cognitive-load` | **Date**: 2026-06-25 | **Spec**: `specs/001-pupil-dilation-cognitive-load/spec.md`
**Input**: Feature specification from `/specs/001-pupil-dilation-cognitive-load/spec.md`

## Summary

This project implements a computational pipeline to quantify the relationship between task‑evoked pupil dilation and cognitive load during visual search tasks. The technical approach involves ingesting raw eye‑tracking data from OpenNeuro ds004248, preprocessing signals (blink interpolation, low‑pass filtering), extracting trial‑wise load proxies (search time, target salience from metadata, fixation count), and performing statistical analysis (Pearson correlations with Bonferroni correction, Linear Mixed‑Effects modeling). Finally, a CPU‑tractable sliding‑window logistic regression classifier will simulate real‑time load detection. The entire pipeline is designed to run on free‑tier GitHub Actions runners (CPU‑only, ≤6GB RAM, ≤6h).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `mne` (for signal processing), `pyyaml`, `tqdm`. No GPU libraries.  
**Storage**: Local file system (`data/raw/`, `data/processed/`, `outputs/`).  
**Testing**: `pytest` (unit tests for data validation, integration tests for pipeline phases).  
**Target Platform**: Linux (GitHub Actions free‑tier runner).  
**Project Type**: Data analysis pipeline / CLI tool.  
**Performance Goals**: Complete full pipeline in ≤5 hours; RAM usage ≤6 GB.  
**Constraints**: No GPU/CUDA; no deep learning; strict adherence to dataset variable availability; Bonferroni correction for multiple comparisons; handling of missing data as per spec.  
**Scale/Scope**: Single dataset (OpenNeuro ds – Visual Search with Salient Distractors) with a moderate number of subjects, ~‑ trials total.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re‑check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | All random seeds pinned in `code/config.yaml`; `requirements.txt` pins versions; data fetched from canonical OpenNeuro source via `datalad` or direct download script. |
| **II. Verified Accuracy** | **Non‑Compliant (pending)** | The dataset URL for ds004248 is identified. Compliance will be re‑evaluated ONLY after successful download, checksum verification, and recording of the hash in `data/raw/<filename>_meta.json`. |
| **III. Data Hygiene** | **Compliant** | Raw data stored unaltered in `data/raw/`; each raw file has an accompanying provenance JSON (`*_meta.json`) with source URL, SHA‑256 checksum, and acquisition date. Processed derivatives are written to new files in `data/processed/` with derivation logs. |
| **IV. Single Source of Truth** | **Compliant** | All statistics in the final report are generated directly from CSV/JSON outputs under `outputs/`; no hand‑typed numbers. |
| **V. Versioning Discipline** | **Compliant** | The Advancement-Evaluator Agent updates the project's `state` file (`state/projects/PROJ-174-...yaml`) with content hashes for **every** artifact change. This mechanism ensures the single source of truth for artifact versions as mandated by Principle V. |
| **VI. Eye‑Tracking Data Integrity** | **Compliant** | Raw EDF/CSV files are stored **unaltered** in `data/raw/`. **Provenance metadata** links each derivative file back to its original source file, strictly satisfying the integrity requirement of Principle VI. |
| **VII. Real‑Time Load Classification Validation** | **Compliant** | The evaluation script logs the **exact integer value** of `random_seed` (e.g., 42) and `sliding_window_ms = 200` (exact integer) in the output JSON. Classification thresholds are recorded, and the script also outputs the continuous correlation between predicted load probability and search time as an auxiliary validation. |

## Project Structure

### Documentation (this feature)

```text
specs/001-pupil-dilation-cognitive-load/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-174-investigating-the-relationship-between-p/code/
├── config.yaml          # Configuration: seeds, thresholds, paths
├── requirements.txt     # Pinned dependencies
├── data_loader.py       # Ingest raw data (OpenNeuro ds004248)
├── preprocess.py        # Blink interpolation, filtering, trial alignment
├── features.py          # Compute load proxies (search time, salience, fixations)
├── analysis.py          # Correlations, LME models
├── classifier.py        # Sliding‑window logistic regression
├── evaluate.py          # Metrics, sensitivity analysis, auxiliary correlation
├── main.py              # Pipeline orchestrator
└── tests/
    ├── test_preprocess.py
    ├── test_analysis.py
    └── test_classifier.py
```

**Structure Decision**: Single‑project layout keeps data, code, and results tightly coupled, facilitating reproducibility on the limited CI environment.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Linear Mixed‑Effects (LME) Model** | Required by the relevant functional requirement to account for subject‑level random intercepts and handle unbalanced trial counts. | Simple linear regression would ignore subject variability, inflating Type I error. |
| **Sliding‑Window Classifier** | Required by FR‑ to demonstrate real‑time capability (ms updates). | Batch classification would not satisfy the real‑time claim. |
| **Bonferroni Correction** | Required by FR to control family-wise error across 9 correlation tests. | Uncorrected p‑values would increase false‑positive risk. |
| **Collinearity Mitigation** | Required by methodological concerns (FR‑005, SC‑002). | Ignoring VIF could produce unstable fixed‑effect estimates. |

## Methodological Enhancements (addressing reviewer concerns)

* **Collinearity handling in LME** – Compute VIF; if any predictor > 5, the default action is to fit a **Reduced Model** (dropping the predictor with the highest VIF) to preserve the interpretability of unique contributions. PCA is moved to an exploratory appendix only. |
* **Salience independence** – `stimulus_salience` is read **only** from stimulus metadata files (e.g., `.npy`, `.json`). If unavailable, salience‑related analyses are **skipped entirely** and a warning is logged. We do NOT compute salience from fixation data. |
* **Classifier ground‑truth** – If an independent load measure (e.g., secondary‑task performance) exists, it is used. If not, the classifier is re-scoped as a **Feasibility Demonstration** of real-time signal processing, and results are reported as **Internal Consistency** only. The claim of "predictive validity" is removed in this scenario. |
* **Multiple‑comparison correction** – Bonferroni applied to the correlation tests; adjusted p‑values are stored in `outputs/correlations.csv`. |
* **Sensitivity analysis** – Threshold sweep {0.01, 0.05, 0.10} with full metric tables recorded. |

## Compute Feasibility

Designed for GitHub Actions free tier (2 CPU, ≈7 GB RAM, 14 GB disk, ≤6 h).  
* **Data Size** – ds004248 raw size < 1 GB; processed CSVs < 500 MB.  
* **Model Complexity** – Logistic regression and LME are CPU‑tractable; no GPU or large‑scale training.  
* **Runtime Estimate** – Preprocessing & feature extraction: approximately one hour; LME fitting [deferred]; classifier training & evaluation: approximately one hour; total well under the time budget.

## Limitations & Risks

1. **Dataset Availability** – If ds004248 cannot be downloaded or fails verification, the pipeline will abort with a clear error. A synthetic placeholder dataset matching the schema is provided for development but not for final inference. |
2. **Ground‑Truth Independence** – When no independent load measure exists, classification results are limited to **Internal Consistency**; this limitation is explicitly documented. |
3. **Statistical Power** – Small subject counts (< 20 trials per subject) trigger a warning and may lead to aggregation or model simplification, as per Edge Cases. |
4. **Collinearity** – If VIF > 5, the Reduced Model is used, and the "unique contribution" claim is limited to the predictors retained in that model. |