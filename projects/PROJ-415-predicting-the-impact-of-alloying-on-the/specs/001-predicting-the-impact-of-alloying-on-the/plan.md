# Implementation Plan: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

**Branch**: `001-predict-alloy-diffusion` | **Date**: 2023-10-27 | **Spec**: `specs/001-predict-alloy-diffusion/spec.md`  
**Input**: Feature specification from `/specs/001-predict-alloy-diffusion/spec.md`

## Summary
The project will ingest experimental diffusion data from the NIST Standard Reference Database 150 (SRD 150), perform a mandatory **Data Availability Check**, filter the data to FCC self-diffusion rows exactly as FR-001 specifies, engineer atomic descriptors (size mismatch, electronegativity difference, valence electron count), train Random Forest, Gradient Boosting, and Linear Regression models, and conduct statistical validation including bootstrap significance testing and a classification-threshold sensitivity analysis. All steps run on CPU-only hardware within the GitHub Actions free-tier limits.

## Spec Gap (flagged for kickback — do NOT implement against current spec)
FR-001 authorizes filtering **only** rows where `diffusion_mode == "self"`. However, FR-003/FR-004/FR-005 (model training on activation-energy *shifts* driven by alloying) require data with varying solutes — i.e., solute/impurity diffusion rows — to provide variance in the descriptors. The current spec does not authorize extracting those rows. **Required spec amendment (kickback)**: amend FR-001 and US-1 Scenario 1 to authorize extraction of both (a) FCC self-diffusion rows (baseline set, per FR-006) and (b) FCC solute/impurity diffusion rows (training set). Until the spec is amended, this plan implements FR-001 exactly as written (self-only filtering); the solute-diffusion extraction tasks below are **deferred** and marked `[SPEC-AMENDMENT-PENDING]`. The pipeline must not silently override the authoritative spec.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `scikit-learn`, `numpy`, `matplotlib`, `seaborn`, `periodictable==0.20.1`, `statsmodels`, `joblib`, `pytest`  
- **Storage**: CSV/JSON files under `data/` and `validation/`  
- **Testing**: `pytest` (unit + integration)  
- **Target Platform**: Linux (`ubuntu-latest` GitHub Actions runner)  
- **Project Type**: Data-science / Computational Materials Science  
- **Performance Goals**: Full pipeline ≤ 6 h, peak RAM ≤ 7 GB  
- **Constraints**: No synthetic data; CPU-only; dataset size < 10 MB per the project **Constitution, Principle VI (Computational Resource Compliance)**, which mandates "dataset size MUST remain under 10 MB to ensure reproducibility within CI constraints."  

## Constitution Check
| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Reproducibility** | ✅ PASS | Fixed seeds, `requirements.txt`, immutable raw data. |
| **II. Verified Accuracy** | ✅ PASS | All citations will be validated by the Reference-Validator. |
| **III. Data Hygiene** | ✅ PASS | Checksums, provenance JSON, no in-place mutation. |
| **IV. Single Source of Truth** | ✅ PASS | `data/curated/filtered.csv` is the SSoT for all downstream analyses and MUST validate against `contracts/dataset.schema.yaml`. |
| **V. Versioning Discipline** | ✅ PASS | Content hashes recorded; timestamps managed automatically. |
| **VI. Computational Resource Compliance** | ✅ PASS | CPU-only models, dataset size < 10 MB (per Principle VI), runtime budget respected. |
| **VII. Descriptor Consistency** | ✅ PASS | `periodictable==0.20.1` pins atomic constants; Pauling electronegativity used consistently. |

