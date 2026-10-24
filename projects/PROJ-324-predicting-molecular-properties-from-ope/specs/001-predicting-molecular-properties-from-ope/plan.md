# Implementation Plan: Molecular Property Prediction Pipeline

**Branch**: `324-molecular-property-prediction`  
**Date**: 2026-10-23  
**Spec**: `spec.md`  
**Input**: Feature specification from `/specs/324-molecular-property-prediction/spec.md`

## Summary
The pipeline will (1) download experimental molecular data from PubChem via PubChemPy, (2) preprocess to retain only experimental logP, solubility, and boiling point records and enforce quality thresholds, (3) generate **MACCS** and **ECFP4** fingerprints with Open Babel (FP2 omitted to respect the 2 200‑bit limit), (4) compute property‑specific additive baselines, (5) train a Random Forest model using nested 5‑fold cross‑validation, (6) compare RF to the baseline with three property‑wise paired Wilcoxon signed‑rank tests (one per property) applying Holm‑Bonferroni correction (α = 0.05) and a non‑parametric bootstrap test for combined significance, (7) compute SHAP values and SHAP interaction matrices, (8) validate SHAP interactions via a **bootstrap‑of‑model** approach (200 resamples) rather than target permutation, (9) **select the top‑100 MACCS bits** by **mean absolute SHAP interaction strength** computed **only on inner‑validation folds** (split‑based selection to avoid leakage), (10) compute the **Local Non‑Additivity Index (LNAI)** for all ≤ 4 950 bit‑pairs that satisfy prevalence filters, **adjusting for each bit’s main effect**, using **2 000 permutations** (Numba‑accelerated) and Benjamini‑Hochberg FDR correction (α = 0.05), (11) map SHAP bits back to chemical substructures and achieve precision ≥ 0.8 and recall ≥ 0.7 against a curated reference set, (12) generate visual artifacts (RF residual plot, SHAP interaction heatmap), (13) produce an Interaction‑Zone Report PDF, (14) obtain expert review from two independent chemists and record acceptance in a Validation Report PDF, (15) compute a **per‑molecule LNAI** (average of significant pairwise LNAI values) and output `lna_index_per_molecule.csv`, (16) generate schema‑compliant `predictions_schema.csv` and `molecules_schema.csv`, (17) compile a comprehensive Validation Audit PDF. All steps are deterministic, reproducible, and fit within the GitHub Actions free‑tier compute envelope.

## Technical Context
- **Language/Version**: Python 3.10+  
- **Primary Dependencies**: `pubchempy`, `rdkit`, `scikit-learn`, `shap`, `openbabel` (CLI), `pandas`, `numpy`, `matplotlib`, `pyyaml`, `pytest`, `ruff`, `black`, `numba`  
- **Storage**: File hierarchy under `data/` (`raw/`, `processed/`, `derived/`)  
- **Testing**: `pytest` (unit & integration)  
- **Target Platform**: Linux GitHub Actions free tier (2 CPU cores, 7 GB RAM, 14 GB disk)  
- **Performance Goals**: End‑to‑end ≤ 4 h on CPU; no GPU required.  
- **Constraints**: `max_depth ≤ 15`, `n_estimators ≤ 300`, fingerprint length ≤ 2 200 bits (MACCS 166 + ECFP4 1024 = 1 190 bits), top‑K = 100 MACCS bits.

## Constitution Check
| Principle | Satisfied? | How Satisfied |
|-----------|------------|----------------|
| I. Reproducibility | ✅ | Fixed seeds (`seed=42`), immutable `requirements.txt`, deterministic Open Babel flags. |
| II. Verified Accuracy | ✅ | PubChemPy endpoint verified; URLs logged in `verification_log.txt`. |
| III. Data Hygiene | ✅ | SHA‑256 recorded in `state/artifact_hashes.yaml`; all transformations write new files. |
| IV. Single Source of Truth | ✅ | Every figure/table generated directly from files under `data/derived/`. |
| V. Versioning Discipline | ✅ | Content hashes stored in `state/projects/…yaml`; timestamps updated on each artifact change. |
| VI. Non‑Additivity Interaction Mapping | ✅ | Baseline vs. RF residuals compared; top‑K bits selected without leakage; LNAI computed with main‑effect adjustment; per‑molecule LNAI added; Interaction‑Zone Report produced. |
| VII. Computational Efficiency | ✅ | CPU‑first implementation; pairwise LNAI limited to ≤ 4 950 tests; permutation count reduced to 2 000; Numba‑accelerated loops keep runtime ≤ 4 h (estimated). |

