# Implementation Plan: Phase Transitions in Amorphous Solids Under Shear Stress

**Branch**: `001-phase-transitions-amorphous-solids` | **Date**: 2026-09-03 | **Spec**: `specs/001-phase-transitions-in-amorphous-solids/spec.md`
**Input**: Feature specification from `/specs/001-phase-transitions-in-amorphous-solids/spec.md`

## Summary

This feature implements a computational pipeline to detect precursory structural signatures ($D^2_{min}$) in amorphous solids under shear stress. The system ingests molecular dynamics (MD) trajectory data (generated synthetically for validation), computes non-affine displacements using the Falk-Langer algorithm, identifies macroscopic yielding via stress-drop detection, and performs statistical correlation analysis (Permutation Test) between brittle and ductile regimes. The pipeline includes a predictive threshold validation module with sensitivity analysis. The implementation prioritizes CPU-tractable methods (streaming large datasets, sampling where necessary) to fit within GitHub Actions free-tier constraints (modest RAM, 6h runtime).

**Critical Scope Adjustment**: Due to the absence of a verified public MD trajectory dataset containing the required physical variables (particle coordinates, stress tensor, box dimensions), this plan implements a **Synthetic MD Data Generator** to produce valid, physically-grounded trajectories for pipeline validation. The project scope is reframed to "Pipeline Validation on Synthetic MD Data" until real data is available. The "brittle" and "ductile" labels are derived from physical simulation parameters (strain rate, temperature) to ensure non-circular ground truth.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `pandas`, `scipy`, `scikit-learn`, `datasets` (Hugging Face), `matplotlib`, `pyyaml`  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `specs/contracts/`)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`)  
**Project Type**: Scientific analysis CLI / library  
**Performance Goals**: Process ≤100k particle trajectories within 6 hours; memory footprint < 7GB.  
**Constraints**: No local GPU; streaming required for datasets > 14GB; deterministic seeds for reproducibility.  
**Scale/Scope**: Up to 100,000 particles per trajectory; multiple strain rates/temperatures supported via configuration.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Status | Rationale / Mapping |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds are fixed to ensure reproducibility in `code/`. Dependencies pinned in `requirements.txt`. External datasets (Synthetic Generator) are deterministic and reproducible. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` restricted to verified sources (Synthetic Generator logic). No fabricated URLs. |
| **III. Data Hygiene** | **PASS** | Raw data (synthetic) preserved in `data/raw/`. Derived metrics ($D^2_{min}$) written to `data/processed/`. Checksums recorded in `state/`. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats trace to `data/processed/` artifacts. No hand-typed numbers in paper drafts. |
| **V. Versioning Discipline** | **PASS** | Content hashes for artifacts tracked in `state/projects/...yaml`. |
| **VI. Simulation Trajectory Integrity** | **PASS** | Raw trajectories (synthetic) untouched. `code/preprocessing.py` writes new files for derived metrics. |
| **VII. Numerical Determinism** | **PASS** | Fixed seeds for k-means (k=3) and yielding algorithms. Tie-breaking rules enforced. |

## Project Structure

### Documentation (this feature)

```text
specs/001-phase-transitions-in-amorphous-solids/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── trajectory.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-080-phase-transitions-in-amorphous-solids-un/
├── code/
│   ├── __init__.py
│   ├── data_loader.py          # Handles streaming, checksums, raw -> processed
│   ├── data_generator.py       # Synthetic MD trajectory generation
│   ├── preprocessing.py        # Falk-Langer D2_min, stress-drop detection
│   ├── analysis.py             # Permutation Test, shear-band aggregation, sensitivity
│   ├── validation.py           # Threshold prediction, confusion matrix
│   ├── memory_profiler.py      # RAM usage measurement
│   └── utils.py                # Deterministic seeds, logging
├── data/
│   ├── raw/                    # Generated trajectory files
│   └── processed/              # D2_min CSVs, stress curves, aggregated stats
├── specs/001-phase-transitions-in-amorphous-solids/
│   └── contracts/              # Schema definitions
└── tests/
    ├── unit/
    └── integration/
```

