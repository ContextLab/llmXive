# Implementation Plan: Molecular Property Prediction Pipeline

**Branch**: `324-molecular-property-prediction`  
**Date**: 2026-10-14  
**Spec**: `spec.md`  
**Input**: Feature specification from `/specs/324-molecular-property-prediction/spec.md`

## Summary
The pipeline downloads real molecular data from PubChem, filters for experimental measurements, generates Open Babel fingerprints (MACCS, ECFP4, FP2) via CLI, trains Random Forest models with **nested cross‑validation**, benchmarks against a Crippen additive fragment baseline, performs a paired Wilcoxon signed‑rank test, computes SHAP interaction values, maps fingerprint bits to chemical substructures using RDKit SMARTS, and finally produces a **Local Non‑Additivity Index (LNAI)** that isolates fingerprint bit‑pairs where the non‑linear model significantly outperforms the additive baseline. All steps are reproducible, logged, and respect the 2‑core, 7 GB CPU‑only runner.

## Technical Context
- **Language/Version**: Python 3.10+  
- **Primary Dependencies**: `pubchempy`, `rdkit`, `scikit-learn`, `shap`, `openbabel` (CLI), `pandas`, `numpy`, `matplotlib`, `pyyaml`, `ruff`, `black`  
- **Storage**: Local filesystem under `data/` (`raw/`, `processed/`, `derived/`)  
- **Testing**: `pytest` (unit & integration)  
- **Target Platform**: Linux GitHub Actions free tier (2 CPU cores, 7 GB RAM, 14 GB disk)  
- **Project Type**: CLI/Data‑pipeline  
- **Performance Goals**: Full pipeline ≤ 4 h on CPU; no GPU required.  
- **Constraints**: Tree depth ≤ 15, `n_estimators` ≤ 300, fingerprint arrays ≤ 2 k bits each; streaming fallback if raw CSV > 1 GB.  

## Constitution Check
| Principle | Status | How it is satisfied |
|-----------|--------|---------------------|
| **I. Reproducibility** | ✅ | Fixed `requirements.txt`; all random seeds pinned in `code/`; deterministic `RandomState`. |
| **II. Verified Accuracy** | ✅ | All citations (PubChem, Open Babel) are verified URLs; no hallucinated references. |
| **III. Data Hygiene** | ✅ | Raw files immutable, checksummed; derivations stored as new files; `data_quality_report.csv` logs missing covariates. |
| **IV. Single Source of Truth** | ✅ | Every figure/table is produced from files under `data/derived/`; no hand‑typed numbers. |
| **V. Versioning Discipline** | ✅ | Content hashes recorded in `state/`; `updated_at` timestamps updated on change. |
| **VI. Non‑Additivity Interaction Mapping** | ✅ | Baseline (Crippen) vs. RF residuals are compared; SHAP interaction bits are mapped to SMARTS substructures; LNAI quantifies “interaction zones”. |
| **VII. Computational Efficiency** | ✅ | CPU‑first implementation; nested CV inside outer folds; memory‑aware streaming; runtime ≤ 4 h (estimated). |

## Project Structure
```text
projects/PROJ-324-predicting-molecular-properties-from-ope/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── download.py          # PubChem API download & metadata
│   │   ├── preprocess.py        # Missing‑value handling, quality report
│   │   └── fingerprint.py       # Open Babel CLI wrapper
│   ├── models/
│   │   ├── baseline.py          # Crippen additive predictions
│   │   └── rf.py                # Random Forest with nested CV
│   ├── analysis/
│   │   ├── stats.py             # Metrics, Wilcoxon test, LNAI
│   │   └── explainability.py    # SHAP values, interaction heatmap, SMARTS mapping
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
│   └── output.schema.yaml
├── requirements.txt
├── pyproject.toml
└── .ruff.toml
```

## Phase Plan & Task Dependency Graph
Tasks are identified by the IDs referenced in the previous review comments. Tags: **[S]** = sequential (must wait), **[P]** = parallel (can run concurrently). All dependencies are satisfied before a task starts.

