# Implementation Plan: Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection

**Branch**: `PROJ-372-assessing-sensitivity` | **Date**: 2026-08-16 | **Spec**: [link]
**Input**: Feature specification from `specs/PROJ-372/spec.md`

## Summary

This project implements a statistical pipeline to quantify the stability of OLS regression coefficients under random dataset subset selection. The system ingests verified numerical datasets, profiles them for OLS assumption violations (heteroscedasticity, multicollinearity, outliers), generates multiple random subsets across five specific sample size tiers (loaded from `config.yaml`), fits OLS models, and computes the empirical standard deviation of coefficients. A meta-analysis then correlates coefficient instability with **subset-specific** violation metrics and condition numbers, controlling for sample size. The implementation adheres strictly to the "Real Data Only" constraint, streaming large datasets and running on CPU-only infrastructure.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `pyyaml`, `pytest`, `pre-commit`, `datasets` (HuggingFace)  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `artifacts/...`), JSON/Parquet for artifacts  
**Testing**: `pytest` (unit and integration), `pre-commit` hooks for linting/formatting  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, 7GB RAM)  
**Project Type**: Data Science Pipeline / Statistical Library  
**Performance Goals**: Process datasets up to 7GB via streaming; complete 1000+ OLS fits within 6h job limit; memory usage < 6GB.  
**Constraints**: No synthetic data; no GPU unless CPU-tractable methods fail; strict reproducibility via pinned seeds; tiers loaded from config.

