# Implementation Plan: Statistical Properties of Simulated Black Hole Mergers

**Branch**: `001-statistical-properties-black-hole-mergers` | **Date**: 2026-06-28 | **Spec**: `specs/001-statistical-properties-black-hole-mergers/spec.md`
**Input**: Feature specification from `/specs/001-statistical-properties-black-hole-mergers/spec.md`

## Summary

This project implements a CPU-tractable statistical analysis pipeline to compare observational Gravitational Wave Transient Catalog (GWTC) data against simulated binary black hole merger populations. The primary technical approach involves downloading posterior samples from GWTC-1/2, generating or acquiring a synthetic population catalog with matching schema (mass_ratio, effective_spin), and performing Kolmogorov-Smirnov (KS) tests with Bonferroni correction and sensitivity analysis. The pipeline strictly adheres to GitHub Actions free-tier constraints (≤6h runtime, ≤7GB RAM, CPU-only) and addresses scientific rigor requirements including power analysis, MDES calculation, and selection bias correction. The analysis explicitly distinguishes between comparing *intrinsic* populations (requiring formal selection functions) and *detection* distributions (unweighted comparison).

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `numpy`, `scipy`, `pandas`, `matplotlib`, `requests`, `tqdm`
**Storage**: Local filesystem (`data/` for raw/processed, `output/` for figures/reports)
**Testing**: `pytest` (unit tests for data parsing, integration tests for pipeline execution)
**Target Platform**: Linux (GitHub Actions free-tier runner)
**Project Type**: Data analysis pipeline / CLI
**Performance Goals**: Runtime ≤6 hours, Peak RAM ≤7 GB, Peak Disk ≤20 GB
**Constraints**: No GPU/CUDA; no external heavy LLMs; all random seeds pinned; checksum verification for all data.
**Scale/Scope**: Processing ≥100 *valid* merger events per catalog (after filtering NaNs); generating 2 primary KDE plots; running KS tests on 2 dimensions.

> Domain-specific empirical specifics (exact counts, dataset sizes) are deferred to the research/implementation phase. The pipeline is designed to handle the full GWTC catalog if available, but will sample if necessary to meet memory constraints.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Plan Action |
|-----------|--------|------------------------|
| **I. Reproducibility** | PASS | Plan mandates `requirements.txt` pinning, random seed enforcement in `code/`, and checksummed data in `data/`. Pipeline re-runs from scratch on CI. |
| **II. Verified Accuracy** | PASS | Citations in `research.md` restricted to the "# Verified datasets" block provided by the system. No fabricated URLs. |
| **III. Data Hygiene** | PASS | Raw data preserved; derivations written to new files with content hashes recorded in `state/`. PII scan passed (no PII expected in astrophysical catalogs). |
| **IV. Single Source of Truth** | PASS | Figures and stats in reports generated directly from `data/` and `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | PASS | Artifacts carry content hashes; `updated_at` timestamps updated on change. |
| **VI. Simulation Data Integrity** | **AMENDED** | **Constitution Amendment Path Initiated**: Principle VI mandates IllustrisTNG/EAGLE. The Spec explicitly notes these lack resolved component mass/spin for BBH. The plan implements the fallback (Synthetic/Power-law) as per Spec Assumptions. **Action**: A formal amendment is initiated to replace "IllustrisTNG/EAGLE" with "BBH Population Synthesis or Validated Synthetic Models" to align with scientific validity. No data lacking the required schema will be used. |
| **VII. Statistical Rigor** | PASS | KS tests, Bonferroni correction, sensitivity analysis (α ∈ {near-standard values}), and formal simulation-based power analysis (MDES) are explicitly planned. CPU-only execution ensures deterministic runtime. |

## Project Structure

### Documentation (this feature)

```text
specs/001-statistical-properties-black-hole-mergers/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── gwtc_catalog.schema.yaml
    ├── simulation_catalog.schema.yaml
    ├── statistical_test_result.schema.yaml
    ├── power_analysis_result.schema.yaml
    └── visualization_output.schema.yaml
```

### Source Code (repository root)

```text
src/
├── main.py                 # Pipeline entry point
├── data/
│   ├── download.py         # Downloaders for GWTC and Simulation
│   ├── preprocess.py       # Parsing, filtering, NaN handling
│   └── schemas.py          # Validation logic
├── analysis/
│   ├── kde.py              # KDE computation (Scott's rule)
│   ├── ks_test.py          # KS test, Bonferroni, Sensitivity
│   └── power.py            # MDES and Power Analysis (Simulation-based)
├── viz/
│   └── plots.py            # KDE plots, divergence annotation
├── utils/
│   ├── checksum.py         # Integrity verification
│   └── logger.py           # Logging configuration
└── config.py               # Paths, seeds, thresholds

tests/
├── contract/
│   └── test_schemas.py     # Validate data against YAML schemas
├── integration/
│   └── test_pipeline.py    # End-to-end run on sample data
└── unit/
    ├── test_kde.py
    └── test_ks_test.py
```

**Structure Decision**: Single project structure (`src/`) chosen for simplicity and alignment with the "CLI/Data Analysis" project type. Separates concerns into `data`, `analysis`, `viz`, and `utils` to facilitate testing and maintenance.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Synthetic Data Generation | Constitution Principle VI requires specific simulation data (IllustrisTNG/EAGLE) which lacks the required schema (resolved mass/spin). | Using IllustrisTNG directly would fail FR-002/FR-005 (schema mismatch). Generating a synthetic catalog based on a power-law hypothesis (cited from GWTC-3 literature) is the only scientifically valid path to satisfy the statistical comparison requirement. |
| Sensitivity Analysis (α sweep) | Spec US-2b requires robustness check against arbitrary thresholds. | Skipping this would violate FR-009 and scientific rigor standards for population inference. |
| Power Analysis & MDES | Spec US-2c and FR-010/FR-015 require quantifying Type II error risk. | Omitting this would leave non-significant results uninterpretable, violating SC-010. The heuristic sample-size ratio is replaced by a formal simulation-based MDES. |
| Selection Bias Handling | GWTC data is subject to strong mass-dependent selection bias. | Simple volume-weighting is scientifically invalid. The plan adopts a two-tier approach: (1) Primary analysis on unweighted distributions (detection space), (2) Optional formal correction if LVK selection files are available. |