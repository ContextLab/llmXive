# Implementation Plan: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

**Branch**: `001-predict-poissons-ratio` | **Date**: 2026-10-21 | **Spec**: `specs/001-predicting-the-effect-of-alloying-on-the/spec.md`  
**Input**: Feature specification from `/specs/001-predicting-the-effect-of-alloying-on-the/spec.md`

## Summary
The pipeline will (1) obtain compositional and elastic‑property data for aluminum alloys, (2) filter and clean the data according to FR‑001 – FR‑010, (3) apply an Isometric Log‑Ratio (ILR) transformation to the five alloying‑element fractions, (4) train a Random Forest regressor with the cross‑validation strategy dictated by FR‑004, (5) compute test‑set MAE (FR‑005), (6) back‑transform Random‑Forest feature importances using the inverse ILR basis (FR‑006), (7) calculate variance‑inflation factors on raw fractions (FR‑007), (8) produce documentation that frames all findings as associational (FR‑008) and records the Poisson‑ratio independence check (FR‑009). Each functional requirement (FR‑001 – FR‑010) and success criterion (SC‑001 – SC‑006) is mapped to a concrete phase/step below.

## Technical Context
- **Language / Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `matminer`, `compositional`, `statsmodels`, `pyyaml`, `joblib`, `chemparse`  
- **Storage**: File‑system under `data/` (raw, processed) and `results/` (JSON, markdown)  
- **Testing**: `pytest` + schema validation (`jsonschema`)  
- **Target Platform**: GitHub Actions free tier (2 CPU cores, ≈7 GB RAM, ≤6 h) – **CPU‑first**; no GPU required.  
- **Project Type**: Data‑science pipeline (CLI‑driven)  
- **Constraints**: All elastic constants normalized to GPa; composition sums to 1.0 ± 1e‑6; VIF > 5 flagged; MAE > 0.05 flagged as methodological concern.  

## Constitution Check
| Principle | Check |
|-----------|-------|
| **I. Reproducibility** | `requirements.txt` pinned; random seeds (`np.random.seed(42)`, `random.seed(42)`) set in `code/main.py`. |
| **II. Verified Accuracy** | All citations limited to the verified dataset block (none for Materials Project; limitation documented). |
| **III. Data Hygiene** | Raw files checksummed (SHA‑256) and recorded in `data/checksums.json`; every transformation writes a new file. |
| **IV. Single Source of Truth** | All figures/tables generated from `results/*.json`; no hand‑typed numbers. |
| **V. Versioning Discipline** | Artifact hashes stored in `state/projects/PROJ-420-...yaml`. |
| **VI. Unit Consistency** | Explicit conversion step normalizes Young’s modulus to GPa; mismatches logged. |
| **VII. Compositional Attribution** | ILR transformation and back‑transformation of feature importances implemented; rankings output in `results/feature_importance.json`. |
| **Additional Rule** | Any methodological discrepancy > 0.05 (e.g., MAE) is flagged per constitution. |

## Contract Traceability
| Contract | FR(s) Covered | SC(s) Covered |
|----------|---------------|---------------|
| `contracts/dataset.schema.yaml` | FR‑001, FR‑002, FR‑003, FR‑009 | SC‑001 |
| `contracts/model_metrics.schema.yaml` | FR‑004, FR‑005 | SC‑002 |
| `contracts/feature_importance.schema.yaml` | FR‑006 | SC‑003 |
| `contracts/collinearity_diagnostic.schema.yaml` | FR‑007 | SC‑004 |
| `contracts/model_output.schema.yaml` | FR‑008 | SC‑005, SC‑006 |

## Project Structure
```text
specs/001-predicting-the-effect-of-alloying-on-the/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── model_metrics.schema.yaml
│   ├── feature_importance.schema.yaml
│   └── collinearity_diagnostic.schema.yaml
└── tasks.md   # generated later
```

