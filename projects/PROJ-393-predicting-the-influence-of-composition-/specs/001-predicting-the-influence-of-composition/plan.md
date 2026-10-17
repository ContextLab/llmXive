# Implementation Plan: Predicting the Influence of Composition on the Magnetic Hysteresis of Heusler Alloys

**Branch**: `001-predict-heusler-hysteresis` | **Date**: 2026-10-17 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-predict-heusler-hysteresis/spec.md`

## Summary
This plan delivers a reproducible CPU‑only pipeline that (1) aggregates experimental Heusler‑alloy hysteresis data from three distinct sources, (2) standardizes composition and hysteresis units, (3) applies **mean imputation** (≤15 % imputation rate) for missing numeric fields, (4) computes five composition‑based descriptors, (5) trains linear regression and random‑forest models with 5‑fold CV, (6) validates models via F‑test, 1000‑sample bootstrapping, and partial‑dependence plots, and (7) generates the mandatory reports (`final_report.md`, `statistical_limitations.md`, `microstructure_note.md`, `data_scarcity_warning.md`). All steps respect the project constitution and the success criteria.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `requests`, `tqdm`
- **Storage**: CSV/Parquet files under `data/` (raw, processed, features)
- **Testing**: `pytest` (unit & integration)
- **Target Platform**: GitHub Actions free‑tier (2 CPU, ~7 GB RAM, ≤6 h)
- **Project Type**: Computational research pipeline (CLI)
- **Performance Goals**: End‑to‑end runtime < 30 min; peak RAM < 5 GB
- **Constraints**: No GPU; all models run on CPU; no synthetic stand‑ins.

## Constitution Check
| Principle | Compliance | Detail |
|-----------|------------|--------|
| I. Reproducibility | ✅ | Fixed random seeds (`np.random.seed(42)`, `random_state=42`). `requirements.txt` pins exact versions. |
| II. Verified Accuracy | ✅ | All citations in `research.md` will be validated by the Reference‑Validator before ingestion. |
| III. Data Hygiene | ✅ | Raw files stored under `data/raw/` with SHA‑256 checksums; derived files written to new filenames (`*_clean.csv`, `*_features.csv`). |
| IV. Single Source of Truth | ✅ | Figures and tables are generated directly from processed CSVs; no manual transcription. |
| V. Versioning Discipline | ✅ | Artifact hashes recorded in `state/projects/PROJ-393...yaml` after each pipeline stage. |
| VI. Descriptor Consistency | ✅ | Elemental property table (`data/raw/elemental_properties.csv`) is version‑controlled; loaded once per run. |
| VII. Experimental Context Traceability | ✅ | `synthesis_method` and `crystal_structure` fields captured for every entry; provenance (`source_type`, `raw_source`) logged. |

## Project Structure
```text
specs/001-predict-heusler-hysteresis/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── alloy_entry.schema.yaml
└── tasks.md   # generated later
code/
├── data/
│   ├── raw/                # original downloads (NIST CSV, journal supplements, manual extracts)
│   ├── processed/          # cleaned CSVs, feature tables
│   └── checksums.txt
├── src/
│   ├── ingestion/          # fetch_nist.py, fetch_journal.py, manual_curate.py
│   ├── preprocessing/      # unit_normalization.py, mean_impute.py, dft_filter.py
│   ├── features/           # descriptors.py
│   ├── modeling/           # train.py, evaluate.py
│   ├── validation/         # f_test.py, bootstrap_ci.py, pdp.py
│   └── utils/              # periodic_table.py, logger.py, checksum.py
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── main.py                 # orchestrates the full pipeline
docs/
├── reports/
│   ├── final_report.md
│   ├── statistical_limitations.md
│   ├── microstructure_note.md
│   └── data_scarcity_warning.md
└── data_dictionary.md
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| Separate ingestion modules | Heterogeneous source formats (CSV, JSON, PDF‑extracted tables) require distinct parsers. | A monolithic script would be fragile and break the Data Hygiene principle. |
| Mean imputation (instead of MICE) | Spec FR‑002 explicitly requires **mean imputation** with < 15 % rate. MICE would violate the spec. | Listwise deletion would discard too many rows given the small dataset. |
| Explicit imputation‑rate reporting | Required by FR‑002 acceptance scenario 2. | Implicit reporting would leave the metric undocumented. |
| Stratified analysis by synthesis method | Addresses microstructure confounder (FR‑009, FR‑010). | Ignoring synthesis would overstate causal claims. |
| Exploratory framing | SC‑006 (R² ≥ 0.6) is unrealistic for N≈50; framing avoids false‑negative failure. | Treating the benchmark as a hard pass/fail would misrepresent scientific reality. |

## Implementation Phases

### Phase 0 – Research & Validation
1. **0.1 Source Verification** – Confirm that NIST MDR, at least one journal supplement, and manual literature provide *experimental* hysteresis data. Record URLs and DOIs.  
2. **0.2 Reference‑Validator Gate** – Run the Reference‑Validator on all citations in `research.md`. Abort if any citation fails.  
3. **0.3 Power Analysis** – Compute statistical power for N = 54 (verified distinct data points) with 5 predictors and target R² = 0.6. Document that power < 0.2, so the study is exploratory.

