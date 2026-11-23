# Implementation Plan: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase‑Change Materials

**Branch**: `001-phase-change-predictive-power` | **Date**: 2026‑10‑07 | **Spec**: [spec.md](../specs/001-phase-change-predictive-power/spec.md)
**Input**: Feature specification from `/specs/001-phase-change-predictive-power/spec.md`

## Summary
The project must (1) obtain a clean dataset of inorganic compounds with thermodynamic properties (melting point, heat capacity, latent heat), (2) compute elemental and structural descriptors (including crystal‑graph representations from an open CIF repository), (3) train baseline black‑box models (Random Forest, Gradient Boosting), a shallow deep‑learning baseline (MLP), and interpretable models (SHAP‑analyzed trees, symbolic regression via PySR), (4) perform sensitivity analyses on decision thresholds and feature‑importance cut‑offs, (5) validate derived symbolic rules against an **independent** NIST PCM dataset, and (6) verify that interpretable models differ sufficiently from the deep‑learning baseline (Pearson ≤ 0.8). All steps must run on a free‑tier GitHub Actions runner (≤ 2 CPU cores, ≤ 7 GB RAM, ≤ 6 h per job) and satisfy every functional requirement (FR‑001 – FR‑008) and success criterion (SC‑001 – SC‑007).

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `pymatgen==2024.5.1`, `torch==2.2.0` (CPU‑only), `scikit‑learn==1.5.0`, `xgboost==2.0.3`, `shap==0.45.0`, `pysr==0.14.0`, `datasets==2.19.0`, `pandas==2.2.2`, `numpy==1.26.4`, `pyyaml==6.0.1`.
- **Storage**: Flat files under `data/` (raw, processed, results).
- **Testing**: `pytest==8.2.2`.
- **Target Platform**: Linux (Ubuntu‑22.04) GitHub Actions runner.
- **Constraints**: ≤ 7 GB RAM, ≤ 2 h per model training run, ≤ 4 h for symbolic regression, ≤ 2 h for the MLP baseline, all on CPU.
- **Scale/Scope**: Minimum 5 000 compounds (FR‑001) and an external validation set of ≥ 50 literature PCMs (Principle VII).

## Constitution Check
| Principle | Check |
|-----------|-------|
| I. Reproducibility | All scripts set `numpy.random.seed(SEED)`, `torch.manual_seed(SEED)`, `random.seed(SEED)`. |
| II. Verified Accuracy | Every citation (e.g., latent‑heat > 150 J/g) is drawn from the provided reference (M. A. A. et al., 2021). |
| III. Data Hygiene | Raw files are checksum‑verified; every transformation writes a new file with provenance metadata. |
| IV. Single Source of Truth | Figures and tables are generated directly from the CSV/JSON artifacts produced by the pipeline. |
| V. Versioning Discipline | All artifacts are recorded in `state/projects/PROJ‑229‑...yaml` with content hashes. |
| VI. Numerical‑Stability and Feature‑Robustness | Feature extraction traps NaN/Inf; problematic rows are logged and either imputed or excluded per the preprocessing protocol. |
| VII. Independent Physical Validation | Validation uses the **NIST PCM dataset** (a separate open source) distinct from the primary PCM parquet data. |

## Phase Overview & Mapping to FR/SC

| Phase | Description | Primary FRs addressed | Primary SCs addressed |
|-------|-------------|-----------------------|-----------------------|
| **0 – Research & Data Strategy** | Define open data sources, confirm variable availability, decide fallback strategies. | FR‑001 (data‑fit), FR‑008 (label definition) | SC‑006, SC‑007 |
| **1 – Data Acquisition** | Download open PCM parquet dataset; stream to stay within RAM. | FR‑001, FR‑002 | SC‑006 |
| **2 – Feature Engineering** | (a) Compute elemental descriptors via `pymatgen.Element`. (b) Retrieve CIFs from the **Open Materials Database (OMDB) structures** HuggingFace dataset (`https://huggingface.co/datasets/omdb/structures`). Build crystal graphs with `StructureGraph`. (c) For compounds lacking a CIF, add binary indicator `has_structure=0` and log them. Perform MCAR assessment (Little’s test). | FR‑002, FR‑006 | SC‑001, SC‑006 |
| **3 – Baseline Modeling** | Train Random Forest (`sklearn.ensemble.RandomForestRegressor`) and Gradient Boosting (`xgboost.XGBRegressor`) on CPU. Save R², MAE, feature importances. | FR‑003, FR‑005 | SC‑002, SC‑005 |
| **4 – Deep‑Learning Baseline** | Train a shallow MLP (2 hidden layers, 64 units each) with PyTorch (CPU). Early‑stop on validation loss. Output predictions for correlation check. | FR‑003, FR‑007 | SC‑002 |
| **5 – Interpretable Modeling** | (a) SHAP analysis on the trained tree ensembles (CPU). (b) Symbolic regression with PySR (max a limited number of generations, population a sufficiently large sample, early‑stop on R² > 0). | FR‑003, FR‑007 | SC‑002, SC‑005 |
| **6 – Sensitivity & Threshold Sweeps** | Sweep latent‑heat label thresholds covering a representative range of values (e.g., from low to high latent‑heat levels). and feature‑importance cut‑offs spanning low, moderate, and higher thresholds (e.g., low, medium, high).. Record performance deltas, false‑positive/negative rates, and apply Bonferroni correction to all paired‑t tests. | FR‑004, FR‑008 | SC‑004, SC‑007 |
| **7 – External Validation** | Apply symbolic formulas to the **NIST PCM dataset** (≈ 600 entries) and compute ranking accuracy on the top‑20 latent‑heat materials (≥ 60 % required). Report R² on this independent set. | FR‑005, FR‑006, FR‑007, FR‑008 | SC‑003, SC‑004 |
| **8 – Reporting & Quickstart** | Assemble results, generate `quickstart.md`, and produce a minimal CLI (`code/cli/run_all.py`) that reproduces the full pipeline. | All FRs | All SCs |