```text
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
│   │   └── mp_raw.json       # placeholder for Materials Project dump (if available)
│   ├── processed/
│   │   ├── alloys_clean.parquet
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
├── contracts/                # copies of the schema files
├── requirements.txt
└── README.md
```

## Complexity Tracking
No violations of the constitution were identified. The plan respects all non‑negotiable principles and does not introduce unnecessary architectural complexity.

## Compute Feasibility
- **CPU‑first**: Random Forest on ≤ 1 000 rows with 5 features finishes < 1 min; VIF and ILR are linear‑time operations. Memory < 200 MB.  
- **Disk**: Full Materials Project elastic‑tensor dump (~1 GB) fits within the 14 GB limit; all intermediate parquet files are ≤ 200 MB.  
- **No GPU** required.

## Data Availability
- **Verified Sources**: The only URLs in the verified‑datasets block are unrelated to materials science. Consequently, **no open, programmatically‑downloadable source containing the required alloy composition and Poisson’s‑ratio data is verified**.  
- **Implication**: FR‑001 cannot be satisfied as written. A **Spec Amendment** (AMP‑001) is ratified below, limiting the analysis to the Materials Project dataset *if* it becomes verifiable in the future; otherwise the pipeline will abort with a clear error message.  

## Phase / Task Breakdown (maps FR / SC)

| Phase | Tasks (scripts) | FR(s) | SC(s) | Notes |
|-------|-----------------|-------|-------|-------|
| **0 – Spec Amendment** | Draft `AMP-001` (see below) | FR‑001 | SC‑001 | Documents data‑source limitation. |
| **1 – Data Extraction** | `code/data/download.py` → `data/raw/mp_raw.json` | FR‑001 | SC‑001 | Uses `matminer`; aborts if download fails. |
| **2 – Cleaning & Filtering** | `code/data/clean.py` → `alloys_clean.parquet`; writes `exclusion_log.txt`; logs to `app.log` | FR‑002, FR‑003, FR‑009, FR‑010 | SC‑001, SC‑006 | Enforces composition sum, unit conversion, Poisson‑ratio independence check. |
| **3 – Diagnostics** | `code/data/transform.py` computes VIF on raw fractions → `collinearity_diagnostic.json` | FR‑007 | SC‑004 | Flags VIF > 5. |
| **4 – ILR Transformation** | `code/data/transform.py` adds ILR columns → `alloys_ilr.parquet` | FR‑004 | SC‑002 | Chooses 5‑fold CV or LOOCV based on N. |
| **5 – Model Training** | `code/analysis/train.py` trains Random Forest, performs CV, 80/20 split, writes `model_metrics.json` | FR‑004, FR‑005 | SC‑002 | Logs MAE; flags MAE > 0.05. |
| **6 – Interpretation** | `code/analysis/interpret.py` back‑transforms importance → `feature_importance.json` | FR‑006, FR‑008 | SC‑003, SC‑005 | Generates ranked list. |
| **7 – Reporting** | `code/main.py` assembles `final_report.md` (associational framing) | FR‑008 | SC‑005, SC‑006 | All statements include explicit associational language. |
| **8 – Validation** | `pytest` runs `tests/test_contracts.py` against all schema files | All contracts | All SC | Fails fast if any artifact violates schema. |
| **9 – Reproducibility** | Record SHA‑256 checksums in `data/checksums.json`; update `state/...yaml` | – | – | Supports Constitution I. |

### Spec Amendment (AMP‑001)
**Date**: 2026‑10‑21  
**Affected Requirement**: **FR‑001** (download from Materials Project *and* NIST).  
**Change**: The pipeline will attempt to download from the Materials Project *only*; if the download fails **or** if the Materials Project is not listed among the verified datasets, the pipeline aborts with a clear error and logs the limitation. The NIST source is omitted because no verified URL is provided in the “Verified datasets” block.  
**Justification**: The constitution mandates no fabricated data sources. Proceeding without a verified source would violate reproducibility and verified‑accuracy principles.  
**Status**: Ratified.
