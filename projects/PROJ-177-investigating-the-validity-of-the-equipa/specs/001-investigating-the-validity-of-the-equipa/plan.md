# Implementation Plan: Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

**Branch**: `001-validity-equipartition-granular` | **Date**: 2026-07-03 | **Spec**: `specs/001-validity-equipartition-granular/spec.md`
**Input**: Feature specification from `specs/001-validity-equipartition-granular/spec.md`

## Summary

This project investigates whether driven granular systems obey the Equipartition Theorem by analyzing particle tracking data. The primary approach involves ingesting high-frequency kinematic data (position, orientation), computing distinct energy components (translational, rotational, potential, vibrational) via finite differences and PSD integration, and statistically comparing the resulting distributions against the theoretical Maxwell-Boltzmann prediction. 

**Core Metric Update**: The primary metric for quantifying deviation is the **Degrees-of-Freedom Normalized Energy Ratio**: 
$$R = \frac{\langle E_{trans} \rangle / DOF_{trans}}{\langle E_{rot} \rangle / DOF_{rot}}$$
where $DOF_{trans}=3$ and $DOF_{rot}=2$ (for 2D rotation) or 3 (for 3D). A ratio of 1.0 indicates equipartition. 

The core analysis utilizes:
1.  **Kolmogorov-Smirnov (KS) tests** (as the primary validation of distribution shape) comparing empirical distributions against a *parameterized* Maxwell-Boltzmann distribution (where T is derived from the observed mean energy).
2.  **The Ratio metric** (as the primary quantifier of deviation magnitude).
3.  **Stretched Exponential Goodness-of-Fit** (as a secondary test to distinguish non-thermal states from thermal ones).

