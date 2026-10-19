# Implementation Plan: Molecular Property Prediction Pipeline

**Branch**: `324-molecular-property-prediction`  
**Date**: 2026-10-15  
**Spec**: `spec.md`  
**Input**: Feature specification from `/specs/324-molecular-property-prediction/spec.md`

## Summary
The pipeline will (1) download real molecular data from PubChem, (2) preprocess to retain high‑confidence experimental measurements, (3) generate Open Babel fingerprints (MACCS, ECFP4, FP2) via a CLI subprocess, (4) train a Random Forest model using **nested cross‑validation** (inner CV inside each outer fold), (5) compute property‑specific additive baselines (Crippen for logP, linear regression for solubility and boiling point), (6) perform a paired Wilcoxon signed‑rank test on absolute errors, (7) calculate SHAP interaction values, (8) map high‑importance **MACCS** bits back to SMARTS substructures (hashed bits from ECFP4/FP2 are reported as “uninterpretable”), (9) compute a **Local Non‑Additivity Index (LNAI)** for fingerprint bit‑pairs using point‑biserial correlation with Benjamini‑Hochberg FDR correction, (10) generate all required plots, tables, and a comprehensive validation audit. All steps are deterministic, reproducible, and respect the 2‑core, 7 GB CPU‑only runner limits.

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
| **I. Reproducibility** | ✅ | Fixed `requirements.txt`; all random seeds pinned (`np.random.seed(42)`, `RandomState(42)`); deterministic Open Babel calls (`--gen3d` disabled). |
| **II. Verified Accuracy** | ✅ | Added verification step T011.6 that runs the Reference‑Validator on every external URL and stores `verification_log.txt`. |
| **III. Data Hygiene** | ✅ | Raw files immutable; SHA‑256 checksums stored in `state/artifact_hashes.yaml`; every transformation writes a new file with documented derivation. |
| **IV. Single Source of Truth** | ✅ | Every figure/table generated directly from files under `data/derived/`. |
| **V. Versioning Discipline** | ✅ | Content hashes recorded in `state/projects/…yaml`; `updated_at` timestamps updated on every artifact change. |
| **VI. Non‑Additivity Interaction Mapping** | ✅ | Baseline vs. RF residuals compared; SHAP interaction bits (MACCS only) mapped to SMARTS; LNAI quantifies “interaction zones” with proper statistical correction. |
| **VII. Computational Efficiency** | ✅ | CPU‑first implementation; nested CV respects memory limits; runtime ≤ 4 h (estimated). |

