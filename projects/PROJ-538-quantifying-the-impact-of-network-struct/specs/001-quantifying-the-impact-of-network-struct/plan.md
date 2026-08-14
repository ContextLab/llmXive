# Implementation Plan: Quantifying the Impact of Network Structure on Heat Transport in Disordered Alloys

**Branch**: `001-quantify-network-heat-transport` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-quantify-network-heat-transport/spec.md`

## Summary

This project implements a computational pipeline to quantify the relationship between the topological structure of atomic defects in disordered alloys (Cu-Ni, Au-Ag) and their thermal conductivity.

**Critical Feasibility Note**: The specification assumes the existence of a public repository (OpenKim/Materials Cloud) containing MD snapshots with *pre-calculated thermal conductivity* for Cu-Ni and Au-Ag alloys. However, the "Verified datasets" block indicates **NO verified source** exists for real-world datasets containing *both* atomic coordinates and thermal conductivity for these specific alloys.

Consequently, this plan implements a **Dual-Mode Execution Strategy** with a primary focus on **Methodological Validation**:
1. **Real Data Mode**: Attempts to download from OpenKim/Materials Cloud. If coordinates or conductivity are missing, it halts with a `DataAvailabilityError` (as per Constitution Principle III).
2. **Synthetic Validation Mode**: Generates a physically grounded synthetic dataset using Lennard-Jones potentials (via `ase`/`lammps`) to validate the *methodology* (graph construction, metric extraction, and correlation analysis). Thermal conductivity in this mode is estimated via an independent phonon-scattering model (Callaway approximation) based on defect density and mass difference, **NOT** derived from graph metrics. This ensures the correlation analysis is statistically valid and not tautological. The synthetic data consists of **50 statistically independent snapshots** generated with randomized seeds and thermalization steps to ensure ensemble independence. This mode validates the *pipeline* but does not claim to answer the specific Cu-Ni hypothesis with real data.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `networkx`, `scikit-learn`, `matplotlib`, `seaborn`, `pydantic`, `ase` (for synthetic generation), `phonopy` (for phonon model)
**Storage**: Local file system (CSV/Parquet for data, PNG for figures); no database required.
**Testing**: `pytest` with `pytest-cov`
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, 7 GB RAM)
**Project Type**: Scientific data analysis pipeline / CLI
**Performance Goals**: Complete ingestion, graph construction, and analysis for **N=50 synthetic snapshots** within 6 hours on CPU.
**Constraints**: Must handle missing metadata gracefully; must not fabricate real data; must apply Bonferroni correction for multiple comparisons; must report power analysis; must distinguish between real and synthetic data paths; must ensure statistical independence of synthetic samples.
**Scale/Scope**:
- Real Data: N=0 (expected failure, reported as such).
- Synthetic Validation: N=50 (for methodological validation, ensuring ensemble independence).

## Constitution Check

| Principle | Status | Evidence / Action Plan |
|:--- |:--- |:--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, random seeds in `code/`, and re-fetching from canonical URLs (or deterministic synthetic generation) in `data/`. |
| **II. Verified Accuracy** | **PASS (Synthetic)** | Synthetic data generation code is verified. Real data sources are unverified/missing; the plan halts if real data is required but missing, avoiding false claims. |
| **III. Data Hygiene** | **PASS (Synthetic)** | Synthetic data is checksummed and derived deterministically. Real data is preserved unchanged; if missing, the pipeline halts rather than fabricating. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats trace to `data/` rows and `code/` blocks. Synthetic data is clearly labeled. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts carry content hashes; `state` YAML updated on change. |
| **VI. Numerical Stability** | **PASS** | Plan mandates robust regression diagnostics, outlier checks, and explicit handling of NaNs/undefined metrics. |
| **VII. Graph-Theoretic Fidelity** | **PASS** | Edge definition (mismatched species, Voronoi) strictly enforced in `code/`; deviations logged as variants. |

## Project Structure

### Documentation (this feature)
```text
specs/001-quantify-network-heat-transport/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
└── contracts/
 ├── atomic_snapshot.schema.yaml
 ├── defect_graph.schema.yaml
 └── correlation_result.schema.yaml