> **Note on Tier Configuration & FR-US2 Traceability**: The spec's `spec.md` section "Sample Size Tiers" in US2 lists `[deferred]`, while the "Research Design Parameters" section explicitly defines them as `[10, 25, 50, 75, 90]`. This plan resolves the ambiguity by explicitly mapping the FR-US2 requirement to the "Research Design Parameters" section. The implementation **will NOT hardcode** these values in the code. They are loaded dynamically from `config.yaml` at runtime. **Task T023 description has been updated to refer strictly to the config source**, removing any hardcoded list from the task text to prevent developer confusion. The plan explicitly states that the '[deferred]' markers in US2 are resolved by the 'Research Design Parameters' section.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Action / Reference |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | `requirements.txt` will pin versions. `random_seed` will be set in `config.yaml` and loaded in `src/utils/random_state.py`. All datasets fetched via `datasets.load_dataset` with verified URLs. |
| **II. Verified Accuracy** | **Pass** | All dataset URLs will be cross-referenced against the `# Verified datasets` block in the user message. No external citations added without verification. |
| **III. Data Hygiene** | **Pass** | Raw data downloaded to `data/raw` with checksums recorded in `state/...yaml`. Derived data (profiles, subsets) written to `data/processed` and `artifacts/`. No in-place modification. |
| **IV. Single Source of Truth** | **Pass** | All figures and statistics in the final report will be generated programmatically from `artifacts/stability/` and `artifacts/meta_analysis/` JSON files. No hand-typed numbers. |
| **V. Versioning Discipline** | **Pass** | Artifacts will include content hashes. `state/...yaml` updated on artifact generation. |
| **VI. Empirical Validation** | **Pass** | `src/ingestion/profile.py` will compute Condition Number, Breusch-Pagan, and **Cook's Distance**. `src/analysis/meta.py` will explicitly regress stability metrics against **Subset-Specific Condition Number, Subset-Specific BP p-value, and Subset-Specific Cook's Distance** (computed per subset) alongside the Tier (log(N)). The Full-Dataset metrics will be used as random intercepts to control for baseline quality. |
| **VII. Non-Circular Derivation** | **Pass** | **Design Anchor**: Violation metrics for the meta-analysis are computed **ONCE per SUBSET** in `src/analysis/ols_runner.py` (Subset-Specific CondNum, BP, Cook's). The Full-Dataset metrics are computed **ONCE on the full dataset** in `src/ingestion/profile.py` and stored as a random intercept. The Stability Result (SD of coefficients) is computed on **random subsets**. The meta-analysis regresses the subset-based metric against the subset-based violation metric. This ensures the predictor (violation) is derived from the same subset as the outcome, avoiding circularity with the full dataset while isolating subset-selection effects. |

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-372-assessing-sensitivity/
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
├── config.py            # Loads config.yaml, handles tier parsing
├── ingestion/
│   ├── __init__.py      # [T001a] - Module initialization
│   ├── loader.py        # HuggingFace/UCI loading with streaming
│   └── profile.py       # OLS violation profiling (BP, Cook's, CondNum) on FULL dataset
├── resampling/
│   ├── __init__.py      # [T001b] - Module initialization
│   ├── generator.py     # Random subset generation (per tier)
│   └── splitter.py      # Tier-based stratification logic
├── analysis/
│   ├── __init__.py      # [T001c] - Module initialization
│   ├── ols_runner.py    # OLS fitting on subsets; computes Subset-Specific CondNum, BP, Cook's
│   ├── stability.py     # SD calculation & Bootstrap Convergence check
│   └── meta.py          # Meta-analysis regression (HLM with Subset-Specific predictors)
├── visualization/       # [NEW] - Visualization module
│   ├── __init__.py      # [T001f] - Module initialization
│   └── curves.py        # Generates Stability Curves (SD vs CondNum)
├── utils/
│   ├── __init__.py      # [T001d] - Module initialization
│   ├── random_state.py  # Seed management
│   └── io.py            # JSON/Parquet I/O helpers
└── cli/
    └── main.py          # Entry point

tests/
├── __init__.py
├── unit/
│   ├── __init__.py      # [T001e] - Module initialization
│   ├── test_loader.py
│   ├── test_profile.py
│   └── test_stability.py
└── integration/
│   ├── __init__.py      # [T001e] - Module initialization
│   └── test_pipeline.py

data/
├── raw/                 # [T004a] - Raw downloaded data
│   └── .gitkeep         # [T004c]
├── processed/           # [T004a] - Processed data
│   └── .gitkeep         # [T004c]
└── .gitkeep             # [T004c]

artifacts/
├── profiles/            # [T004a] - DatasetProfile JSON (Full Dataset)
│   └── .gitkeep         # [T004c]
├── stability/           # [T004a]
│   ├── subsets_*.json   # [T047] - Multiple JSON files per tier (T047)
│   ├── coefficient_sd.json # [T048] - Aggregated SD (T048)
│   └── convergence.log  # [T050, T036] - SE of SD logs (T050, T036)
├── meta_analysis/       # [T004a] - Meta-analysis results
│   └── .gitkeep         # [T004c]
├── visualizations/      # [NEW] - Generated plots
│   └── .gitkeep         # [T004c]
└── checkpoints/         # [T004a]
    └── .gitkeep         # [T004c]

pre-commit-config.yaml   # [T003c]
```

**Structure Decision**: Selected the "Single Project" structure with a modular `src/` layout. This aligns with the Python data science standard (e.g., cookiecutter-data-science) and ensures clear separation of concerns for ingestion, resampling, and analysis. The directory structure explicitly includes `__init__.py` files to satisfy task requirements [T001a-e] and `.gitkeep` files for empty directories [T004c]. A new `src/visualization/` module is added to explicitly handle the FR-US3 visualization requirement.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Streaming Architecture** | Datasets may exceed 7GB RAM. | Loading full datasets into memory would crash the GitHub Actions runner (7GB limit). Streaming is mandatory for "Real Data Only" constraint on large files. |
| **Bootstrap Convergence Loop** | Must verify SE of SD < 5% without assuming Normality. | The Normal approximation (SD / sqrt(2N)) is invalid for heavy-tailed distributions. Bootstrap resampling of the estimates is required for robust SE estimation. |
| **Hierarchical Meta-Analysis** | Must link violation severity to stability across datasets while controlling for sample size and baseline quality. | Simple regression confounds dataset identity with violation severity and sample size. A pooled regression with dataset random intercepts and continuous log(N) control is required to isolate the effect of subset-specific violations. |
| **Subset-Specific Predictors** | To avoid tautology (Full CondNum ~ Subset Stability). | Using Full Dataset CondNum as a predictor for Subset Stability is circular. The analysis must use CondNum computed **per subset** to isolate the effect of subset selection on stability. |

## Compute Feasibility & Data Strategy

- **CPU-First**: OLS regression on subsets is computationally light. `statsmodels` or `scikit-learn` on CPU is sufficient. No GPU is required for this specific statistical method.
- **Data Streaming**: `datasets.load_dataset(..., streaming=True)` will be used for HuggingFace datasets to avoid OOM errors.
- **Tier Configuration**: The sample size tiers `[10, 25, 50, 75, 90]` are defined in `Research Design Parameters` in `spec.md`. The code will load these from a `config.yaml` file to avoid hardcoding, resolving the ambiguity in T023.

## Task List (Selected)

- **T001a**: Initialize `src/ingestion/` with `__init__.py`.
- **T001b**: Initialize `src/resampling/` with `__init__.py`.
- **T001c**: Initialize `src/analysis/` with `__init__.py`.
- **T001d**: Initialize `src/utils/` with `__init__.py`.
- **T001e**: Initialize `tests/unit/` and `tests/integration/` with `__init__.py`.
- **T003c**: Create `pre-commit-config.yaml`.
- **T004a**: Create directory structure (`data/raw`, `data/processed`, `artifacts/...`).
- **T004c**: Add `.gitkeep` to all empty directories.
- **T023**: **Generate random subsets per dataset across tiers defined in `config.yaml` (NOT hardcoded).** The system must read tier percentages from `config.yaml` and generate multiple subsets per tier.
- **T047**: Generate a set of `subsets_*.json` files per tier containing subset-specific metrics.
- **T048**: Generate `coefficient_sd.json` with aggregated SD per tier.
- **T049**: Implement comparison logic for coefficient SDs across subsets.
- **T050**: Generate `convergence.log` with SE of SD calculations.
- **T036**: Verify and log that SE of SD < 5% threshold.