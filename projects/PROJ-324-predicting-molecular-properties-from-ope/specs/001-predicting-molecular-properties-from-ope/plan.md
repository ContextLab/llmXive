# Implementation Plan: Molecular Property Prediction Pipeline

**Branch**: `324-molecular-property-prediction`  
**Date**: 2026-10-23  
**Spec**: `spec.md`  
**Input**: Feature specification from `/specs/324-molecular-property-prediction/spec.md`

## Summary
The pipeline will (1) download real molecular data from PubChem (experimental records only) via a verified `PubChemPy` recipe, (2) preprocess to filter missing values, enforce experimental‑only records, and generate a data‑quality report, (3) generate Open Babel fingerprints (MACCS, ECFP4, FP2) via a deterministic CLI wrapper, (4) compute property‑specific additive baselines, (5) train a Random Forest model with nested cross‑validation, (6) perform a paired Wilcoxon signed‑rank test on absolute errors (Bonferroni‑corrected for three properties), (7) compute SHAP values and SHAP interaction matrices, (8) validate SHAP interactions with a permutation test, (9) select the top‑K (K=50) MACCS bits by mean absolute SHAP, (10) compute a Local Non‑Additivity Index (LNAI) **only for the selected top‑K bits** (≤1,225 pairwise tests) using **rank‑biserial correlation** between `(RF_error − Baseline_error)` and the joint presence of the two bits, applying a **prevalence filter** (bits must appear in ≥5 % of molecules) and Benjamini‑Hochberg FDR (α = 0.05), (11) map the most important MACCS bits to SMARTS substructures, (12) generate all required plots and CSV tables, (13) produce a lightweight validation summary CSV, and (14) create a test‑set split file. All steps are deterministic, reproducible, and respect the appropriate core and 7 GB runner limits.

## Technical Context
- **Language/Version**: Python 3.10+  
- **Primary Dependencies**: `pubchempy`, `rdkit`, `scikit-learn`, `shap`, `openbabel` (CLI), `pandas`, `numpy`, `matplotlib`, `pyyaml`, `ruff`, `black`  
- **Storage**: Files under `data/` (`raw/`, `processed/`, `derived/`)  
- **Testing**: `pytest` (unit & integration)  
- **Target Platform**: Linux GitHub Actions free tier (2 CPU cores, 7 GB RAM, 14 GB disk)  
- **Performance Goals**: Full end‑to‑end execution ≤ 4 h on CPU; no GPU required.  
- **Constraints**: `max_depth ≤ 15`, `n_estimators ≤ 300`, fingerprint arrays ≤ 2 200 bits each; streaming fallback if raw CSV > 1 GB.  

## Constitution Check

| Principle | Satisfied? | How Satisfied |
|-----------|------------|----------------|
| **I. Reproducibility** | ✅ | Fixed `requirements.txt`; all random seeds pinned (e.g., `np.random.seed(<fixed_seed>)`, `RandomState(<fixed_seed>)`). Open Babel called with deterministic flags. |
| **II. Verified Accuracy** | ✅ | External URLs (PubChem API, Open Babel site) verified via Reference‑Validator; results stored in `data/derived/verification_log.txt`. |
| **III. Data Hygiene** | ✅ | Raw files immutable; SHA‑2 family checksums recorded in `state/artifact_hashes.yaml`. All transformations write new files with documented derivation suffixes. |
| **IV. Single Source of Truth** | ✅ | All figures/tables generated directly from files under `data/derived/`. |
| **V. Versioning Discipline** | ✅ | Content hashes recorded in `state/projects/…yaml`; `updated_at` timestamps updated on every artifact change. |
| **VI. Non‑Additivity Interaction Mapping** | ✅ | Baseline vs. RF residuals compared; SHAP importance used to select top‑K MACCS bits; LNAI computed on those bit‑pairs; MACCS bits mapped to SMARTS; results stored in `data/derived/deviation_contexts.csv`. |
| **VII. Computational Efficiency** | ✅ | CPU‑first implementation; nested CV respects memory limits; top‑K pre‑selection limits LNAI pairwise tests to ≤1,225, guaranteeing runtime ≤ 4 h (estimated). |

## Project Structure
```text
projects/PROJ-324-predicting-molecular-properties-from-ope/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── download.py          # PubChem download & checksum
│   │   ├── preprocess.py        # Missing‑value handling, quality report, experimental‑only filter
│   │   └── fingerprint.py       # Open Babel wrapper
│   ├── models/
│   │   ├── baseline.py          # Property‑specific additive baselines
│   │   └── rf.py                # Random Forest with nested CV
│   ├── analysis/
│   │   ├── stats.py             # Metrics, Wilcoxon test, LNAI, verification log
│   │   └── explainability.py    # SHAP, interaction validation, MACCS‑SMARTS mapping, test‑set export
│   └── main.py                  # Orchestration script
├── data/
│   ├── raw/
│   ├── processed/
│   └── derived/
├── tests/
│   ├── unit/
│   └── integration/
├── contracts/
│   ├── dataset.schema.yaml
│   ├── fingerprint.schema.yaml
│   ├── interaction_context.schema.yaml
│   ├── molecule.schema.yaml
│   ├── output.schema.yaml
│   └── prediction.schema.yaml
├── requirements.txt
├── pyproject.toml
└── .ruff.toml
```