## Project Structure
```text
projects/PROJ-324-predicting-molecular-properties-from-ope/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── download.py          # PubChem download & checksum
│   │   ├── preprocess.py        # Quality filtering, experimental‑only flag
│   │   └── fingerprint.py       # Open Babel wrapper (MACCS, ECFP4)   # FP2 removed
│   ├── models/
│   │   ├── baseline.py          # Property‑specific additive baselines
│   │   └── rf.py                # Random Forest with nested CV
│   ├── analysis/
│   │   ├── stats.py             # Metrics, Wilcoxon test, LNAI, precision/recall, power analysis
│   │   └── explainability.py    # SHAP, bootstrap interaction validation, SMARTS mapping, report generation
│   └── main.py                  # Orchestration script
├── data/
│   ├── raw/
│   ├── processed/
│   └── derived/
├── reference/
│   └── substructures.yaml       # Curated substructure reference set
├── contracts/
│   ├── dataset.schema.yaml
│   ├── fingerprint.schema.yaml
│   ├── interaction_context.schema.yaml
│   ├── molecule.schema.yaml
│   ├── output.schema.yaml
│   └── prediction.schema.yaml
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
├── pyproject.toml
└── .ruff.toml
```

## Phase Plan & Task Dependency Graph
All tasks run **sequentially** (`[S]`). No parallel tags are used where a dependency exists.

| ID | Description | Tags | Depends on |
|----|-------------|------|------------|
| **T001** | *Data download*: Retrieve experimental SMILES + logP, solubility, boiling point from PubChem via PubChemPy, write `data/raw/pubchem.csv`. | [S] | – |
| **T002** | *Preprocess & quality*: Filter to `property_type="Experimental"`, enforce ≤ 5 % missing covariates, retain records with confidence ≥ 0.9, generate `data/derived/data_quality_report.csv`. | [S] | T001 |
| **T003** | *Verification log*: Record URL verification outcomes in `data/derived/verification_log.txt`. | [S] | T001 |
| **T004** | *Baseline computation*: Compute additive‑fragment baseline predictions for logP (Crippen fragments) and linear models for solubility & boiling point. Output `data/derived/baseline_predictions.csv`. | [S] | T002 |
| **T005** | *Baseline residual plot*: Generate `data/derived/baseline_residuals.png`. | [S] | T004 |
| **T006** | *Fingerprint generation*: Wrapper around `obabel` to produce **MACCS** and **ECFP4** fingerprints for each SMILES. (FP2 omitted to respect the bit‑length constraint.) | [S] | T002 |
| **T007** | *Fingerprint storage*: Save arrays as memory‑mapped NumPy files under `data/processed/`. | [S] | T006 |
| **T008** | *Nested CV*: Outer 5‑fold CV; inner 5‑fold CV tunes `max_features` & `min_samples_leaf`. Trains Random Forest (`n_estimators=300`, `max_depth=15`). | [S] | T007 |
| **T009** | *RF test predictions*: Predict on outer hold‑out folds; write `data/derived/rf_predictions.csv`. | [S] | T008 |
| **T010** | *Statistical comparison*: Perform three independent paired Wilcoxon signed‑rank tests (one per property) on absolute errors, apply Holm‑Bonferroni correction (α = 0.05), and additionally run a non‑parametric bootstrap test of the combined error reduction (1 000 resamples) to guard against heteroscedasticity. Produce `data/derived/statistical_report.md`. | [S] | T004, T009 |
| **T011** | *SHAP values*: Compute SHAP values for the trained RF; store per‑molecule JSON records under `data/derived/shap/*.json`. | [S] | T009 |
| **T012** | *SHAP interaction matrix*: Compute with `shap.TreeExplainer`; persist as `data/derived/shap_interaction.npy`. | [S] | T011 |
| **T013** | *SHAP interaction validation*: **Bootstrap‑of‑model** (200 resamples) to obtain a null distribution for each interaction; retain interactions where observed magnitude exceeds the 95th percentile. Output `data/derived/shap_interaction_validation.txt`. | [S] | T012 |
| **T014** | *Top‑K MACCS bits (selection‑set)*: Using **mean absolute SHAP interaction strength** computed **only on inner‑validation folds**, rank MACCS bits and select top K = 100. Save list `data/derived/top_k_maccs_selection.txt`. | [S] | T011 |
| **T014a** | *Top‑K MACCS bits (test‑set)*: Apply the same ranking on the outer‑fold **test‑set** to obtain `data/derived/top_k_maccs_test.txt` for downstream LNAI testing (ensures no leakage). | [S] | T009 |
| **T015** | *LNAI computation*: For each **pair among the top‑K bits** (≤ 4 950 pairs) **on the outer‑fold test data**, (i) regress out each bit’s main effect from `(RF_error − Baseline_error)`, (ii) compute rank‑biserial correlation with the joint‑presence indicator; apply prevalence filters (≥ 5 % marginal & joint); perform **2 000** permutations (Numba‑accelerated) to obtain a null distribution; apply Benjamini‑Hochberg FDR (α = 0.05); output `data/derived/lna_index.csv`. | [S] | T009, T014a |
| **T015b** | *Per‑molecule LNAI*: For each molecule, average the significant LNAI scores of all bit‑pairs it participates in; write `data/derived/lna_index_per_molecule.csv`. | [S] | T015 |
| **T015c** | *Power analysis*: Estimate detectable effect size for the LNAI test given N ≈ 5 000 and 4 950 tests; log warning if power < 0.8. | [S] | T015 |
| **T016** | *SMARTS mapping*: Translate selected MACCS bits to SMARTS via `reference/maccs_smart_lookup.json`; match against molecules; produce `data/derived/deviation_contexts.csv`. | [S] | T014a |
| **T017** | *Precision/Recall evaluation*: Compare mapped substructures to `reference/substructures.yaml`; compute precision ≥ 0.8 and recall ≥ 0.7; record metrics in `data/derived/mapping_metrics.txt`. | [S] | T016 |
| **T018** | *Test‑set split*: Record outer‑fold assignment per molecule; write `data/derived/test_set.csv`. | [S] | T008 |
| **T019a** | *RF residual plot*: Generate `data/derived/rf_residuals.png`. | [S] | T009 |
| **T019b** | *SHAP interaction heatmap*: Generate `data/derived/shap_interactions.png`. | [S] | T012 |
| **T020** | *Interaction‑Zone Report*: Compile significant LNAI bit‑pairs (FDR ≤ 0.05) with SMARTS descriptions into `data/derived/interaction_zone_report.pdf`. | [S] | T015, T016, T017 |
| **T021** | *Expert review*: Two independent chemists review `interaction_zone_report.pdf`; their acceptance statements compiled into `data/derived/validation_report.pdf`. | [S] | T020 |
| **T022** | *Validation audit*: Assemble checksums, data‑quality report, verification log, residual plots, LNAI tables, SHAP validation, mapping metrics, per‑molecule LNAI, expert review into `data/derived/validation_audit.pdf`. | [S] | T005, T009, T015, T013, T017, T021, T015b |
| **T023a** | *Schema‑compliant predictions*: Generate `data/derived/predictions_schema.csv` conforming to `prediction.schema.yaml`. | [S] | T009, T002 |
| **T023b** | *Schema‑compliant molecules*: Generate `data/derived/molecules_schema.csv` conforming to `molecule.schema.yaml`. | [S] | T002 |
| **T024** | *Orchestration*: `code/main.py` runs tasks T001‑T023 in order, logs timestamps, aborts if any step exceeds 5 h. | [S] | – |

