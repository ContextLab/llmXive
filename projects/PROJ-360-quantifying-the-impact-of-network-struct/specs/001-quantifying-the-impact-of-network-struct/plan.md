# Implementation Plan: Quantifying the Impact of Network Structure on Heat Diffusion in Crystalline Solids

**Branch**: `001-network-structure-thermal-conductivity` | **Date**: 2024-01-15 | **Spec**: `specs/001-network-structure-thermal-conductivity/spec.md`
**Input**: Feature specification from `specs/001-network-structure-thermal-conductivity/spec.md`

## Summary

This feature implements a computational pipeline to quantify the correlation between topological network metrics of atomic structures and their thermal conductivity in crystalline solids. The approach involves downloading crystallographic data (CIF files) from the Materials Project, constructing atomic networks based on covalent radii, computing graph metrics (degree, path length, clustering), and performing statistical correlation and linear regression analysis to predict thermal conductivity. The plan explicitly addresses confounding variables (volume, atom count, mass) and statistical limitations (sample size, metric coupling).

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pymatgen` (for CIF parsing, bond detection, and physical descriptors), `networkx` (for graph metrics), `scikit-learn` (for regression and cross-validation), `pandas` (data manipulation), `requests` (API access), `numpy` (numerical operations), `statsmodels` (VIF and robust statistics).
**Storage**: Local filesystem (`data/raw/cif/`, `data/processed/`, `models/`, `results/`).
**Testing**: `pytest` for unit tests on network construction and metric calculation; integration tests for the full pipeline.
**Target Platform**: Linux (GitHub Actions free-tier runner: limited CPU, constrained RAM, GB disk).
**Project Type**: Data analysis pipeline / Scientific computing.
**Performance Goals**: Full pipeline execution < 6 hours; API retry logic handles /503 errors.
**Constraints**: No GPU; CPU-only execution; strict adherence to Materials Project API rate limits; deterministic random seeds.
**Scale/Scope**: Target ≥50 materials; < 7 GB RAM usage during processing.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

1. **Reproducibility (NON-NEGOTIABLE)**: Plan includes explicit random seed pinning in `research.md` and `quickstart.md`. Dependencies will be pinned in `requirements.txt`.
2. **Verified Accuracy**: The plan references the Materials Project API. **Correction**: The reference URL in `research.md` has been updated to use the programmatic API endpoint pattern (` Name or service not known)"))]) or a verified dataset loader where direct URL access is restricted, ensuring the "Verified datasets" constraint is met by relying on the `pymatgen` interface which handles authentication and rate limiting, rather than a static HTML URL that returns 403. **Action**: The Reference-Validator Agent will run on all citations in `idea/`, `technical-design/`, and `implementation-plan/` before Phase 0 execution, as mandated by Principle II.
3. **Data Hygiene**: Plan mandates checksumming of raw CIF downloads and immutable storage in `data/raw/`.
4. **Single Source of Truth**: All metrics and results will be derived from `data/processed/metrics.csv` and stored in JSON/CSV, never hand-typed.
5. **Versioning Discipline**: The plan explicitly commits to updating the `state/projects/PROJ-360-quantifying-the-impact-of-network-struct.yaml` file, specifically the `artifact_hashes` map, whenever any artifact under `data/` or `code/` changes, satisfying Principle V.
6. **Numerical Stability**: Plan specifies `scikit-learn` and `numpy` with fixed seeds for all stochastic steps (cross-validation, VIF calculation).
7. **Materials Project Data Provenance**: The plan includes a `data/metadata.yaml` to record the snapshot timestamp and material IDs used.

## Project Structure

### Documentation (this feature)