```

### Source Code (repository root)
```text
projects/PROJ-538-quantifying-the-impact-of-network-struct/
├── code/
│ ├── __init__.py
│ ├── main.py # Entry point (routes to Real or Synthetic)
│ ├── ingest.py # Data ingestion & graph construction
│ ├── synthetic.py # Synthetic data generation (LJ potentials)
│ ├── metrics.py # Topological metric extraction
│ ├── stats.py # Correlation, power analysis, sensitivity
│ ├── viz.py # Plot generation
│ └── config.py # Hyperparameters & paths
├── data/
│ ├── raw/ # Downloaded datasets or synthetic seeds
│ └── processed/ # Graphs, metrics, results
├── tests/
│ ├── unit/
│ │ ├── test_ingest.py
│ │ ├── test_metrics.py
│ │ ├── test_stats.py
│ │ └── test_sensitivity.py
│ └── contract/
│ └── test_schemas.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure chosen for simplicity. The workflow is linear (Ingest -> Metrics -> Stats -> Viz), fitting a monolithic script structure with modular functions. No frontend/backend split required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|:--- |:--- |:--- |
| **Voronoi Tessellation** | Required by spec (US-1, FR-002) to define "nearest neighbor" in disordered lattices. | Distance cutoffs are inaccurate for disordered alloys where atomic spacing varies; Voronoi is the physical standard. |
| **Bonferroni Correction** | Required by FR-006 to control family-wise error rate across multiple metrics. | Uncorrected p-values would inflate false positives in exploratory analysis. |
| **Power Analysis** | Required by FR-007 due to small sample size (N ≤ 50). | Without it, non-significant results cannot be distinguished from underpowered tests. |
| **Synthetic Data Generation** | Required because no verified real-world dataset exists with both coordinates and conductivity. | Using a proxy dataset without coordinates would fail the core hypothesis. Synthetic data allows methodological validation. |
| **Sensitivity Analysis** | Required by SC-004 to verify robustness of conclusions. | A single threshold (p < 0.05) is arbitrary; sweeping thresholds ensures stability. |

## Implementation Phases

### Phase 0: Data Audit & Mode Selection
- **Task**: Attempt to download from OpenKim/Materials Cloud (FR-001).
- **Verification Mechanism**:
 - Query OpenKim API (` Name or service not known)"))]) and Materials Cloud API (`) for Cu-Ni and Au-Ag snapshots.
 - Check for the presence of `thermal_conductivity` metadata field and atomic coordinate data (`x`, `y`, `z`, `species`).
 - If both are present: Proceed to **Real Data Mode**.
 - If missing: Log `DataAvailabilityError` and switch to **Synthetic Validation Mode**.
- **Output**: `data/audit_log.json` and `data/config/mode.yaml`.

### Phase 1: Data Ingestion & Graph Construction
- **Real Data Mode**: Parse MD snapshots, construct `DefectGraph` via Voronoi.
- **Synthetic Mode**:
 - Generate 50 snapshots using Lennard-Jones potentials (`ase`).
 - **Ensemble Independence**: Each snapshot uses a unique random seed, randomized initial positions, and a thermalization step (NVT ensemble) to ensure statistical independence.
 - Estimate thermal conductivity via an independent phonon-scattering model (Callaway approximation) based on defect density and mass difference, **NOT** derived from graph metrics.
 - Construct `DefectGraph` via Voronoi.
- **Validation**: Verify edge existence ONLY between mismatched species (US-1).
- **Contract Generation**: Generate `contracts/defect_graph.schema.yaml` and validate all constructed graphs against it.

### Phase 2: Topological Metric Extraction
- **Task**: Compute clustering coefficient, mean degree, degree variance, percolation threshold (US-2).
- **Robustness**: Handle disconnected graphs (largest component only). Report NaN with warning if undefined.
- **Contract Validation**: Validate extracted metrics against `contracts/defect_graph.schema.yaml`.

### Phase 3: Statistical Correlation & Power Analysis
- **Task**: Pearson/Spearman correlation (FR-004).
- **Correction**: Apply Bonferroni correction (FR-006).
- **Power**: Perform post-hoc power analysis (FR-007). If N < 20, flag low power. For Synthetic Mode, N=50 is used. For Real Data Mode (N=0), report "Insufficient Data for Power Analysis".

### Phase 4: Sensitivity Analysis (SC-004)
- **Task**: Sweep significance threshold (p < 0.01, 0.05, 0.10).
- **Check**: Verify rank-order stability of correlation coefficients (change < 0.1).
- **Output**: `data/processed/sensitivity_report.csv` and `contracts/sensitivity_result.schema.yaml`.

### Phase 5: Visualization & Reporting
- **Task**: Generate scatter plots, heatmaps (FR-005).
- **Output**: PNG files (300 DPI) and final summary report.

## Risk Register

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Missing Real Data** | **Fatal** for hypothesis. | Switch to Synthetic Validation Mode; clearly label results as methodological validation. |
| **Small Sample Size (N < 20)** | Low statistical power. | Power analysis reported; results qualified as "exploratory". Synthetic mode uses N=50. |
| **Disconnected Graphs** | Undefined $p_c$. | Calculate on largest component; report NaN if no edges. |
| **Tautological Correlation** | Invalid science. | Synthetic conductivity derived from independent phonon model, NOT graph metrics. |
| **Lack of Ensemble Independence** | Invalid statistics. | Synthetic generation uses unique seeds and thermalization steps to ensure independence. |

## References

- **Spec**: `specs/001-quantify-network-heat-transport/spec.md`
- **Constitution**: `projects/PROJ-538-quantifying-the-impact-of-network-struct/.specify/memory/constitution.md`
- **Verified Datasets**: None found for real-world Cu-Ni/Au-Ag + coordinates + conductivity.