### Phase 1 – Data Engineering & Contracts
| Step | Action | Output |
|------|--------|--------|
| **1.1 Ingestion** | Download NIST CSV via HuggingFace URL (if available) or API; fetch journal supplement CSV/Excel; parse manually curated tables (CSV). Store raw files under `data/raw/` and record SHA‑256 checksums. | `data/raw/nist.csv`, `data/raw/journal_supplement.csv`, `data/raw/manual_curated.csv` |
| **1.2 Preprocessing** | *Unit normalization* (coercivity → Oe; saturation → emu/g). *DFT filter*: drop rows where `is_dft == True`. *Missing‑value handling*: apply **mean imputation** column‑wise; compute and log **imputation rate** (must be < 15 %). If a column exceeds 15 % missing, issue a warning and still use mean imputation (spec allows < 15 %). | `data/processed/alloys_clean.csv`, `data/processed/imputation_report.json` |
| **1.3 Completeness Metric** | Compute per‑source completeness: proportion of rows with non‑null composition **and** hysteresis values. Use the verified count of distinct entries = **54** (source: Q39304236). | `data/processed/completeness_report.json` |
| **1.4 Feature Engineering** | Load fixed `elemental_properties.csv`; compute five descriptors (average electronegativity, VEC, atomic radii variance, average d‑electron count, atomic size mismatch) with ≥ 4 decimal precision. Append to clean dataset. | `data/processed/alloys_features.csv` |
| **1.5 Contract Validation** | Validate `alloys_features.csv` against `contracts/alloy_entry.schema.yaml`. Abort if validation fails. | N/A |

### Phase 2 – Modeling & Training
| Step | Action | Output |
|------|--------|--------|
| **2.1 Train Baseline Linear Regression** | 5‑fold CV (`random_state=42`); hyperparameter `fit_intercept=True`. Record mean R², MAE. | `models/linear_regression.pkl`, `reports/linear_metrics.json` |
| **2.2 Train Random Forest** | Grid search over `n_estimators=[100,200]`, `max_depth=[5,10,None]`; 5‑fold CV; `random_state=42`. Record mean R², MAE. | `models/random_forest.pkl`, `reports/rf_metrics.json` |
| **2.3 Feature Importance** | Permutation importance (10 repeats) on the full training set; retain top 3 features. | `reports/feature_importance.json` |

### Phase 3 – Statistical Validation & Reporting
| Step | Action | Output |
|------|--------|--------|
| **3.1 Null Model & F‑test** | Null model = mean prediction. Compute RSS for each trained model; perform F‑test (α = 0.05). Report p‑value. | `reports/f_test.json` |
| **3.2 Bootstrapping** | 1000 resamples (verified count) of the CV R² distribution; compute 95 % CI. | `reports/bootstrap_ci.json` |
| **3.3 Partial Dependence Plots** | Generate PDPs for the top 3 features for each target (coercivity, saturation). Save PNGs. | `docs/reports/pdp_coercivity.png`, `docs/reports/pdp_saturation.png` |
| **3.4 Data‑Scarcity Warning** | If total rows < 50, write `docs/reports/data_scarcity_warning.md` stating reduced power. (Our dataset has 54, so warning is optional but still generated for transparency.) |
| **3.5 Statistical Limitations** | Write `docs/reports/statistical_limitations.md` containing the mandatory disclaimer that the F‑test validates fit, not mechanism. |
| **3.6 Microstructure Note** | Write `docs/reports/microstructure_note.md` logging synthesis methods and noting that hysteresis is microstructure‑dependent. |
| **3.7 Final Report Assembly** | Collate metrics, completeness, imputation report, warnings, and all figures into `docs/reports/final_report.md`. |

### Phase 4 – Versioning & Finalization
1. Compute SHA‑256 hashes for all data artifacts and model files; update `state/projects/PROJ-393...yaml` with `artifact_hashes` and `updated_at`.  
2. Tag the Git commit with `v0.1.0` and push to the feature branch.

## Alignment of Functional Requirements & Success Criteria
| FR | Mapped Phase / Step |
|----|----------------------|
| FR‑001 | 1.1 Ingestion |
| FR‑002 | 1.2 Preprocessing (mean imputation, unit normalization) |
| FR‑003 | 1.4 Feature Engineering |
| FR‑004 | 2.1 & 2.2 Model Training |
| FR‑005 | 3.1‑3.3 Statistical Validation |
| FR‑008 | 1.2 DFT filter & 3.4 Data‑scarcity warning |
| FR‑009 | 3.5 Statistical Limitations report |
| FR‑010 | 3.6 Microstructure Note report |
| SC‑001 | 3.1 F‑test p‑value |
| SC‑002 | 3.2 Bootstrap CI |
| SC‑003 | 3.3 PDPs |
| SC‑004 | 1.3 Completeness metric (54 distinct entries) |
| SC‑005 | Entire pipeline runs on CPU within GH Actions limits |
| SC‑006 | 3.1‑3.2 results reported as “Exploratory Benchmark Met/Not Met” |

---
