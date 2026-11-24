# Implementation Plan: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

**Branch**: `001-predict-poissons-ratio` | **Date**: 2026-10-24 | **Spec**: `specs/001-predicting-the-effect-of-alloying-on-the/spec.md`  
**Input**: Feature specification from `/specs/001-predicting-the-effect-of-alloying-on-the/spec.md`

## Summary
The pipeline will (1) download compositional and elastic‑property data for aluminum alloys, (2) filter and clean the data according to FR‑001 – FR‑010, (3) compute variance‑inflation factors on raw fractions, (4) apply the Isometric Log‑Ratio (ILR) transformation, (5) **first split the data into an 80/20 train/test set**, (6) **run cross‑validation only on the training portion**, (7) evaluate on the held‑out test set, (8) extract feature importance using permutation importance on the original compositional features (primary) and back‑transform Gini importance from ILR coordinates for exploratory insight, (9) generate associational narrative (FR‑008) and all required JSON artifacts, and (10) validate those artifacts against schemas. Every functional requirement (FR‑001 – FR‑010) and success criterion (SC‑001 – SC‑006) is mapped to a concrete phase/step below.

## Technical Context
- **Language / Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `matminer`, `statsmodels`, `pyyaml`, `joblib`, `chemparse`  
- **Storage**: File‑system under `data/` (raw, processed) and `results/` (JSON, markdown)  
- **Testing**: `pytest` + schema validation (`jsonschema`)  
- **Target Platform**: GitHub Actions free tier (2 CPU cores, ≈7 GB RAM, ≤6 h) – **CPU‑first**; no GPU required.  
- **Constraints**:  
  - Elastic constants normalized to GPa (VI).  
  - Composition sums to 1.0 ± 1e‑6.  
  - VIF > 5 flagged (VII).  
  - MAE > 0.05 flagged per constitution (I).  

## Constitution Check
| Principle | Check |
|-----------|-------|
| **I. Reproducibility** | `requirements.txt` pinned; random seeds (`np.random.seed(42)`, `random.seed(42)`) set in `code/main.py`. |
| **II. Verified Accuracy** | No external citation beyond the verified‑datasets block; limitation on NIST source documented (AMP‑001). |
| **III. Data Hygiene** | Raw files checksummed (SHA‑256) and recorded in `data/checksums.json`; every transformation writes a new file. |
| **IV. Single Source of Truth** | All figures/tables generated from JSON artifacts in `results/`. |
| **V. Versioning Discipline** | Artifact hashes stored in `state/projects/PROJ-420-...yaml`. |
| **VI. Unit Consistency** | Explicit conversion step normalizes Young’s modulus to GPa; mismatches logged. |
| **VII. Compositional Attribution** | ILR transformation and back‑transformation of feature importances implemented; rankings output in `results/feature_importance.json`. |
| **Additional Rule** | Any methodological discrepancy > 0.05 (e.g., MAE) is flagged per constitution. |

## Spec Amendment (AMP‑001)
**Date**: 2026‑10‑24  
**Affected Requirement**: **FR‑001** (download from Materials Project *and* NIST).  
**Change**: The pipeline will attempt to download from the Materials Project **only**; if the download fails **or** the Materials Project is not listed among the verified datasets, the pipeline aborts with a clear error and logs the limitation. The NIST source is omitted because no verified URL is provided in the “Verified datasets” block.  
**Justification**: The constitution mandates no fabricated data sources. Proceeding without a verified source would violate reproducibility and verified‑accuracy principles.  
**Status**: Ratified.

## Data Source Limitation (Addressing FR‑009)
The Materials Project provides Poisson's ratio derived from DFT elastic tensors rather than independent experimental measurements. No open, programmatically accessible dataset with independently measured Poisson's ratio (e.g., ultrasonic) is available in the verified datasets block. Consequently, **FR‑009 cannot be fully satisfied**. The pipeline will:
1. Filter for records where the metadata field `poisson_source` is one of `ultrasonic`, `direct_measurement`, or `laser_ultrasonics`.  
2. If **zero** records remain after this filter, the pipeline aborts with a clear error message and records the limitation in the provenance log and final report.  
This limitation is explicitly documented in the final report and flagged for scope revision.

## Project Structure
```text
specs/001-predicting-the-effect-of-alloying-on-the/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── dataset.schema.yaml
└── tasks.md   # generated later

projects/PROJ-420-predicting-the-effect-of-alloying-on-the/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── download.py      # fetches raw data
│   │   ├── clean.py         # filtering, unit conversion, exclusion logging
│   │   └── transform.py     # ILR, VIF, back‑transformation utilities
│   ├── analysis/
│   │   ├── train.py         # Random Forest CV & test split
│   │   └── interpret.py     # importance extraction, ranking
│   ├── utils/
│   │   ├── logger.py        # RotatingFileHandler → data/logs/app.log
│   │   └── validators.py    # schema validation helpers
│   └── main.py              # orchestrates the pipeline
├── data/
│   ├── raw/
│   │   └── mp_raw.json       # Materials Project dump (if download succeeds)
│   ├── processed/
│   │   ├── alloys_clean.parquet   # **AlloyRecord** objects after cleaning
│   │   └── alloys_ilr.parquet
│   └── logs/
│       ├── app.log
│       └── exclusion_log.txt
├── results/
│   ├── model_metrics.json
│   ├── feature_importance.json
│   ├── collinearity_diagnostic.json
│   └── final_report.md
├── tests/
│   ├── test_data.py
│   ├── test_analysis.py
│   └── test_contracts.py
├── contracts/                # copies of schema files
├── requirements.txt
└── README.md
```