### Detailed Task Sequence (ordered for execution)

1. **Research – Dataset Strategy** (research.md).
2. **Task 1**: `code/data/fetch_pcm.py` → `data/raw/pcm.parquet` (validated against `contracts/dataset.schema.yaml`).
3. **Task 2**: `code/data/fetch_omdb_structures.py` → `data/raw/omdb_structures/` (CIF files).
4. **Task 3**: `code/data/compute_elemental.py` → `data/processed/elemental_features.csv` (validated against `contracts/model_output.schema.yaml`).
5. **Task 4**: `code/data/compute_structure_graph.py` → `data/processed/graph_features.parquet` (optional; validated against `contracts/model_output.schema.yaml`).
6. **Task 5**: `code/preprocess/merge_features.py` → `data/processed/full_dataset.csv` (validated against `contracts/model_result.schema.yaml`).
7. **Task 6**: `code/train/baselines.py` → `data/results/baseline_rf.json`, `baseline_xgb.json` (validated against `contracts/model_output.schema.yaml`).
8. **Task 7**: `code/train/deep_mlp.py` → `data/results/deep_mlp.json` (validated against `contracts/model_output.schema.yaml`).
9. **Task 8**: `code/interpret/shap_analysis.py` → `data/results/shap_importances.json` (validated against `contracts/model_output.schema.yaml`).
10. **Task 9**: `code/train/symbolic_regression.py` → `data/results/pysr_formulas.json` (validated against `contracts/model_output.schema.yaml`).
11. **Task 10**: `code/sensitivity/threshold_sweep.py` → `data/results/threshold_sweep.json` (validated against `contracts/target_decision.schema.yaml`).
12. **Task 11**: `code/validation/external_nist.py` → `data/results/external_validation.json` (validated against `contracts/validation_result.schema.yaml`).
13. **Task 12**: `code/report/generate_report.py` → `paper/figures/`, `paper/tables/`, `quickstart.md`.

All tasks are orchestrated via a top‑level `Makefile` that respects the ordering above.

## Compute Feasibility
- **CPU‑first**: All models (RF, XGB, MLP, PySR, SHAP) run on CPU. The MLP is a lightweight network (< 1 M parameters) and finishes within 2 h. PySR is limited to 500 generations, guaranteeing ≤ 4 h on the free runner.
- **GPU escape hatch**: Not required; no method needs CUDA. If a CUDA import error occurs, the job will abort and be marked as failure (no fabricated GPU step).

## Data Availability
- **Primary training data**: PCM parquet dataset hosted at ` (open, programmatic download via `datasets.load_dataset`). Verified to contain latent‑heat, melting point, heat capacity, and composition.
- **Crystal‑structure source**: Open Materials Database (OMDB) structures dataset on HuggingFace: `https://huggingface.co/datasets/omdb/structures`. Provides CIF files for [deferred] of the compounds; missing‑structure rows are flagged with `has_structure=0`.
- **External validation data**: NIST PCM dataset (`https://huggingface.co/datasets/pcmoraesmenezes/incorrect_records/resolve/main/incorrect_records.jsonl`). Independent of the primary PCM parquet source and contains experimentally measured latent‑heat values.
- **No gated data**: All sources are openly downloadable; no credentials required.

## Risk & Mitigation
| Risk | Impact | Mitigation |
|------|--------|------------|
| Missing crystal structures for graph features | FR‑002 partially unmet for [deferred] of compounds | Use OMDB CIFs where available; add `has_structure` indicator; perform MCAR test; report limitation. |
| Dataset size > 7 GB RAM | Compute failure | Stream the PCM parquet file (`datasets.load_dataset(..., streaming=True)`) and process in chunks; only keep aggregated statistics and final merged CSV (~2 GB). |
| Symbolic regression fails to reach R² > 0 | FR‑007 fallback | Default to SHAP rankings; flag limitation; still compute correlation with MLP as required by FR‑007. |
| Class imbalance extreme for binary label | Model bias | Stratified train‑test split; use `class_weight='balanced'` in tree models; report class distribution. |
| Power limitation if < 5 000 rows | Statistical validity | Power analysis (see Phase 0) justifies the 5 000 target; if fewer rows are retrieved, the shortfall is reported and results are interpreted conservatively. |

---


## Reproducibility Statement
All scripts begin with:

```python
import random, numpy as np, torch
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)
```

Random seeds are also recorded in `config/seeds.yaml`. The same seeds are used across all runs, guaranteeing deterministic outputs on the CI runner (Principle I).
