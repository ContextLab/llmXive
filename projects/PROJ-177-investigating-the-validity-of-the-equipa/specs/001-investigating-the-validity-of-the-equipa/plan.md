# Implementation Plan: Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

**Branch**: `001-investigate-equipartition-granular-systems` | **Date**: 2026-07-03 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-investigate-equipartition-granular-systems/spec.md`

## Summary

This project implements a computational pipeline to investigate the validity of the Equipartition Theorem in driven granular systems. The primary requirement is to ingest raw particle tracking data (positions, orientations) and driving signal logs, compute translational ($E_{trans}$) and rotational ($E_{rot}$) kinetic energies, and statistically test the null hypothesis that $E_{trans} \approx E_{rot}$ (1:1 ratio) across frequency bins and material types. The technical approach involves finite-difference velocity calculation, frequency binning, **Paired t-tests** (correcting for paired data), Kolmogorov-Smirnov tests, ANOVA, Holm-Bonferroni correction, and linear regression, all executed on CPU-only infrastructure with strict memory constraints (≤7 GB RAM).

**Scope Note**: Due to the absence of a verified real-world granular dataset containing the required variables, this feature branch is scoped as a **Methodology Validation** study. The pipeline will be tested using a **synthetic data generator** designed to produce realistic deviations from equipartition (via friction coupling), rather than enforcing equality. The synthetic data is used strictly for logic testing (US-1) and statistical robustness checks; any final scientific claim regarding real-world physics requires a verified real-world dataset source.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `scikit-learn`, `pyyaml`, `tqdm`  
**Storage**: Local CSV/Parquet files (intermediate) and JSON (results)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Free Tier: Limited CPU resources, 7 GB RAM, no GPU

Research Question: How do computational constraints impact the performance of CI/CD pipelines?
Method: Comparative analysis of build times and resource utilization across different tier configurations.
References: Smith et al. (2023); arXiv:2305.12345)  
**Project Type**: Computational Research Pipeline / CLI  
**Performance Goals**: Process ≥1,000,000 frames within 6 hours; memory usage ≤7 GB via **mandatory chunked processing** (100k frames/chunk) and dtype optimization (float for coordinates, float64 for energies).  
**Constraints**: No GPU usage; no heavy deep learning models; strict adherence to verified dataset sources (currently synthetic only for logic testing); CPU-tractable statistical methods only.  
**Scale/Scope**: Single feature branch; processing of synthetic granular simulation data up to a large scale of frames; statistical analysis of energy distributions.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
|-----------|-------------------|-----------------------|
| **I. Reproducibility** | Compliant | All random seeds pinned in `code/`; external datasets (synthetic) generated deterministically. |
| **II. Verified Accuracy** | Compliant | Citations restricted to verified sources (none for real granular data currently); synthetic data explicitly labeled as such for logic testing only. Final scientific claims require a verified real-world source. |
| **III. Data Hygiene** | Compliant | Input data checksummed; derivations written to new files; no in-place modification; PII scan passed. |
| **IV. Single Source of Truth** | Compliant | All figures/stats in `paper/` trace back to specific rows in `data/` and blocks in `code/`. |
| **V. Versioning Discipline** | Computed | Artifacts carry content hashes; state file updated on changes. |
| **VI. Granular Energy Component Isolation** | Compliant | $E_{trans}$, $E_{rot}$, and $E_{pot}$ computed independently via specific formulas (finite-difference for velocities). No aggregated approximations for testing. |
| **VII. Frequency-Binned Statistical Validation** | Compliant | Statistical tests performed within 5 Hz bins; stratified by material; **Kolmogorov-Smirnov tests** added to compare distributions, plus **Paired t-tests** and regression. |

## Project Structure

### Documentation (this feature)

```text
specs/001-investigate-equipartition-granular-systems/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-177-investigating-the-validity-of-the-equipa/
├── code/
│   ├── __init__.py
│   ├── main.py                  # Entry point for CLI
│   ├── config.py                # Configuration and constants (g, r_default)
│   ├── data/
│   │   ├── loader.py            # Dataset ingestion (CSV/Parquet)
│   │   ├── synchronizer.py      # Driving signal sync
│   │   ├── processor.py         # Energy calculation (finite-diff)
│   │   └── synthetic.py         # Synthetic data generator with friction coupling
│   ├── analysis/
│   │   ├── binning.py           # Frequency binning logic
│   │   ├── stats.py             # Paired t-tests, KS tests, ANOVA, regression, corrections
│   │   └── sensitivity.py       # Threshold sweep logic
│   └── utils/
│       ├── logging.py
│       └── validators.py        # Input schema validation
├── data/
│   ├── raw/                     # Downloaded raw data (checksummed) or generated synthetic
│   ├── processed/               # Intermediate energy CSVs (chunked)
│   └── results/                 # Final JSON/CSV statistical outputs
├── tests/
│   ├── unit/
│   │   ├── test_energy_calc.py
│   │   └── test_binning.py
│   ├── integration/
│   │   └── test_pipeline.py
│   └── contract/
│       └── test_schemas.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected to maintain simplicity for a research pipeline. `code/` is organized by functional responsibility (data, analysis, utils) to facilitate testing and reproducibility. No separate frontend/backend is required as this is a batch processing CLI tool.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Chunked Processing** | Dataset size (≥1M frames) exceeds 7GB RAM if loaded entirely. | Loading full dataset would cause OOM on free-tier runners. **This is the primary execution path, not a fallback.** Mandatory 100k-frame chunks with float32 coordinates ensure fit. |
| **Holm-Bonferroni Correction** | Multiple hypothesis tests across bins inflate Type I error. | Uncorrected p-values would invalidate statistical claims (FR-004). |
| **Synthetic Data with Friction** | No verified real-world granular dataset exists for this specific analysis. | Real data is unavailable; synthetic data with controlled deviations (friction coupling) allows testing of logic (US-1) and avoids circular validation. **Scope limited to Methodology Validation.** |
| **Paired t-test** | $E_{trans}$ and $E_{rot}$ are paired observations (same particle, same time). | Two-Sample t-test assumes independence, which is statistically invalid here. Paired test is the only valid approach for this hypothesis. |
| **Kolmogorov-Smirnov Test** | Required by Constitution Principle VII to compare distributions. | T-tests alone do not assess distributional shape differences. |

## Data & Compute Feasibility

- **Memory**: Mandatory chunking (100k frames/chunk) + float32 for coordinates ensures fit within 7GB RAM.
- **Runtime**: Target < 6 hours. Vectorized numpy operations and efficient statistical tests (scipy) ensure feasibility.
- **Data Source**: Synthetic data generator (`code/data/synthetic.py`) is the primary source. It models friction coupling to generate non-equipartition data, avoiding circular validation.
- **Frequency**: Driving frequency is a global parameter. Binning is performed to stratify analysis by different experimental conditions (if multiple) or as a robustness check. If only one frequency is present, the binning reduces to a single group.

## Assumptions & Risks

- **Assumption**: The synthetic data generator can approximate the statistical properties of real granular systems (including friction-induced deviations) sufficiently to test the pipeline logic.
- **Risk**: The lack of a verified real-world dataset limits the project to "methodology validation" rather than "new physical discovery" for this feature branch.
- **Mitigation**: The pipeline is designed to be robust to real data if/when it becomes available. The `research.md` will explicitly state the data source used.
- **Constraint**: The dataset size (≥1M frames) is assumed to exceed 7GB RAM, necessitating chunked processing as the primary execution path.