**Structure Decision**: Single project structure chosen. The workflow is linear (Generate -> Load -> Preprocess -> Analyze -> Validate), fitting a monolithic `code/` directory with modular scripts. No web server or mobile components required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Shear-Band Aggregation** | Required by FR-003 (amended) to account for spatial autocorrelation before Permutation Test. | Direct KS-test on particle-level data violates statistical assumptions (independence). |
| **Streaming Data Loader** | Required by SC-005 (7GB RAM limit) for large MD trajectories. | Loading full dataset into memory causes OOM on CI runner. |
| **Sensitivity Sweep** | Required by FR-004 to validate threshold robustness. | Single-threshold validation is insufficient for scientific rigor (arbitrary cutoff). |
| **Synthetic Data Generator** | Required due to lack of verified MD trajectory data. | Using generic proxy data (e.g., KS-test parquet) lacks physical variables (coordinates, stress) and renders validation invalid. |

## Functional Requirements Mapping

| Requirement | Implementation Detail | Status |
| :--- | :--- | :--- |
| **FR-001** | Falk-Langer algorithm implemented in `code/preprocessing.py` using vectorized NumPy. | Planned |
| **FR-002** | Yielding onset detection: **First significant stress drop defined as >5% decrease relative to local max over 50 timesteps**. Implemented in `code/preprocessing.py`. | Planned |
| **FR-003** | **Amended**: Standard KS-test replaced by **Permutation Test** on shear-band aggregated data to handle spatial autocorrelation. Implemented in `code/analysis.py`. | Planned (Spec Deviation) |
| **FR-004** | Sensitivity analysis: Sweep threshold $\{ \text{threshold} - \delta, \text{threshold}, \text{threshold} + \delta \}$ and report FPR/FNR. | Planned |
| **FR-005** | Bonferroni correction applied if >1 hypothesis test (e.g., multiple strain rates). | Planned |
| **FR-006** | Particle count limit: [deferred]. Enforced in `code/data_generator.py`. | Planned |
| **SC-005** | Memory profiling: `code/memory_profiler.py` measures RAM usage and logs to `data/processed/memory_profile.json`. | Planned |

## Phases

### Phase 0: Synthetic Data Generation
*Goal: Generate valid MD trajectories with physical labels.*
- **Task T001**: Implement `data_generator.py` to create particle coordinates, box dimensions, and stress tensors.
- **Task T002**: Assign "brittle" or "ductile" labels based on physical simulation parameters (strain rate, temperature).
- **Task T003**: Save raw trajectories to `data/raw/` and compute SHA-256 checksums.

### Phase 1: Preprocessing
*Goal: Compute $D^2_{min}$ and identify yielding.*
- **Task T004**: Implement `preprocessing.py` to compute Falk-Langer $D^2_{min}$ for each particle.
- **Task T005**: Implement stress-drop detection algorithm ([deferred] drop over 50 timesteps) to flag yielding timesteps.
- **Task T006**: Output `data/processed/d2_min_trajectory.csv` and `data/processed/stress_curve.csv`.

### Phase 2: Statistical Analysis
*Goal: Compare distributions between brittle and ductile regimes.*
- **Task T007**: Aggregate $D^2_{min}$ values to shear bands using k-means (k=3, seed=42).
- **Task T008**: Implement Permutation Test on shear-band aggregates to compare brittle vs. ductile distributions.
- **Task T009**: Output `data/processed/permutation_results.json` and `data/processed/shear_band_stats.csv`.

### Phase 3: Validation
*Goal: Validate predictive threshold and sensitivity.*
- **Task T010**: Implement sensitivity analysis to sweep thresholds and compute FPR/FNR.
- **Task T011**: Output `data/processed/sensitivity_table.csv` and `data/processed/validation_report.json`.

### Phase 4: Memory Profiling
*Goal: Measure and report RAM usage.*
- **Task T012**: Run `memory_profiler.py` during data generation and preprocessing.
- **Task T013**: Output `data/processed/memory_profile.json` with peak RAM usage.

### Phase 5: Documentation & Artifacts
*Goal: Generate final reports and schemas.*
- **Task T014**: Update `quickstart.md` with commands for synthetic data generation.
- **Task T015**: Generate final `plan.md`, `research.md`, `data-model.md`, and `contracts/`.

## Spec Deviations

| Spec Requirement | Deviation | Justification |
| :--- | :--- | :--- |
| **FR-003**: KS-test on shear-band aggregates | **Permutation Test** | Standard KS-test is invalid for spatially autocorrelated data even after aggregation. Permutation test is the statistically rigorous alternative. |
| **Spec Assumption**: Public MD dataset exists | **Synthetic Data Generator** | No verified public MD trajectory dataset with required variables (coordinates, stress) exists. Synthetic data is necessary for pipeline validation. |