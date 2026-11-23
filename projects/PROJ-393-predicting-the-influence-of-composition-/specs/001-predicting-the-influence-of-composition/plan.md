# Implementation Plan: Predicting the Influence of Composition on the Magnetic Hysteresis of Heusler Alloys

**Branch**: `001-predict-heusler-hysteresis` | **Date**: 2026-10-22 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-predict-heusler-hysteresis/spec.md`

## Summary
This plan delivers a reproducible CPU‑only pipeline that (1) aggregates experimental Heusler‑alloy hysteresis data from three distinct sources, (2) standardizes composition and hysteresis units, (3) applies **mean imputation** (≤ 15 % imputation rate) **only to non‑target numeric fields**; target variables with missing values are dropped, (4) computes eight composition‑based descriptors, (5) trains linear regression and random‑forest models with 5‑fold CV, (6) validates models via appropriate statistical tests (F‑test for linear, permutation test for RF), bootstrap confidence intervals (1000 resamples of observations), and partial‑dependence plots, (7) generates mandatory reports (`final_report.md`, `statistical_limitations.md`, `microstructure_note.md`, `data_scarcity_warning.md`). All steps respect the project constitution and the success criteria.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `requests`, `tqdm`  
- **Storage**: CSV/Parquet files under `data/` (raw, processed, features)  
- **Testing**: `pytest` (unit & integration)  
- **Target Platform**: GitHub Actions free‑tier (2 CPU, ~7 GB RAM, ≤6 h)  
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
│   ├── alloy_entry.schema.yaml
│   ├── composition_descriptor.schema.yaml
│   ├── model_output.schema.yaml
│   └── model_result.schema.yaml
└── tasks.md   # generated later
code/
├── data/
│   ├── raw/                # original downloads (NIST CSV, journal supplement, manual extracts)
│   ├── processed/          # cleaned CSVs, feature tables
│   └── checksums.txt
├── src/
│   ├── ingestion/          # fetch_nist.py, fetch_journal.py, manual_curate.py
│   ├── preprocessing/      # unit_normalization.py, mean_impute.py, dft_filter.py
│   ├── features/           # descriptors.py
│   ├── modeling/           # train.py, evaluate.py
│   ├── validation/         # f_test.py, permutation_test.py, bootstrap_ci.py, pdp.py
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
| Exploratory framing | SC‑006 (R² ≥ 0.6) is unrealistic for N≈54; framing avoids false‑negative failure. | Treating the benchmark as a hard pass/fail would misrepresent scientific reality. |
| Expanded descriptor set | Increases construct validity and mitigates omitted‑variable bias (concern methodology‑dde8ab7a). | Sticking with only five descriptors would limit model expressiveness. |

## Implementation Phases

### Phase 0 – Research & Validation
1. **0.1 Source Verification** – Confirm that NIST MDR, at least one journal supplement, and manual literature provide *experimental* hysteresis data. Record URLs and DOIs.  
2. **0.2 Reference‑Validator Gate** – Run the Reference‑Validator on all citations in `research.md`. Abort if any citation fails.  
3. **0.3 Power Analysis** – With N = 54, 5 predictors, α = 0.05, detectable effect size ≈ R² = 0.35 (power ≈ 0.2). Document that achieving R² ≥ 0.6 is statistically unlikely; the study will therefore be framed as exploratory and the achieved R² will be reported descriptively (addresses methodology‑ad33ecaa and methodology‑9e59e226).

### Phase 1 – Data Engineering & Contracts
| Step | Action | Output |
|------|--------|--------|
| **1.1 Ingestion** | Download NIST CSV via HuggingFace URL (if available) or API; fetch journal supplement CSV/Excel; parse manually curated tables (CSV). Store raw files under `data/raw/` and record SHA‑256 checksums. | `data/raw/nist.csv`, `data/raw/journal_supplement.csv`, `data/raw/manual_curated.csv` |
| **1.2 Preprocessing** | *Unit normalization* (coercivity → Oe; saturation → emu/g). *DFT filter*: drop rows where `is_dft == True`. *Missing‑value handling*: **mean imputation** column‑wise for non‑target fields only; compute and log **imputation rate** (must be < 15 %). Rows with missing target (`coercivity` or `saturation`) are **dropped** (no target imputation). | `data/processed/alloys_clean.csv`, `data/processed/imputation_report.json` |
| **1.3 Completeness Metric** | Compute per‑source completeness: proportion of rows with non‑null composition **and** hysteresis values. Verified distinct experimental entries = a substantial set of entries (source: Q39304236). | `data/processed/completeness_report.json` |
| **1.4 Feature Engineering** | Load fixed `elemental_properties.csv`; compute eight descriptors (average electronegativity, VEC, atomic radii variance, d‑band filling, size mismatch, average atomic mass, electron affinity, Pettifor chemical scale) with ≥ 4 decimal places. One‑hot encode `synthesis_method` and `crystal_structure` where available. Append to clean dataset. | `data/processed/alloys_features.csv` |
| **1.5 Contract Validation – AlloyEntry** | Validate `alloys_clean.csv` against `contracts/alloy_entry.schema.yaml`. Abort if validation fails. | N/A |
| **1.5b Contract Validation – CompositionDescriptor** | Validate `alloys_features.csv` against `contracts/composition_descriptor.schema.yaml`. Abort if validation fails. | N/A |
| **1.6 Contract Validation – Model Output** | After modeling, validate `model_results.json` against `contracts/model_output.schema.yaml` and `contracts/model_result.schema.yaml`. | N/A |

### Phase 2 – Modeling & Training
| Step | Action | Output |
|------|--------|--------|
| **2.1 Feature Matrix Construction** | One‑hot encode `synthesis_method` and `crystal_structure`; concatenate with eight composition descriptors. | `data/processed/feature_matrix.npy` |
| **2.2 Train Baseline Linear Regression** | 5‑fold CV (`random_state=42`); hyperparameter `fit_intercept=True`. Record mean R², MAE. | `models/linear_regression.pkl`, `reports/linear_metrics.json` |
| **2.3 Train Random Forest** | Grid search over `n_estimators=[100,200]`, `max_depth=[5,10,None]`; 5‑fold CV; `random_state=42`. Record mean R², MAE. | `models/random_forest.pkl`, `reports/rf_metrics.json` |
| **2.4 Feature Importance** | Permutation importance (10 repeats) on the full training set; retain top 3 features. | `reports/feature_importance.json` |
| **2.5 Sensitivity Analysis** | Re‑run models on the **complete‑case** dataset (rows with no imputed fields) and compare performance to the mean‑imputed baseline; report differences. | `reports/sensitivity_analysis.json` |

### Phase 3 – Statistical Validation & Reporting
| Step | Action | Output |
|------|--------|--------|
| **3.1 Null Model & F‑test (Linear Only)** | Null model = mean prediction. Compute RSS for linear regression; perform F‑test (α = 0.05, Bonferroni‑adjusted for two targets). Report p‑value. | `reports/f_test_linear.json` |
| **3.2 Permutation Test (Random Forest)** | Perform a permutation test (10 000 permutations) to assess whether the RF improvement over the null model is significant. | `reports/perm_test_rf.json` |
| **3.3 Bootstrapping (Observations)** | Resample the **original observations** with replacement 1000 times (verified count = 1000). For each bootstrap sample, fit the linear model and record R²; compute a **95 % confidence interval** for R². | `reports/bootstrap_ci.json` |
| **3.4 Partial Dependence Plots** | Generate PDPs for the top 3 features for each target (coercivity, saturation). Save PNGs. | `docs/reports/pdp_coercivity.png`, `docs/reports/pdp_saturation.png` |
| **3.5 Data‑Scarcity Warning** | Because N = 54 < 100, automatically generate `data_scarcity_warning.md` stating reduced statistical power and potential overfitting. | `docs/reports/data_scarcity_warning.md` |
| **3.6 Statistical Limitations** | Write `statistical_limitations.md` containing the mandatory disclaimer that the F‑test validates fit, not mechanism, and note microstructural confounders. | `docs/reports/statistical_limitations.md` |
| **3.7 Microstructure Note** | Write `microstructure_note.md` logging synthesis methods and crystal structures and emphasizing their influence on hysteresis. | `docs/reports/microstructure_note.md` |
| **3.8 Final Report Assembly** | Collate metrics, completeness, imputation report, warnings, and all figures into `final_report.md`. Include a descriptive statement of achieved R² versus the exploratory benchmark (SC‑006). | `docs/reports/final_report.md` |
| **3.9 Model Output Validation** | Validate the generated `model_results.json` against `contracts/model_output.schema.yaml` and `contracts/model_result.schema.yaml`. Abort if validation fails. | N/A |

### Phase 4 – Versioning & Finalization
1. Compute SHA‑256 hashes for all data artifacts and model files; update `state/projects/PROJ-393...yaml` with `artifact_hashes` and `updated_at`.  
2. Tag the Git commit with `v0.1.0` and push to the feature branch.

## Alignment of Functional Requirements & Success Criteria
| FR | Mapped Phase / Step |
|----|----------------------|
| FR‑001 | 1.1 Ingestion |
| FR‑002 | 1.2 Preprocessing (mean imputation, target‑drop rule) |
| FR‑003 | 1.4 Feature Engineering (8 descriptors) |
| FR‑004 | 2.2 & 2.3 Model Training |
| FR‑005 | 3.1‑3.4 Statistical Validation |
| FR‑008 | 1.2 DFT filter & 3.5 Data‑scarcity warning |
| FR‑009 | 3.6 Statistical Limitations report |
| FR‑010 | 3.7 Microstructure Note report |
| SC‑001 | 3.1 F‑test p‑value (linear) |
| SC‑002 | 3.3 Bootstrap 95 % CI |
| SC‑003 | 3.4 PDPs |
| SC‑004 | 1.3 Completeness metric (54 distinct entries) |
| SC‑005 | Entire pipeline runs on CPU within GH Actions limits |
| SC‑006 | Revised: report achieved R² and discuss power; no hard pass/fail (exploratory benchmark) |

---