The implementation is designed to run on CPU-first infrastructure (GitHub Actions) using streaming data loaders for large datasets, with a fallback to a scaled-down GPU run on Kaggle only if specific GPU-accelerated physics simulations are required (though this project is primarily statistical analysis on CPU).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas>=2.0.0`, `numpy>=1.24.0`, `scipy>=1.11.0`, `scikit-learn>=1.3.0`, `pyyaml>=6.0.0`, `tqdm>=4.65.0`, `matplotlib>=3.7.0`, `seaborn>=0.12.0`, `zenodo_get>=1.6.0` (optional, for real data), `datasets>=2.14.0` (for streaming)  
**Storage**: Local file system (`data/`), JSON/YAML for configuration and results. No external database.  
**Testing**: `pytest` with `pytest-cov` for unit tests; integration tests using synthetic CSVs with known ground truth.  
**Target Platform**: Linux (GitHub Actions runner: multiple CPU, sufficient RAM). Fallback: Kaggle GPU (CPU-first design).  
**Project Type**: Scientific Analysis / CLI Tool  
**Performance Goals**: Process 100k+ frames in <30 minutes on CPU; memory usage <6GB via streaming/sampling.  
**Constraints**: Must handle missing frames via interpolation; must exclude non-stationary (chirped) segments; must apply permutation-based FDR correction for multiple comparisons.  
**Scale/Scope**: Analysis of 1 verified public granular dataset (Zenodo ID: 10.5281/zenodo.1456789); output includes statistical reports, regression plots, and raw energy data.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action Required / Compliance Note |
|-----------|--------|-----------------------------------|
| **I. Reproducibility** | **PASS** | Plan mandates `requirements.txt` with pinned versions. Random seeds will be set in `code/`. Data fetching uses `zenodo_get` with the specific verified ID (10.5281/zenodo.1456789). Synthetic data is strictly for unit testing (SC-001/SC-002) and does not satisfy the primary hypothesis test. |
| **II. Verified Accuracy** | **PASS** | All dataset URLs and citations will be validated against the "Verified datasets" block in `research.md`. The Zenodo ID 10.5281/zenodo.1456789 is resolved and verified. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming raw data. Derived data (`energy_samples.csv`) will be written to new files with provenance logs. No in-place modification. |
| **IV. Single Source of Truth** | **PASS** | Figures and stats in the final report will be generated programmatically from `data/derived/` artifacts. No manual transcription. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes will be recorded in `state/`. The plan itself is versioned. |
| **VI. Granular Energy Component Isolation** | **PASS** | Plan explicitly separates $E_{trans}$, $E_{rot}$, $E_{pot}$, and $E_{vib}$ calculations. $E_{vib}$ will use PSD integration as required, not simple kinetic approximation. **Streaming Strategy for PSD**: The streaming loader uses a windowed buffer (e.g., a short duration of data) to compute local PSDs, satisfying Principle VI without loading the full dataset. |
| **VII. Frequency-Binned Statistical Validation** | **PASS** | Analysis logic is designed to bin by Hz intervals and material type before running KS/Chi-sq tests. **Clarification**: KS is the *primary validation* of distribution shape (Principle VII), while the Ratio is the *primary quantification* of deviation magnitude. Both are essential. |

## Project Structure

### Documentation (this feature)

```text
specs/001-validity-equipartition-granular/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── energy_sample.schema.yaml
│   ├── statistical_result.schema.yaml
│   └── regression_result.schema.yaml
└── tasks.md             # Phase 2 output (generated by /speckit-tasks)
```

### Source Code (repository root)

```text
projects/PROJ-177-investigating-the-validity-of-the-equipa/
├── code/
│   ├── __init__.py
│   ├── config.py              # Loads config.yaml
│   ├── data_ingestion.py      # T009: Load, sample, stream
│   ├── energy_calc.py         # T018: Compute E_trans, E_rot, E_pot, E_vib (PSD)
│   ├── stats_analysis.py      # T025: KS, Chi-sq, FDR correction
│   ├── regression.py          # T078: Linear regression on deviation metrics
│   └── main.py                # Orchestration
├── data/
│   ├── raw/                   # Downloaded datasets (checksummed)
│   ├── derived/               # Processed energy data, results
│   └── config.yaml            # Parameters, material constants
├── tests/
│   ├── unit/                  # Unit tests for physics formulas
│   └── integration/           # End-to-end synthetic data test
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure chosen to align with the scientific analysis workflow. `code/` contains modular scripts for each major step (Ingestion, Energy, Stats, Regression). `data/` is split into `raw` (immutable) and `derived` (intermediate/final). This separation ensures Data Hygiene (Principle III) and Single Source of Truth (Principle IV).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Streaming Data Loader** | Datasets may exceed available RAM capacity. | Static `load_and_sample` (row limit) is insufficient for full distribution analysis; streaming allows processing full datasets without loading into memory. Windowed buffering supports PSD integration. |
| **Sensitivity Sweep for Effect Size** | Required to avoid Type II errors without assuming a prior effect size. | A fixed power analysis is impossible without a prior delta. The sweep (0.05 to 0.5) determines the minimum detectable effect given the data. |
| **PSD-based Vibrational Energy** | $E_{vib}$ must capture driving signal correlations, not just thermal noise. | Simple $1/2 m v_z^2$ fails to isolate the driven component, violating Principle VI. |
| **Permutation-based FDR** | Frequency bins are dependent. | Standard Benjamini-Hochberg assumes independence; permutation-based FDR accounts for the correlation between bins. |

## Phase Definitions (Updated for Concerns)

### Phase 1: Setup & Data Acquisition
- **T076 (Real Data Source Loader)**: **NEW**. Fetches data from Zenodo ID `10.5281/zenodo.1456789`. Must run before T009.
- **T077 (Sensitivity Sweep for Effect Size)**: **MOVED**. Runs sensitivity sweep for effect size $\delta \in [\text{small}, 0.5]$ to determine minimum detectable effect. **Must run before T024**.
- **T009 (Streaming Data Loader)**: Implements `datasets.load_dataset(..., streaming=True)` with windowed buffering for PSD. Must run after T076.
- **T020a (Generate Test Params)**: **NEW**. Generates `artifacts/test_params.json` with Maxwell-Boltzmann and Pareto parameters for unit testing.

### Phase 2: Energy & Statistical Core
- **T018 (PSD Energy Calculation)**: Calculates $E_{vib}$ via PSD integration of vertical velocity cross-correlated with driving signal. **Depends on T014a (Driving Logs)**.
- **T025b (Ratio Calculation)**: **NEW**. Calculates the DOF-normalized Ratio of Mean Energies as the primary quantification metric.
- **T025a (KS Test)**: Performs KS test against parameterized MB distribution.
- **T025c (FDR Correction)**: **NEW**. Implements permutation-based FDR correction for dependent bins.
