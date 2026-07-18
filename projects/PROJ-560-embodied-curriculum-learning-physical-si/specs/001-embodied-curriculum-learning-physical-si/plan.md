# Implementation Plan: Embodied Curriculum Learning: Physical Simulation for Abstract Concept Teaching

**Branch**: `001-embodied-curriculum-learning` | **Date**: 2026-06-02 | **Spec**: `spec.md`
**Input**: Feature specification for secondary analysis of educational datasets and synthetic data generation for validating embodied vs. static instruction effects.

## Summary

This feature implements a CPU-tractable statistical analysis pipeline to investigate the **association** between embodied training (physics-based virtual manipulation) and transfer to abstract mathematical reasoning, compared to static visual instruction. The system operates in two distinct modes with different methodological scopes:

1.  **Secondary Analysis Mode**: Processes existing public educational datasets with `instruction_type` labels. **Crucially**, this mode is strictly observational. It can only identify *associations*, not causal *improvement*, due to the lack of randomization in public data.
2.  **Synthetic Generation Mode**: Creates controlled datasets with known ground truths. This mode is used **solely for pipeline validation** (verifying code correctness and statistical engine accuracy) and **not** for validating the research hypothesis or the phenomenon of embodied learning.

The core output is a JSON report containing ANCOVA results (primary), t-test results (secondary descriptive), effect sizes, power analysis, and sensitivity sweeps, strictly framed as associational.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scipy`, `statsmodels`, `numpy`, `pyyaml`, `json`  
**Storage**: Local CSV/Parquet files (read-only for public data, generated for synthetic); JSON output.  
**Testing**: `pytest` (unit tests for data loaders, statistical functions; integration tests for end-to-end pipeline).  
**Target Platform**: Linux (GitHub Actions free-tier: standard CPU allocation, 7GB RAM, no GPU).  
**Project Type**: CLI tool / Data Analysis Library  
**Performance Goals**: < 10 minutes runtime for N=10,000 dataset; < 500MB RAM usage.  
**Constraints**: No GPU usage; no external API calls during execution (except initial dataset fetch if permitted, otherwise local cache); strict adherence to `instruction_type` variable presence.  
**Scale/Scope**: Single dataset processing per run; support for multiple concepts (columns) requiring Bonferroni correction.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds (numpy, python) pinned in `code/`. Dependencies pinned in `requirements.txt`. |
| **II. Verified Accuracy** | **PASS** | Dataset URLs cited strictly from the `# Verified datasets` block in `research.md`. The Reference-Validator Agent will be integrated into the CI pipeline to verify these URLs before execution. |
| **III. Data Hygiene** | **PASS** | Raw data preserved; derivations written to new files with checksums recorded in `state/projects/PROJ-560-embodied-curriculum-learning-physical-si/artifact_hashes.yaml`. |
| **IV. Single Source of Truth** | **PASS** | All statistics in `paper/` derived from `data/` JSON outputs; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Content hashes for all artifacts; `updated_at` timestamps managed by Advancement-Evaluator. |
| **VI. Simulation-Pedagogy Alignment** | **PASS (Conditional)** | This principle applies **only** to the Synthetic Data Generation mode, where the system generates a `mapping_log` linking physics parameters to math concepts. **Secondary Analysis Mode is explicitly exempt** as public datasets are observational and static, lacking the required physics-to-math derivation logs. |
| **VII. Secondary Data Provenance** | **PASS** | Public dataset condition labels preserved; filtering logs generated in `data/derivation_logs/`. The `skipped_records.log` will be stored in this directory and will contain the required derivation details to prevent selection bias. |

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-560-embodied-curriculum-learning-physical-si/
├── code/
│   ├── requirements.txt
│   ├── src/
│   │   ├── __init__.py
│   │   ├── data_loader.py       # FR-001, FR-008: Load public/synthetic data
│   │   ├── synthetic_gen.py     # FR-009: Generate synthetic datasets
│   │   ├── stats_engine.py      # FR-002, FR-003, FR-004, FR-006, FR-007 (ANCOVA + t-test)
│   │   ├── sensitivity.py       # FR-005: Threshold sweep
│   │   └── cli.py               # Main entry point
│   └── tests/
│       ├── test_data_loader.py
│       ├── test_stats_engine.py
│       └── test_synthetic_gen.py
├── data/
│   ├── raw/                     # Public datasets (cached)
│   ├── processed/               # Derived CSVs with gain scores
│   ├── synthetic/               # Generated datasets for validation
│   └── derivation_logs/         # Logs for skipped records and data transformations
└── state/
    └── projects/PROJ-560-.../
        └── artifact_hashes.yaml
```

**Structure Decision**: Single project structure selected. The feature is a CLI-driven analysis tool, not a web service or mobile app. The `code/src` directory houses modular logic for data loading, synthetic generation, statistical testing, and sensitivity analysis, allowing for easy unit testing and reproducibility.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Synthetic Data Generator** | Required by FR-009 to validate the pipeline when public data lacks `instruction_type`. | Relying solely on public data risks pipeline failure if labels are missing; synthetic data provides a "ground truth" control for code correctness. |
| **Sensitivity Sweep** | Required by FR-005 to ensure robustness against arbitrary threshold choices. | A single threshold analysis is methodologically weak and fails to demonstrate stability of the effect size. |
| **Collinearity Detection** | Required by FR-006 to prevent misinterpretation of independent effects. | Running multivariate regression without checking correlation leads to spurious causal claims in observational data. |
| **ANCOVA over Gain Scores** | Required to address regression to the mean and baseline dependency in observational data. | Gain scores are statistically invalid for comparing groups with different baseline distributions; ANCOVA is the robust alternative. |