## Project Structure
```text
projects/PROJ-324-predicting-molecular-properties-from-ope/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── download.py          # PubChem download & checksum
│   │   ├── preprocess.py        # Missing‑value handling, quality report
│   │   └── fingerprint.py       # Open Babel wrapper
│   ├── models/
│   │   ├── baseline.py          # Property‑specific additive baselines
│   │   └── rf.py                # Random Forest with nested CV
│   ├── analysis/
│   │   ├── stats.py             # Metrics, Wilcoxon test, LNAI
│   │   └── explainability.py    # SHAP, interaction heatmap, SMARTS mapping, conformational audit
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
| **T010.1** | *MaxMin diverse sampling*: Compute pairwise Euclidean distance on normalized physicochemical descriptors; iteratively **select the candidate with the maximum of the minimum distances** to the current set; **stop when this maximum value `< 0.7`**. | [S] | – |
| **T011.5** | *Data integrity & checksum*: Generate SHA‑256 checksums for every file in `data/raw/`; write `state/artifact_hashes.yaml`. | [S] | T010.1 |
| **T011.6** | *Reference‑Validator verification*: Run Reference‑Validator on all external URLs used (PubChem API, Open Babel site); store `verification_log.txt` under `data/derived/`. | [S] | T011.5 |
| **T014a** | *Baseline implementation (Crippen for logP)*: Compute Crippen fragments via RDKit. | [S] | T011.5 |
| **T014b** | *Baseline implementation (Linear regression for solubility & boiling point)*: Fit simple linear models on molecular weight & polar surface area. | [S] | T011.5 |
| **T014c** | *Baseline output*: Write `data/derived/baseline_predictions.csv` containing property‑specific additive predictions. | [S] | T014a, T014b |
| **T014.5** | *Baseline residuals & plot*: Calculate absolute errors, MAE, RMSE; generate `data/derived/baseline_residuals.png`. | [S] | T014c |
| **T019** | *Fingerprint generation*: Wrapper around `obabel` to produce MACCS, ECFP4, FP2 arrays. | [S] | T011.5 |
| **T019.1** | *Fingerprint storage*: Save arrays as `data/processed/*.npy`. | [S] | T019 |
| **T020** | *Nested cross‑validation*: For each **outer** 5‑fold split, run an **inner** 5‑fold CV **inside that outer training partition** to tune `max_features` and `min_samples_leaf`. No data from the outer hold‑out set is used in inner tuning. | [S] | T019.1 |
| **T020.1** | *RF test predictions*: Using the best hyper‑parameters from the inner CV, predict on the outer‑fold hold‑out set; write `data/derived/rf_predictions.csv`. | [S] | T020 |
| **T021.1** | *Wilcoxon signed‑rank test*: Paired test on absolute errors of RF vs. baseline for each property; Bonferroni‑corrected for three properties; produce `data/derived/statistical_report.md`. | [S] | T014.5, T020.1 |
| **T027** | *SHAP interaction heatmap*: Compute SHAP interaction values with `shap.TreeExplainer`; generate `data/derived/shap_interactions.png`. | [S] | T020.1 |
| **T027.1** | *Persist SHAP interaction matrix*: Save the full interaction matrix as `data/derived/shap_interaction.npy`. | [S] | T027 |
| **T028** | *Prediction records*: For each molecule/property write a JSON record conforming to `prediction.schema.yaml` into `data/derived/predictions/`. | [S] | T020.1 |
| **T029** | *Map SHAP bits → substructures (MACCS only)*: Translate high‑importance MACCS bits into SMARTS patterns via `code/data/rules.py`; write `data/derived/deviation_contexts.csv`. Hashed bits from ECFP4/FP2 are reported as “uninterpretable”. | [S] | T027 |
| **T030.2** | *Local Non‑Additivity Index (LNAI)*: For every fingerprint bit‑pair (i, j), compute the **point‑biserial correlation** between `(RF_error − Baseline_error)` and the binary presence of both bits; apply **Benjamini‑Hochberg FDR correction** (α = 0.05) and retain pairs with FDR < 0.05; output `data/derived/lna_index.csv`. | [S] | T020.1 |
| **T033** | *Conformational‑limitations audit*: Flag molecules with > 10 rotatable bonds (computed with RDKit); write `data/derived/conformational_limitations.csv`. | [S] | T011.5 |
| **T057** | *Comprehensive validation audit*: Collate checksum report, data‑quality report, baseline & RF residuals, LNAI, SHAP heatmap, conformational audit, and verification log into `data/derived/validation_audit.pdf`. | [S] | T014.5, T020.1, T027, T030.2, T033, T011.6 |
| **T058** | *Experimental validation protocol*: Draft `data/derived/experimental_validation_protocol.md` describing how future wet‑lab measurements would validate the top‑ranked interaction zones. | [S] | T030.2, T029 |

### Functional Requirement Coverage
| FR | Mapped Phase / Task |
|----|----------------------|
| FR‑001 | T010.1 → T011.5 (download & checksum) |
| FR‑002 | T011.5 (preprocess & missing‑value handling in `preprocess.py`) |
| FR‑003 | T019 (Open Babel CLI fingerprint generation) |
| FR‑004 | T020 (nested CV) + T020.1 (RF training) |
| FR‑005 | T021.1 (Wilcoxon signed‑rank test) |
| FR‑006 | T027 (SHAP interaction values) |
| FR‑007 | T029 (bit‑to‑substructure mapping, MACCS only) |
| FR‑008 | T011.5 (data‑quality metrics log) |

All FRs are explicitly addressed.

## Compute Feasibility
- **CPU‑first**: RandomForest (`n_estimators=300`, `max_depth=15`) fits < 2 GB RAM; SHAP TreeExplainer runs on CPU.  
- **Memory**: Fingerprint matrices of a few thousand by a few thousand bits (≈ 1 MB) plus model objects comfortably fit within 7 GB RAM.  
- **No GPU Needed**: The pipeline does not invoke CUDA; therefore no escape hatch is required.

## Risk Mitigation
- **Experimental‑data guard**: Only experimental measurements are used for training; computed values are excluded from model fitting but retained for optional consistency reporting.  
- **Memory guard**: Fingerprint arrays are saved as memory‑mapped NumPy files; `rf.py` loads them lazily.  
- **Timeout guard**: Each script logs start/end timestamps; CI aborts > 5 h with a clear error (fulfills NFR‑003).  

---