### Functional Requirement Coverage
| FR | Mapped Phase / Task |
|----|----------------------|
| FR‑001 | T001 |
| FR‑002 | T002 |
| FR‑003 | T006 |
| FR‑004 | T008 |
| FR‑005 | T010 |
| FR‑006 | T011‑T013 |
| FR‑007 | T016 |
| FR‑008 | T002 (data‑quality report) |
| FR‑009 | T004 (baseline residuals) |
| FR‑010 | T020 |
| FR‑011 | T021 |
| FR‑012 | T015 (2 000 permutations) |
| FR‑013 | T014/T014a (split‑based top‑K selection) |
| FR‑014 | T019b |
| FR‑015 | T019a |
| **Additional** | T015b (per‑molecule LNAI) satisfies data‑model field; T023a/T023b satisfy prediction & molecule schemas. |

All functional requirements (FR‑001 – FR‑015) are explicitly addressed.

### Success Criteria Coverage
| SC | Evidence in Plan |
|----|-------------------|
| SC‑001 | T001 targets ≥ 5 000 experimental records; verification in `data_quality_report.csv`. |
| SC‑002 | T002 enforces missing_covariate_rate ≤ 0.05 and low_confidence_rate ≤ 0.05. |
| SC‑003 | T008/ T009 produce MAE ≤ 0.5, RMSE ≤ 0.7; metrics recorded in `statistical_report.md`. |
| SC‑004 | T010 conducts three property‑wise paired Wilcoxon tests with Holm‑Bonferroni, plus a bootstrap check, p ≤ 0.05. |
| SC‑005 | T020 produces Interaction‑Zone Report with ≥ 1 significant bit‑pair; T017 ensures precision ≥ 0.8, recall ≥ 0.7; T021 records positive expert review. |
| SC‑006 (new) | T015b provides per‑molecule LNAI, satisfying the data‑model field. |
| SC‑007 (new) | T023a/T023b generate schema‑compliant records, exercising both `prediction.schema.yaml` and `molecule.schema.yaml`. |

## Compute Feasibility
- **CPU‑first**: RandomForest (`n_estimators=300`, `max_depth=15`) fits < 2 GB RAM; SHAP TreeExplainer runs on CPU; permutation tests (2 000) and bootstrap (200) are **Numba‑JIT** accelerated, keeping total runtime ≤ 4 h.  
- **Memory**: Fingerprint matrices (~5 000 × 1 190 bits ≈ 0.7 MB) plus model objects comfortably < 7 GB RAM.  
- **No GPU needed**: All steps are CPU‑compatible; no escape hatch required.

## Risk Mitigation
- **Data‑source guard**: Only PubChem records with `property_type="Experimental"` are retained; computed estimates are excluded.  
- **Memory guard**: Fingerprint arrays stored as memory‑mapped `.npy`; lazy loading in modeling.  
- **Timeout guard**: Each script logs start/end timestamps; CI aborts if any step exceeds 5 h (fulfills NFR‑003).  
- **Statistical guard**: Power analysis (T015c) warns if LNAI test is under‑powered; bootstrap interaction validation avoids invalid permutation of targets.  

---



