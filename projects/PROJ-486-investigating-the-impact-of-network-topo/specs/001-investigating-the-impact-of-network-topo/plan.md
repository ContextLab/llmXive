# Implementation Plan: Investigating the Impact of Network Topology on Neural Entrainment to Rhythmic Stimuli

**Branch**: `001-network-topology-entrainment` | **Date**: 2026-06-28 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-investigating-the-impact-of-network-topo/spec.md`

## Summary

This feature implements a computational pipeline to investigate the correlation between resting-state network topology (Clustering Coefficient, Characteristic Path Length) and neural entrainment strength. The project distinguishes between **Validation Mode** (unit test with simulated r=0.5 to verify pipeline logic) and **Scientific Analysis Mode** (testing the Null Hypothesis r=0 or using real data). 

The primary scientific execution path attempts to acquire real HCP S1200 data (FR-001). If real matched data is unavailable or the inner join yields N < 30, the system triggers a **Simulated Data Fallback** (FR-009) specifically configured for **Null Hypothesis Testing** (r=0) to verify Type I error control, or for **Power Analysis** (r=0.5) strictly as a unit test. The pipeline computes graph metrics, performs Multiple Linear Regression (MLR) with Holm-Bonferroni correction, handles collinearity via **Orthogonalization** (residualization) if VIF > 5 (instead of suppressing p-values), and conducts robustness checks using alternative parcellations (AAL, Power 264).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `networkx`, `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `matplotlib`, `seaborn`, `requests`, `hashlib`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/visualizations`)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner)  
**Project Type**: Computational Science / Data Analysis Pipeline  
**Performance Goals**: Complete full pipeline (N=50, 200x200 matrices) within 6 hours on 2-core/7GB RAM.  
**Constraints**: CPU-first execution; no local GPU; strict memory limits; simulation fallback is mandatory if real matched data is missing or N < 30.  
**Scale/Scope**: N=50 subjects (simulated or real subset); 3 atlas types (Schaefer, AAL, Power 264).

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Reference / Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/simulation.py` and `code/analysis.py`. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | All citations (HCP S1200, AAL, Power) verified against primary sources. The 'Verified Datasets' table has been removed to avoid referencing unusable URLs; the fallback path is explicitly verified as the correct execution mode. |
| **III. Data Hygiene** | **PASS** | `data/raw` immutable; `data/processed` derived with checksums recorded in `state/...yaml`. |
| **IV. Single Source of Truth** | **PASS** | All figures/statistics generated from `data/processed/*.csv` by `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | **Phase 4** explicitly updates `state/...yaml` with content hashes (using `hashlib`) and `updated_at` timestamps for all artifacts. |
| **VI. Statistical Rigor** | **PASS** | Holm-Bonferroni correction implemented; **Orthogonalization** used for VIF > 5 (not suppression); effect sizes (r) always reported; p < 0.05 threshold enforced. |
| **VII. Multimodal Alignment** | **PASS** | Inner join on `subject_id` enforced; sensitivity analysis (AAL/Power) implemented; CLI argument `--atlas` added for user specification. |

## Project Phases & Task Ordering

**Phase 0: Data Acquisition & Validation (FR-001, FR-007, FR-008)**
- **Task T01**: Attempt to download HCP S1200 resting-state fMRI data (Schaefer parcellation) using `requests` or `hcp-downloader`. 
  - **Logic**: Handle DUA/auth errors gracefully. If auth fails, log "Real data access denied" and proceed to fallback check.
  - **Output**: `data/raw/connectivity_matrices/` (if successful) or empty directory.
- **Task T02**: Validate input `entrainment_metrics.csv` (if provided). 
  - **Function**: `load_entrainment_csv()` in `code/data_loader.py`.
  - **Check**: Columns `subject_id`, `entrainment_metric` exist. 
  - **Check**: `entrainment_metric` is numeric.
  - **Action**: If validation fails (e.g., non-numeric), **HALT** with error "Invalid Entrainment Data" (FR-008, SC-005).
  - **Action**: If file missing, return `{"exists": false, "reason": "missing"}` and proceed to fallback.
- **Task T03**: Validate topology metrics (if generated/simulated). 
  - **Check**: Zero variance detection across the sample.
  - **Action**: If zero variance detected, flag as "Non-informative" and write to `data/processed/metric_flags.json` (FR-007).

**Phase 1: Data Preparation & Fallback Logic (FR-003, FR-009)**
- **Task T04**: Perform inner join on `subject_id` between topology and entrainment data.
  - **Function**: `join_and_check_n()` in `code/data_loader.py`.
  - **Output**: `data/processed/joined_data.csv` (if N >= 30) or trigger fallback.
- **Task T05**: Count N.
  - **If N < 30**: Trigger **Simulated Data Fallback**.
    - **Mode A (Scientific)**: Generate data with **r=0** (Null Hypothesis) to test Type I error.
    - **Mode B (Unit Test)**: Generate data with **r=0.5** (Validation) to verify pipeline detection. *Explicitly labeled "Unit Test"*.
  - **If N >= 30**: Proceed with real data.
- **Task T06**: Write `data/processed/joined_data.csv` and `data/processed/metadata.json` (including `data_source`: "Real" or "Simulated").

**Phase 2: Analysis (FR-004, FR-002, FR-006)**
- **Task T07**: Compute Clustering Coefficient and Characteristic Path Length for all subjects/atlas types.
  - **Logic**: Check for zero variance; if found, set `is_zero_variance = True` and write to `data/processed/metric_flags.json`.
- **Task T08**: Fit MLR: `Entrainment ~ CC + CPL`.
  - **Logic**: Read `metric_flags.json` to skip or flag non-informative metrics.
- **Task T09**: Calculate VIF.
  - **If VIF > 5**: Perform **Orthogonalization** (residualize CC on CPL, or vice versa) to estimate unique effects. Report standardized betas for residuals and joint R-squared. **Do not suppress p-values**; report them for the orthogonalized model.
  - **If VIF <= 5**: Report standardized betas and p-values directly.
- **Task T10**: Apply Holm-Bonferroni correction to p-values.
- **Task T11**: Generate `data/processed/correlation_results.csv` (schema: `correlation_results.schema.yaml`).
- **Task T12**: If `--atlas` argument provided (AAL/Power), repeat T07-T11 for sensitivity analysis.
  - **CLI**: `python code/main.py --atlas AAL` (FR-006).

**Phase 3: Visualization & Reporting (FR-005, FR-010, SC-002)**
- **Task T13**: Generate `data/visualizations/scatter_topology_entrainment.png` (95% CI).
- **Task T14**: Generate `data/visualizations/sensitivity_bar_chart.png` (Absolute difference for AAL and Power vs Schaefer).
- **Task T15**: Generate summary report `docs/report.md` with R-squared, coefficients, adjusted p-values, and effect sizes (r).

**Phase 4: Versioning & Cleanup (Principle V)**
- **Task T16**: Compute content hashes for all `data/processed/` and `data/visualizations/` files using `hashlib.sha256`.
- **Task T17**: Update `state/projects/PROJ-486-investigating-the-impact-of-network-topo.yaml` with `artifact_hashes` and `updated_at` timestamp.

## Project Structure

### Documentation (this feature)

```text
specs/001-network-topology-entrainment/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── topology_metrics.schema.yaml
    ├── correlation_results.schema.yaml
    ├── dataset.schema.yaml
    ├── output.schema.yaml
    └── sensitivity.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-486-investigating-the-impact-of-network-topo/
