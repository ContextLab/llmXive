# Implementation Plan: Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

**Branch**: `001-validity-equipartition-granular` | **Date**: 2026-07-03 | **Spec**: `specs/001-validity-equipartition-granular/spec.md`

## Summary
This project implements a computational physics pipeline to test the validity of the Equipartition Theorem in driven granular systems. The system ingests particle tracking data (positions, orientations) and driving signal logs, computes specific energy components (translational, rotational, potential) per particle, and performs rigorous statistical hypothesis testing. The primary test compares the ratio of mean rotational to translational energy against the theoretical value of 1.0. Secondary tests check for Maxwell-Boltzmann distribution shape using the Lilliefors correction to account for parameter estimation. The analysis is stratified by driving frequency (fixed Hz bins) and material type. The pipeline includes sensitivity analyses, power calculations, and linear regression on scale-invariant metrics (excess kurtosis, energy ratios). The entire pipeline is designed to run on CPU-only CI (GitHub Actions) by sampling data where necessary and using `scipy`/`statsmodels` for statistical methods.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `pyyaml`, `tqdm`, `pytest`  
**Storage**: Local CSV/JSON files within `data/` and `artifacts/`; no external database.  
**Testing**: `pytest` (unit tests for energy formulas, integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions runner: Multiple CPU cores, sufficient RAM, no GPU).  
**Project Type**: Computational Research Pipeline / CLI Tool.  
**Performance Goals**: Process sampled dataset (≤1M rows) within 6 hours; memory usage < 6 GB.  
**Constraints**: No GPU; no heavy deep learning; data must be sampled if raw size > 14 GB disk; all random seeds pinned.  
**Scale/Scope**: Single dataset ingestion, multi-frequency analysis, regression modeling.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on `constitution.md`*

| Principle | Status | Evidence/Plan Element |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `requirements.txt` will pin versions. `code/` will include `random.seed()` calls. Data fetching logic will be deterministic. |
| **II. Verified Accuracy** | **PASS** | The **Reference-Validator Agent** will run as a blocking gate before any citation is accepted into the paper. `research.md` will cite only verified dataset URLs (or explicitly note synthetic data). |
| **III. Data Hygiene** | **PASS** | A dedicated `checksum_raw_data.py` script will generate SHA-256 checksums for all files in `data/raw/` immediately upon ingestion. These hashes will be recorded in the `state/...yaml` map before any processing occurs. Derived files in `data/derived/` will also be checksummed. |
| **IV. Single Source of Truth** | **PASS** | Figures/Stats in `paper/` will be generated directly from `artifacts/` outputs (JSON/CSV) via scripts, not hand-typed. |
| **V. Versioning Discipline** | **PASS** | A `hash_artifacts.py` script will generate content hashes for all derived files and update the `state/...yaml` `artifact_hashes` map automatically after each pipeline run. |
| **VI. Granular Energy Component Isolation** | **PASS** | `code/energy.py` will explicitly compute $E_{trans}$, $E_{rot}$, $E_{pot}$ separately. The `stats.py` module will consume the *separate* columns from `energy_samples.csv` directly for testing, ensuring no aggregation occurs prior to analysis. |
| **VII. Frequency-Binned Statistical Validation** | **PASS** | `code/stats.py` will implement binning logic using **fixed frequency intervals** as mandated by the Constitution. Tests will be stratified by material type. |

## Project Structure

### Documentation (this feature)
```text
specs/001-validity-equipartition-granular/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── energy_output.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)
```text
projects/001-validity-equipartition-granular/
├── code/
│   ├── __init__.py
│   ├── config.py          # Load YAML configs (masses, frequencies)
│   ├── ingestion.py       # FR-001, FR-002: CSV parsing, sync, energy calc
│   ├── stats.py           # FR-003, FR-004, FR-006: KS (Lilliefors), Chi-sq, FDR
│   ├── regression.py      # FR-007, FR-008: Linear regression on kurtosis/ratios
│   ├── sensitivity.py     # FR-005: Threshold sweeps
│   ├── checksum_raw_data.py # III: Checksum generation
│   ├── hash_artifacts.py  # V: Hash generation and state update
│   └── main.py            # Orchestration script
├── data/
│   ├── raw/               # Downloaded raw CSVs (checksummed)
│   ├── derived/           # Computed energy dataframes
│   └── config.yaml        # Material properties, frequency bins
├── artifacts/             # Test results, plots, regression outputs
├── tests/
│   ├── test_energy.py     # Unit tests for formulas
│   └── test_stats.py      # Unit tests for statistical logic
├── requirements.txt       # Pinned dependencies
└── README.md              # Project overview
```

**Structure Decision**: Single-project structure selected to minimize overhead. All logic is encapsulated in `code/` modules. Data is strictly separated into `raw` (immutable) and `derived` (computed). This aligns with Constitution Principle III (Data Hygiene) and Principle VI (Energy Isolation).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **None** | The scope is well-defined by the spec. The statistical methods (Lilliefors, Regression on kurtosis) are standard and CPU-tractable. | N/A |