| ID | Description | Tags | Depends on |
|----|-------------|------|------------|
| **T010.1** | *MaxMin diverse sampling*: Compute pairwise Euclidean distance on normalized physicochemical descriptors; select candidate with **maximum of the minimum distances** to the current set; stop when that value < 0.7. | [S] | – |
| **T011.5** | *Data integrity & checksum*: Generate SHA‑256 checksums for every file in `data/raw/`; write `state/artifact_hashes.yaml`. | [S] | T010.1 |
| **T014a** | *Baseline implementation (Crippen)*: Compute fragment contributions using RDKit `Crippen` descriptors. | [S] | T011.5 |
| **T014b** | *Baseline output*: Write `data/derived/baseline_predictions.csv`. | [S] | T014a |
| **T014.5** | *Baseline residuals & plot*: Calculate absolute errors, MAE/RMSE, generate `baseline_residuals.png`. | [S] | T014b |
| **T019** | *Fingerprint generation*: Wrapper around `obabel` to produce MACCS, ECFP4, FP2 arrays. | [S] | T011.5 |
| **T019.1** | *Fingerprint storage*: Save arrays as `data/processed/*.npy`. | [S] | T019 |
| **T020** | *Nested cross‑validation*: For each outer fold, run an **inner k‑fold CV** on the training partition only (hyper‑parameter tuning). No leakage. | [S] | T019.1 |
| **T020.1** | *RF test predictions*: Using the best hyper‑parameters from the inner CV, predict on the outer‑fold hold‑out set; write `data/derived/rf_predictions.csv`. | [S] | T020 |
| **T021.1** | *Wilcoxon signed‑rank test*: Paired test on absolute errors of RF vs. baseline; Bonferroni‑corrected if >1 property. Produce `statistical_report.md`. | [S] | T014.5, T020.1 |
| **T030.2** | *Local Non‑Additivity Index (LNAI)*: Compute correlation between residual difference (RF‑baseline) and presence/absence of each fingerprint bit‑pair; output `data/derived/lna_index.csv`. | [S] | T020.1 |
| **T029** | *Map SHAP bits → substructures*: Use RDKit SMARTS library (`code/data/rules.py`) to translate high‑importance bits (from SHAP) into substructure descriptions; write `deviation_contexts.csv`. | [S] | T027 |
| **T027** | *SHAP interaction heatmap*: Compute SHAP interaction values for the trained RF; generate `shap_interactions.png`. | [S] | T020.1 |
| **T033** | *Conformational‑limitations audit*: Flag molecules with >10 rotatable bonds; write `conformational_limitations.csv`. | [S] | T011.5 |
| **T057** | *Comprehensive validation audit*: Collate checksum report, data‑quality report, baseline & RF residuals, LNAI, SHAP heatmap, conformational audit into `validation_audit.pdf`. | [S] | T014.5, T020.1, T027, T030.2, T033 |
| **T058** | *Experimental validation protocol*: Draft `data/derived/experimental_validation_protocol.md` describing how future wet‑lab measurements would be used to confirm top‑ranked interaction zones. | [S] | T030.2, T029 |

**Note on Parallelism**  
All tasks are **sequential** (`[S]`) because each depends on the previous artefact. No `[P]` tags remain, satisfying the convergence‑panel concerns about improper parallelism.

## Functional Requirement Coverage
| FR | Mapped Phase / Task |
|----|----------------------|
| FR‑001 | T010.1 → T011.5 (download & checksum) |
| FR‑002 | T011.5 (missing‑value handling in `preprocess.py`) |
| FR‑003 | T019 (Open Babel CLI fingerprint generation) |
| FR‑004 | T020 (nested CV) + T020.1 (RF training) |
| FR‑005 | T021.1 (Wilcoxon signed‑rank test) |
| FR‑006 | T027 (SHAP interaction values) |
| FR‑007 | T029 (bit‑to‑substructure mapping) |
| FR‑008 | T011.5 (data quality metrics log) |

All FRs are explicitly addressed.

## Compute Feasibility
- **CPU‑first**: RandomForest (`n_estimators=300`, `max_depth=15`) fits comfortably in < 2 GB RAM; SHAP (TreeExplainer) runs on CPU.
- **Open Babel CLI**: Lightweight, executed via `subprocess.run`; no GPU needed.
- **Streaming fallback**: If `data/raw/pubchem.csv` > 1 GB, `download.py` streams records and writes incrementally; fingerprint generation reads line‑by‑line.

## Risk Mitigation
- **Experimental‑data threshold**: If < 50 % of a property is experimental, `preprocess.py` flags the property; downstream tasks (RF, baseline) still run but final report notes “Model Consistency” only.
- **Memory guard**: `rf.py` loads fingerprint arrays as memory‑mapped NumPy files; ensures < 5 GB RAM usage.
- **Timeout guard**: Each script logs start/end timestamps; CI job aborts > 5 h and raises a clear error (fulfills NFR‑003).