## Contract Traceability
| Contract | FR(s) Covered | SC(s) Covered |
|----------|---------------|----------------|
| `contracts/dataset.schema.yaml` | FR‑001, FR‑002, FR‑003, FR‑009, FR‑010 | SC‑001 |
| `contracts/model_metrics.schema.yaml` | FR‑004, FR‑005 | SC‑002 |
| `contracts/feature_importance.schema.yaml` | FR‑006 | SC‑003 |
| `contracts/collinearity_diagnostic.schema.yaml` | FR‑007 | SC‑004 |
| (implicit) associational framing documented in `final_report.md` | FR‑008 | SC‑005, SC‑006 |

## Phase / Task Breakdown (maps FR / SC) – **operating on `AlloyRecord` objects**

| Phase | Script(s) | Outputs | FR(s) | SC(s) | Notes |
|-------|-----------|---------|-------|-------|-------|
| **0 – Spec Amendment** | Draft `AMP-001` (see above) | – | FR‑001 | SC‑001 | Documents data‑source limitation. |
| **1 – Data Extraction** | `code/data/download.py` → `data/raw/mp_raw.json` | – | FR‑001 | SC‑001 | Uses `matminer`; aborts on network error. |
| **2 – Cleaning & Filtering** | `code/data/clean.py` → `data/processed/alloys_clean.parquet`; writes `exclusion_log.txt` & `app.log` | `AlloyRecord` objects in `alloys_clean.parquet` | FR‑002, FR‑003, FR‑009, FR‑010 | SC‑001, SC‑006 | Enforces composition sum, unit conversion, Poisson‑ratio independence. |
| **3 – Abort on Tiny Dataset** | Size check after cleaning | – | FR‑004 (power safeguard) | – | If `<20` records, pipeline logs error and exits. |
| **4 – Diagnostics** | `code/data/transform.py` computes VIF on raw fractions → `collinearity_diagnostic.json` | `results/collinearity_diagnostic.json` | FR‑007 | SC‑004 | Flags VIF > 5. |
| **5 – ILR Transformation** | `code/data/transform.py` adds ILR columns → `alloys_ilr.parquet` | `data/processed/alloys_ilr.parquet` | FR‑004 | SC‑002 | Chooses 5‑fold CV or LOOCV based on N. |
| **6 – Train/Test Split** | `code/analysis/train.py` creates an 80/20 split (stratified by ν) **before** any CV. | `train_set.parquet`, `test_set.parquet` (intermediate) | FR‑004, FR‑005 | SC‑002 | Ensures no leakage. |
| **7 – Model Training (CV)** | `code/analysis/train.py` runs 5‑fold CV **on the training set only** (or LOOCV if N < 50). | `results/model_metrics.json` | FR‑004, FR‑005 | SC‑002 | Logs CV MAE; flags MAE > 0.05. |
| **8 – Test‑Set Evaluation** | `code/analysis/train.py` evaluates the fitted model on the held‑out test set. | `results/model_metrics.json` (updated) | FR‑005 | SC‑002 | Records test‑set MAE separately. |
| **9 – Primary Feature Importance** | `code/analysis/interpret.py` computes permutation importance on the **original compositional features** (by permuting, ILR‑transforming each permutation, and measuring MAE drop). | `results/feature_importance.json` (permutation scores) | FR‑006, FR‑008 | SC‑003, SC‑005 | Provides the definitive element ranking. |
| **10 – Exploratory Back‑Transformation** | `code/analysis/interpret.py` back‑transforms Gini‑based ILR importances using `B⁻¹` (Appendix A) for exploratory insight only. | `results/feature_importance.json` (adds `exploratory_ilr_backtransform` field) | FR‑006 | SC‑003 | Marked as exploratory, not primary. |
| **11 – Reporting** | `code/main.py` assembles the final markdown report (`final_report.md`). | `results/final_report.md` | FR‑008 | SC‑005, SC‑06 | Uses explicit associational language and notes the data‑source limitation. |
| **12 – Validation** | `pytest tests/test_contracts.py` | – | All contracts | All SC | Fails fast if any artifact violates schema. |
| **13 – Reproducibility** | Record SHA‑256 checksums in `data/checksums.json`; update `state/...yaml` | – | – | – | Supports Constitution I. |

### Compute & Data Feasibility
- **CPU‑first**: Random Forest on ≤ 1 000 rows with 5 features finishes < 1 min on 2 cores.  
- **Memory**: < 200 MB for all pandas dataframes.  
- **Disk**: Raw Materials Project dump ≈ a few GB; all intermediate parquet files ≤ 200 MB.  
- **GPU**: Not required; no CUDA‑dependent libraries used.  

### Data Availability
- No verified URL provides the required alloy composition + Poisson’s ratio measured independently. Consequently, the pipeline will **abort** if the Materials Project download fails (see Spec Amendment AMP‑001). No synthetic stand‑in is used.

---