├── code/
│   ├── __init__.py
│   ├── data_loader.py       # Loads HCP (real/sim), validates entrainment CSV, handles fallback
│   ├── graph_metrics.py     # Computes CC, CPL, VIF, zero-variance flags, orthogonalization
│   ├── simulation.py        # Generates synthetic data (Null r=0 or Validation r=0.5)
│   ├── analysis.py          # MLR, Holm-Bonferroni, VIF, Orthogonalization
│   ├── viz.py               # Scatter plots, Bar charts for sensitivity
│   └── main.py              # Orchestration script (writes CSVs, updates state, generates viz)
├── data/
│   ├── raw/
│   │   ├── connectivity_matrices/ # (If real) or generated by simulation
│   │   └── entrainment_metrics.csv # (If real) or generated by simulation
│   ├── processed/
│   │   ├── joined_data.csv
│   │   ├── joined_data_simulated.csv
│   │   ├── metric_flags.json
│   │   ├── correlation_results.csv
│   │   ├── sensitivity_results.csv
│   │   └── metadata.json
│   └── visualizations/
│       ├── scatter_topology_entrainment.png
│       └── sensitivity_bar_chart.png
├── tests/
│   ├── unit/
│   │   ├── test_simulation.py       # Tests r=0 and r=0.5 generation
│   │   ├── test_graph_metrics.py
│   │   ├── test_analysis.py         # Tests VIF, Holm-Bonferroni, Orthogonalization
│   │   └── test_validation.py       # Tests "Invalid Entrainment Data" error path (SC-005)
│   └── integration/
│       └── test_pipeline.py         # Tests full flow, output file existence
├── docs/
│   └── README.md
└── requirements.txt
```

**Structure Decision**: Single project structure selected. The pipeline is a linear data processing flow (Load -> Process -> Analyze -> Viz) suitable for a single `code/` directory. Tests are separated into `unit/` (logic) and `integration/` (pipeline flow).

**Directory Initialization**: 
- The implementation MUST create `.gitkeep` files in all empty directories (`code/`, `data/raw/`, `data/processed/`, `data/visualizations/`, `tests/unit/`, `tests/integration/`, `docs/`) to ensure Git tracks them.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Simulated Data Fallback** | No real matched dataset exists (Assumption in Spec). | A "toy" dataset would not validate the statistical pipeline's ability to detect a known correlation (r=0.5) or handle the specific constraints of HCP data structures. |
| **Orthogonalization for Collinearity** | FR-004 requires handling VIF > 5. Suppression destroys hypothesis testing. | Simply suppressing p-values prevents answering "Which metric predicts?". Orthogonalization allows unique effect estimation. |
| **Sensitivity Analysis (AAL/Power)** | US-3 requires robustness verification. | Relying on a single atlas (Schaefer) is methodologically weak in neuroscience; the bar chart comparison is required to demonstrate result stability. |
| **CLI Argument `--atlas`** | FR-006 requires user specification. | Hardcoding all atlases reduces flexibility; user must be able to specify which alternative to test. |
| **Null Hypothesis Simulation** | Scientific soundness requires testing r=0, not just r=0.5. | Simulating r=0.5 as the primary path creates a tautology. r=0 tests Type I error control. |