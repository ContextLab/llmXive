# Implementation Plan: Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection

**Branch**: `PROJ-372-assessing-the-sensitivity-of-regression-` | **Date**: 2026-08-15
**Spec**: `specs/PROJ-372-assessing-the-sensitivity-of-regression-/spec.md`
**Input**: Feature specification from `/specs/PROJ-372-assessing-the-sensitivity-of-regression-/spec.md`

## Summary

This project implements a statistical analysis pipeline to quantify how OLS regression coefficients fluctuate when fitted on random subsets of data. The system ingests **three** verified numerical datasets from HuggingFace/UCI: **California Housing**, **Delaney Solubility**, and **Wine Quality**. It profiles them for OLS assumption violations (heteroscedasticity, multicollinearity, outliers), generates 200 random subsets across **5 specific sample size tiers ([10, 25, 50, 75, 90] percent)**, fits OLS models to each, and computes the empirical standard deviation of coefficients.

A **stratified stability analysis** (replacing the original meta-analysis regression) estimates the relationship between subset-level violation severity and coefficient stability. Instead of a regression on 3 datasets, we bin subsets by violation severity and compare stability across bins using non-parametric tests. This provides sufficient statistical power (N=200 subsets) to detect trends. The implementation is strictly CPU-first, runs on GitHub Actions free-tier, and uses real, open data only.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `pyyaml`, `pytest`, `pre-commit`, `datasets` (HuggingFace), `matplotlib`, `scipy`  
**Storage**: Local filesystem (`data/`, `artifacts/`) for raw and processed data; JSON artifacts for results; CSV/JSON for stability curves.  
**Testing**: `pytest` (unit tests for ingestion, resampling, and analysis modules; integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions runner: 2 CPU, ~7 GB RAM).  
**Project Type**: Data analysis library / CLI tool.  
**Performance Goals**: Complete full pipeline (ingestion -> 200 subsets x 5 tiers -> stratified analysis) within 6 hours on CPU.  
**Constraints**: No synthetic data; streaming for datasets >7GB (though selected datasets are small); strict reproducibility via pinned seeds; convergence check gates tier inclusion.  
**Scale/Scope**: 3 verified datasets; ~3000 model fits total (200 subsets * 5 tiers * 3 datasets); ~500MB max memory footprint.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: Plan mandates pinned random seeds in `src/utils/seed.py` and deterministic dataset fetching via `datasets.load_dataset`. `requirements.txt` pins all versions.
- **II. Verified Accuracy**: Plan restricts dataset citations to the "Verified datasets" block in the spec. No external URLs will be invented.
- **III. Data Hygiene**: Plan enforces `data/raw` checksums and immutable derivations in `data/processed`. PII scan gate included in CI.
- **IV. Single Source of Truth**: All figures and stats in the final report will be generated from `artifacts/` JSON/CSV files, not hand-typed.
- **V. Versioning**: Content hashes for `data/` and `code/` will be recorded in `state/`.
- **VI. Empirical Validation**: The stratified analysis (US3) explicitly models coefficient stability as a function of **subset-level** Breusch-Pagan p-values, **Condition Numbers**, and **Cook's Distance**, satisfying the requirement to map instability to specific violations.
- **VII. Non-Circular Derivation**: The plan explicitly calculates violation metrics **per subset**. The stability metric (SD) and the predictor metrics (CondNum, BP) are derived from the exact same subset data, ensuring independence from full-dataset properties and eliminating measurement error bias.

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-372-assessing-the-sensitivity-of-regression-/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── ingestion/
│   ├── __init__.py
│   ├── loader.py          # HuggingFace/UCI download logic
│   └── profiler.py        # BP test, Cook's Distance, Cond Num
├── resampling/
│   ├── __init__.py
│   └── generator.py       # Subset generation per tier
├── analysis/
│   ├── __init__.py
│   ├── ols_fitter.py      # Model fitting per subset
│   ├── stability.py       # SD calculation & convergence check
│   └── stratified_analysis.py   # Binning and non-parametric tests
├── utils/
│   ├── __init__.py
│   ├── seeds.py           # Seed management
│   └── io.py              # JSON/Parquet I/O
└── cli.py                 # Entry point

tests/
├── __init__.py
├── unit/
│   ├── __init__.py
│   ├── test_loader.py
│   └── test_stability.py
└── integration/
    ├── __init__.py
    └── test_pipeline.py

data/
├── raw/
├── processed/
└── profiles/

artifacts/
├── profiles/
├── stability/
│   ├── subsets_*.json
│   └── coefficient_sd.json
├── stratified_analysis/
├── figures/               # Stability curves (PNG/CSV)
└── convergence.log

pre-commit-config.yaml
requirements.txt
```

**Structure Decision**: Single project structure selected (Option 1) as the scope is a focused statistical pipeline, not a web service or mobile app. Directories `src/ingestion`, `src/resampling`, `src/analysis`, and `src/utils` are explicitly defined to satisfy T001a-e. `tests/unit` and `tests/integration` are defined to satisfy T001e. `pre-commit-config.yaml` is included to satisfy T003c.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations identified. The project scope fits within a single module structure. | N/A |