```text
specs/001-network-structure-thermal-conductivity/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
└── tasks.md # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── download.py # CIF download with retry logic (FR-001)
├── construct_network.py # Bond detection and graph creation (FR-002)
├── compute_metrics.py # Network metric calculation + Physical descriptors (FR-003)
├── analyze.py # Correlation, Regression, Power Analysis (FR-004, FR-005, FR-006, FR-007, FR-010)
├── report.py # Report generation with mandatory text (FR-008)
├── utils.py # Shared utilities (VIF, logging, imputation)
└── requirements.txt # Pinned dependencies

data/
├── raw/
│ └── cif/ # Downloaded CIF files
├── processed/
│ ├── networks/ # Graph objects (pickle)
│ └── metrics.csv # Aggregated metrics + Physical descriptors
└── metadata.yaml # Snapshot info

results/
├── correlations.json # Correlation results
├── model_performance.json # CV results
├── power_analysis.log # Power analysis log
└── final_report.md # Generated report with Limitations section
```

**Structure Decision**: Single `code/` directory with modular scripts to ensure the pipeline can be run sequentially or individually, satisfying the "Single Source of Truth" and "Data Hygiene" principles.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project scope is contained within a single computational pipeline. | N/A |

## Implementation Phases

### Phase 0: Data Acquisition & Network Construction (US-1, FR-001, FR-002)
1. **Download**: Query Materials Project for materials with thermal conductivity data. Apply retry logic (exponential backoff) for rate limits.
2. **Bond Detection**: Use `pymatgen`'s covalent radius summation ($r_i + r_j + \delta$) to define edges.
3. **Fallback**: If no bonds found, increase cutoff to a suitable value, then a characteristic interatomic distance on the order of a few angstroms. Skip if still disconnected.
4. **Graph Creation**: Construct `networkx.Graph` objects.
5. **Testing**: Unit tests verify ≥50 CIFs downloaded and parsed; graphs have ≥2 nodes.

### Phase 1: Metric Computation & Confounder Extraction (US-2, FR-003, FR-009)
1. **Network Metrics**: Compute average degree, average path length (LCC), and clustering coefficient.
2. **Physical Descriptors**: Calculate Unit Cell Volume, Total Atom Count, and Mean Atomic Mass for each material to control for confounding size/physics effects.
3. **Missing Data Strategy**: If a graph is disconnected, impute `average_path_length` with the median of connected components (if n>5) or flag as NaN for exclusion in that specific metric's correlation.
4. **Testing**: Integration tests verify metrics are computed and physical descriptors are added.

### Phase 2: Statistical Analysis & Modeling (US-2, US-3, FR-004, FR-005, FR-006, FR-007, FR-010)
1. **Distribution Check**: Perform Shapiro-Wilk test on thermal conductivity and metrics. If non-normal, apply log-transformation.
2. **Correlation**: Compute Pearson/Spearman coefficients with Bonferroni correction (adjusted for the number of comparisons).
3. **Collinearity**: Calculate VIF. Exclude features with VIF $\ge $.
4. **Regression**: Train Linear Regression on filtered features + physical descriptors.
5. **Validation**: K-fold Cross-Validation

The specific value to remove/generalize: 'K'

Rewritten passage:.
6. **Power Analysis**: If $n < 50$, log a warning in `results/power_analysis.log` (FR-010).
7. **Testing**: Verify correlation outputs and CV metrics.

### Phase 3: Report Generation (FR-008, SC-006)
1. **Generate Report**: Create `results/final_report.md`.
2. **Insert Limitations**: Explicitly insert the mandatory text: "This study is observational. Correlations do not imply causality. The thermal conductivity tensor was reduced to a scalar by averaging principal components, which may obscure anisotropic effects."
3. **Testing**: Verify the report exists and contains the mandatory text.

## Testing Strategy

- **Unit Tests**: Cover FR-001 (download retry logic), FR-002 (bond detection fallbacks).
- **Integration Tests**: Cover FR-003 to FR-007 (metrics computation, correlation, regression, power logging).
- **Contract Tests**: Verify output schemas against `contracts/*.schema.yaml`.

## Compute Feasibility

- **Hardware**: GitHub Actions Free Tier (CPU, 7 GB RAM).
- **Strategy**:
 - Data is processed in a streaming manner (one CIF at a time) to minimize RAM.
 - No GPU required; `networkx` and `scikit-learn` are CPU-optimized.
 - Dataset size (a small number of materials) is trivial for memory.
 - Estimated runtime: < 1 hour.