## Project Structure
```text
specs/001-predict-alloy-diffusion/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── atomic_descriptor.schema.yaml
    ├── dataset.schema.yaml
    ├── diffusion_record.schema.yaml
    ├── model_artifact.schema.yaml
    ├── model_output.schema.yaml
    └── validation_report.schema.yaml

projects/PROJ-415-predicting-the-impact-of-alloying-on-the/
├── data/
│   ├── raw/                # immutable download (if available)
│   └── curated/
│       ├── baselines.csv
│       ├── filtered.csv
│       └── data_provenance.json
├── code/
│   ├── data/
│   │   └── streaming_loader.py   # FR-001 Data Availability Check
│   ├── ingestion/
│   │   └── ingest.py              # loads raw CSV, applies FR-001 filters
│   ├── processing/
│   │   ├── feature_engineering.py
│   │   └── baseline.py            # FR-008 baseline_shift calculator
│   ├── models/
│   │   ├── train_rf.py
│   │   ├── train_gb.py
│   │   └── train_linear.py
│   └── validation/
│       └── sensitivity_analysis.py   # FR-005, FR-009
├── models/                         # Pickled model artifacts
├── validation/                     # JSON reports & plots
├── tests/
│   ├── unit/
│   └── integration/
└── requirements.txt
```

## Complexity Tracking
Complexity is managed by:
1. **CPU-first algorithms** – no GPU required.  
2. **Streaming loader** – processes data in chunks if file size exceeds RAM.  
3. **Early data validation** – halts on missing baseline rows.  

## FR/SC Coverage Map
| FR/SC ID | Plan Element | Description |
|----------|--------------|-------------|
| **FR-001** | `code/data/streaming_loader.py` & `code/ingestion/ingest.py` | Loads raw NIST SRD 150 data, filters to `crystal_structure == "FCC"` AND `diffusion_mode == "self"` exactly as the spec states; Data Availability Check halts with `"ERROR: No verified real dataset found. Synthetic data is not permitted for this research goal."` if < 1 valid row. Solute-row extraction is `[SPEC-AMENDMENT-PENDING]` (see Spec Gap). |
| **FR-002** | `code/processing/feature_engineering.py` | Computes `size_mismatch` using `periodictable==0.20.1`. |
| **FR-003** | `code/models/train_rf.py`, `code/models/train_gb.py` | Grid-search `max_depth` [3-10] & `n_estimators` [50-200]; tie-break on lower complexity. `[SPEC-AMENDMENT-PENDING]` for training-row source. |
| **FR-004** | `code/models/train_*.py` | Nested CV (default) or 80/20 hold-out if < 50 rows; stratified by host when possible, else random split with warning. |
| **FR-005** | `code/validation/sensitivity_analysis.py` | Threshold sweep {0.45 – 0.55 eV}, computes Stability Index, writes `validation/stability_index_report.json`. |
| **FR-006** | `code/processing/baseline.py` | Retrieves pure-host activation energies from self-diffusion rows; halts with `"ERROR: Baseline activation energy for host [X] not found in NIST SRD 150. Pipeline halted."` if missing. |
| **FR-007** | `code/ingestion/ingest.py` | Generates `data/curated/data_provenance.json` (source_url, hash, timestamp, filter_criteria). |
| **FR-008** | `code/processing/baseline.py` | Calculates `baseline_shift` and appends to `filtered.csv`. |
| **FR-009** | `code/validation/sensitivity_analysis.py` | Emits `validation/stability_index_report.json`. |
| **SC-001** | `code/models/train_*.py` | Reports R² on held-out test set against the spec-defined mean-predictor baseline (R² > 0.0). *Flagged for spec kickback*: a stricter criterion (e.g., R² ≥ 0.2 or a physically-motivated baseline) would be more discriminating; the plan does not add an un-spec'd threshold. RMSE vs. mean-predictor is additionally reported for context. |
| **SC-002** | `code/models/train_linear.py` | Checks bootstrap p-value < 0.05 and 95 % bootstrap CI excludes zero; `models/linear_coef.json` conforms to `contracts/model_output.schema.yaml`. |
| **SC-003** | `code/validation/sensitivity_analysis.py` | Verifies Stability Index ≤ 0.05 1/eV. |
| **SC-004** | CI workflow (generated by repository) | Confirms runtime ≤ 6 h and peak RAM ≤ 7 GB. |