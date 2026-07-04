# Implementation Plan: Quantifying the Impact of Code Ownership on Software Quality

**Branch**: `001-code-ownership-analysis` | **Date**: 2024-01-15 | **Spec**: `specs/001-code-ownership-analysis/spec.md`

## Summary

This plan implements an observational study to quantify the correlation between **Recent Ownership Concentration** (Gini coefficient of the last several thousand commits) and **Explicitly Linked Bug Density** (issues mentioning file paths) in large-scale open-source projects. The approach involves cloning high-activity GitHub repositories with shallow history, extracting ownership and bug data via a path-based proximity heuristic, and performing robust statistical analysis (Spearman correlation, Likelihood Ratio Test for non-linearity, VIF diagnostics on linear terms) on a CPU-only environment.

**Key Limitations**:
1.  **Metric Definition**: "Bug Density" is a proxy for "Explicitly Linked Bugs" due to the path-based heuristic. Results are conditional on this linkage.
2.  **Temporal Scope**: Gini coefficients reflect recent ownership (last few years) due to shallow cloning, not historical structure.
3.  **Causality**: Findings are strictly associational.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `GitPython`, `scikit-learn`, `scipy`, `pandas`, `numpy`, `radon`, `matplotlib`, `pyyaml`  
**Storage**: Local filesystem (intermediate CSVs), GitHub API (read-only)  
**Testing**: `pytest` (contract and unit tests)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7 GB RAM)  
**Project Type**: Data analysis pipeline / CLI  
**Performance Goals**: Total runtime ≤6 hours; Peak RAM ≤7 GB; Disk usage ≤14 GB  
**Constraints**: No GPU; Shallow clone depth; Exponential backoff for API rate limits; Observational framing only.  
**Scale/Scope**: A set of repositories; A substantial number of commits per repo; File-level granularity.

## Constitution Check

| Principle | Status | Evidence / Plan Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates `requirements.txt` pinning; `code/` scripts run end-to-end; Random seeds pinned in `research.md` logic. |
| **II. Verified Accuracy** | **PASS** | Dataset references restricted to verified sources; Cite validation for `radon` and `scipy`; No unverified URLs in `research.md`. |
| **III. Data Hygiene** | **PASS** | Intermediate CSVs written to `data/` with checksums; Raw git data preserved; No PII in outputs. |
| **IV. Single Source of Truth** | **PASS** | All stats in `code/results/` JSON; Paper references trace to these files. |
| **V. Versioning Discipline** | **PASS** | Artifacts hashed in `state/`; `updated_at` timestamps managed by agent. Raw ownership attribution CSVs in `data/intermediate/` are hashed and recorded in `state/...yaml` to satisfy versioning without bloating Git history. |
| **VI. Ownership Metric Transparency** | **PASS** | Gini computed from `git clone --depth <specified_limit>` (per Spec FR-001, superseding Constitution draft typo of "100"); Raw attribution CSVs version-controlled via content hashing in `state/`. |
| **VII. Statistical Rigor** | **PASS** | Spearman correlation with CI; VIF on linear terms only; LRT for non-linearity; Multiple-comparison correction; Sensitivity analysis included; Primary reporting threshold aligned with Constitution (|ρ| > 0.3, p < 0.05). |

## Project Structure

### Documentation (this feature)

```text
specs/001-code-ownership-analysis/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-062-quantifying-the-impact-of-code-ownership/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data_collection.py      # FR-001, FR-006, FR-014
│   ├── metrics_calc.py         # FR-002, FR-003, FR-008, FR-009
│   ├── statistical_analysis.py # FR-004, FR-010, FR-011, FR-012, FR-013, FR-015, FR-016
│   ├── visualizations.py       # FR-005
│   └── main.py                 # Orchestration
├── data/
│   ├── raw/                    # Cloned repos (shallow)
│   ├── intermediate/           # CSVs (ownership, bugs, metrics)
│   └── results/                # JSON summaries, PNG plots
├── tests/
│   ├── contract/               # Schema validation
│   ├── integration/            # End-to-end pipeline
│   └── unit/                   # Metric calculation logic
└── docs/
    └── README.md
```

**Structure Decision**: Single-project structure selected. The `code/` directory contains the analysis pipeline. `data/` is split into `raw` (immutable), `intermediate` (derived), and `results` (final outputs) to satisfy Data Hygiene (Principle III).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Shallow Clone + Depth** | Required for FR-001 to limit disk/RAM while ensuring sufficient history for Gini. | Full clone exceeds GB disk and 6h time limit for large repos. |
| **Path-Based Proximity Heuristic** | Required by FR-009 to link bugs to modules without API circularity. | Assignee-based linking (removed in spec) creates circular validation; full NLP is too heavy for CPU-only. |
| **Quadratic Regression (Gini²)** | Required by FR-016 to test non-linearity. | Linear-only model fails to capture potential U-shaped ownership effects. |
| **Sensitivity Analysis (Sweeps)** | Required by FR-012 and FR-015 to validate robustness of thresholds. | Single-threshold reporting is fragile and violates SC-008/SC-011. |
| **LRT for Non-Linearity** | Required to avoid invalid VIF on collinear Gini/Gini². | Standard VIF on Gini+Gini² is mathematically infinite; LRT provides valid model comparison. |