## Phase Plan & Task Dependency Graph
All tasks are **sequential** (`[S]`). No parallel tags are used where a dependency exists.

| ID | Description | Tags | Depends on |
|----|-------------|------|------------|
| **T001** | *Data download*: Retrieve experimental SMILES + properties from PubChem, write `data/raw/pubchem.csv`. | [S] | – |
| **T002** | *Preprocess & quality*: Filter to `property_type="Experimental"`, handle missing values, generate `data/derived/data_quality_report.csv`. | [S] | T001 |
| **T003** | *Verification log*: Run Reference‑Validator on external URLs, store `data/derived/verification_log.txt`. | [S] | T001 |
| **T004** | *Baseline computation*: Crippen fragments for logP; linear regressions for solubility & boiling point. | [S] | T002 |
| **T005** | *Baseline residual plot*: Compute MAE/RMSE, generate `data/derived/baseline_residuals.png`. | [S] | T004 |
| **T006** | *Fingerprint generation*: Wrapper around `obabel` to produce MACCS, ECFP4, FP2 arrays. | [S] | T002 |
| **T007** | *Fingerprint storage*: Save arrays as `data/processed/*.npy`. | [S] | T006 |
| **T008** | *Nested cross‑validation*: Outer 5‑fold CV; inner 5‑fold CV tunes `max_features` & `min_samples_leaf`. | [S] | T007 |
| **T009** | *RF test predictions*: Predict on outer hold‑out folds, write `data/derived/rf_predictions.csv`. | [S] | T008 |
| **T010** | *Statistical comparison*: Paired Wilcoxon signed‑rank test on absolute errors (RF vs. baseline) for each property, Bonferroni‑corrected, produce `data/derived/statistical_report.md`. | [S] | T004, T009 |
| **T011** | *SHAP values*: Compute SHAP values for the trained RF, save per‑molecule JSON records (`data/derived/predictions/*.json`). | [S] | T009 |
| **T012** | *SHAP interaction matrix*: Compute with `shap.TreeExplainer`, persist as `data/derived/shap_interaction.npy`. | [S] | T011 |
| **T013** | *SHAP interaction validation*: Permutation test (100 shuffles) to assess stability of interaction values; generate `data/derived/shap_interaction_validation.txt`. | [S] | T012 |
| **T014** | *Top‑K MACCS bits*: Rank MACCS bits by mean absolute SHAP, select top K = 50, save list `data/derived/top_k_maccs.txt`. | [S] | T011 |
| **T015** | *LNAI computation*: For each **pair among the top‑K bits** (≤1,225 pairs), compute **rank‑biserial correlation** between `(RF_error − Baseline_error)` and the **joint presence** of the two bits, applying a **prevalence filter** (bits must appear in ≥5 % of molecules) and Benjamini‑Hochberg FDR (α = 0.05). Output `data/derived/lna_index.csv`. | [S] | T009, T014 |
| **T016** | *MACCS‑SMARTS mapping*: Translate top‑K MACCS bits to SMARTS using `maccs_smart_lookup.json`; produce `data/derived/deviation_contexts.csv`. | [S] | T014 |
| **T017a** | *Test‑set split*: Record outer‑fold assignment per molecule, write `data/derived/test_set.csv`. | [S] | T008 |
| **T017b** | *Visual artifacts*: Generate `rf_residuals.png`, `shap_interactions.png`, and any other plots. | [S] | T009, T012, T015 |
| **T018** | *Validation summary*: Collate checksum info, data‑quality report, verification log, baseline & RF residuals, LNAI table, SHAP validation summary, test‑set info into `data/derived/validation_summary.csv`. | [S] | T005, T009, T015, T013, T003, T002, T017a |
| **T019** | *Orchestration*: `code/main.py` runs tasks T001‑T018 in order. | [S] | – |

### Functional Requirement Coverage
| FR | Mapped Phase / Task |
|----|----------------------|
| FR‑001 | T001 (download) |
| FR‑002 | T002 (preprocess & quality) |
| FR‑003 | T006 (Open Babel fingerprint generation) |
| FR‑004 | T008 (nested CV RF) |
| FR‑005 | T010 (Wilcoxon signed‑rank test) |
| FR‑006 | T011‑T013 (SHAP values, interaction matrix, validation) |
| FR‑007 | T016 (MACCS‑SMARTS mapping) |
| FR‑008 | T002 (data‑quality report) |

All FRs are explicitly addressed.

## Compute Feasibility
- **CPU‑first**: RandomForest (`n_estimators=300`, `max_depth=15`) fits < 2 GB RAM; SHAP TreeExplainer runs on CPU.  
- **Memory**: Fingerprint matrices (~5 000 × 2 200 bits ≈ 1.4 MB) plus model objects comfortably within 7 GB RAM.  
- **No GPU Needed**: The pipeline does not invoke CUDA; therefore no escape hatch is required.

## Risk Mitigation
- **Data‑source guard**: Only PubChem records flagged as `property_type="Experimental"` are used; computed values are excluded.  
- **Memory guard**: Fingerprint arrays saved as memory‑mapped NumPy files; `rf.py` loads lazily.  
- **Timeout guard**: Each script logs timestamps; CI aborts > 5 h with a clear error (fulfills NFR‑003).  

---

