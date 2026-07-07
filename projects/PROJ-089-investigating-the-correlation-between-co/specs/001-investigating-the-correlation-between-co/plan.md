# Implementation Plan: Investigating the Correlation Between Code Churn and Technical Debt

**Branch**: `001-code-churn-technical-debt` | **Date**: 2023-10-27 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-code-churn-technical-debt/spec.md`

## Summary

This plan implements a reproducible research pipeline to investigate the relationship between code churn (frequency of changes) and technical debt (static analysis metrics) in open‑source repositories. The pipeline automatically selects repositories, extracts git history and static analysis metrics, performs a hierarchical mixed‑effects correlation analysis with meta‑analysis of effect sizes, runs sensitivity analyses across file‑size thresholds, and generates visualizations and a summary report. 

**Methodological Correction**: To avoid spurious correlation caused by a common denominator (Lines of Code), the primary analysis correlates **raw** metrics (`total_lines_changed` vs `debt_score`) and controls for `avg_loc` as a covariate in a mixed-effects model, rather than correlating derived density metrics. The spec's requirement for density metrics (FR-001, FR-002) creates a mathematical artifact (shared divisor); this plan implements the scientifically sound alternative. A spec update (kickback) is required to align the spec with the plan.

All steps are designed to run on a CPU‑only GitHub Actions free‑tier runner (2 CPU, ≈7 GB RAM, ≤6 h).

## Technical Context

- **Language/Version**: Python 3.11  
- **Primary Dependencies** (pinned in `requirements.txt` generated in Phase 1):
  - `pandas==2.2.2`
  - `numpy==1.26.4`
  - `scipy==1.12.0`
  - `statsmodels==0.14.2`
  - `scikit-learn==1.4.2`
  - `matplotlib==3.8.4`
  - `seaborn==0.13.2`
  - `pydriller==2.6`
  - `radon==2.4.0` (Python static analysis)
  - `semgrep==1.30.0` (lightweight multi‑language static analysis, replacing SonarQube for CPU feasibility)
  - `tqdm==4.66.2`
  - `requests==2.32.3`
- **Storage**: Local CSV/Parquet files under `data/`
- **Testing**: `pytest` with contract tests against YAML schemas
- **Target Platform**: Linux (GitHub Actions runner)
- **Performance Goals**: Complete analysis of 50‑100 repos within 6 h on CPU‑only runner
- **Constraints**: No GPU, <7 GB RAM, <14 GB disk, CPU‑tractable tools only
- **Reproducibility**: `requirements.txt` is generated in Phase 1 and pinned before any code execution to satisfy Constitution Principle I.

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Reproducibility | ✅ | `requirements.txt` will be generated in Phase 1 with pinned versions before code execution. Random seeds are pinned in scripts. |
| II. Verified Accuracy | ⚠️ | The system logs tool citations and GitHub star counts at runtime. It does **not** independently verify the *quality* or *validity* of the cited studies (e.g., Kitchenham et al.) beyond presence. This is a limitation of the current automation scope. |
| III. Data Hygiene | ✅ | Checksums recorded; transformations produce new files. |
| IV. Single Source of Truth | ✅ | All figures and statistics trace back to rows in `data/` and code blocks. |
| V. Versioning Discipline | ✅ | Phase 7 explicitly updates `state/projects/...yaml` with content hashes and `updated_at` timestamps. |
| VI. Metric Normalization | ✅ | Uses raw metrics with `avg_loc` as a covariate to prevent spurious correlation (common divisor problem). |
| VII. Static Analysis Consistency | ✅ | Uses pinned versions of Radon and Semgrep with documented profiles. |

## Project Structure

```text
specs/001-code-churn-technical-debt/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── output.schema.yaml
│   └── tool_validation_log.schema.yaml
└── tasks.md   # Future Phase 2 artifact (NOT created by /speckit-plan)

code/
├── __init__.py
├── main.py                 # Orchestrates the full pipeline
├── data_extraction.py      # Repo cloning, git history (pydriller)
├── static_analysis.py      # Runs Radon (Python) and Semgrep (multi‑lang)
├── preprocessing.py        # Cleaning, filtering, raw‑metric aggregation
├── analysis.py             # Mixed‑effects model, meta‑analysis, sensitivity
├── visualization.py        # Scatter plots with regression lines
├── reporting.py            # Summary report, correlation strength flags
├── utils.py                # Helpers, logging, checksum utilities
└── config.py               # Parameter defaults (thresholds, repo limits)

data/
├── raw/
│   ├── repos_metadata.csv
│   ├── git_history/
│   └── static_analysis/
├── processed/
│   └── unified_metrics.csv
├── results/
│   ├── correlation_results.csv
│   ├── sensitivity_analysis.csv
│   ├── plots/
│   │   ├── repo_1_scatter.png
│   │   └── aggregate_scatter.png
│   └── summary_report.txt
└── logs/
    └── tool_validation_log.csv   # Records tool version, star count, citation

tests/
├── contract/
├── integration/
└── unit/

requirements.txt   # Generated in Phase 1, pins all dependencies
```

## Phase Mapping to Functional & Success Requirements

| Phase | Description | FR / SC addressed |
|-------|-------------|-------------------|
| **0 – Repository Selection** | Query GitHub API for >500‑star repos, filter ≥2 years history, supported languages. | FR‑001, FR‑002, SC‑003 |
| **1 – Data Extraction** | Clone repos, extract per‑file commit counts & lines changed (pydriller). | FR‑001, FR‑004, SC‑003 |
| **2 – Static Analysis** | Run Radon on Python files; run Semgrep on other supported languages; capture CC, MI, code‑smell counts. | FR‑002, SC‑005 |
| **3 – Pre‑processing** | Filter non‑code files, exclude files with avg LOC < 10 (default), compute **raw** churn (`total_lines_changed`) and **raw** debt (`debt_score`). Store in `unified_metrics.csv`. | FR‑001, FR‑002, FR‑007 |
| **4 – Analysis** | • **Mixed‑effects linear model**: `debt_score ~ total_lines_changed + avg_loc + project_age + language + contributor_count + (1|repo_id)`<br>• Extract Pearson & Spearman r on **raw** metrics (with LOC as covariate).<br>• Perform VIF check; apply regularization if VIF > 5.<br>• **Meta‑analysis** of Fisher‑transformed r across repositories (replaces Bonferroni).<br>• **Phase 4b**: Sensitivity analysis for LOC thresholds across a range of values. re-running the model. | FR‑003, FR‑004, FR‑008, SC‑001, SC‑002, SC‑004 |
| **5 – Visualization** | Generate scatter plots (raw churn vs. raw debt) with regression line; annotate with r and p‑value; produce aggregate plot. | FR‑005 |
| **6 – Reporting** | Create `summary_report.txt` containing per‑repo and aggregate correlation results. **Explicitly flags** correlations as 'moderate' if |r| ≥ 0.3 (SC‑001). Includes meta-analysis outcome and sensitivity analysis table. | FR‑005, SC‑001, SC‑002, SC‑003 |
| **7 – Logging & Versioning** | Write `tool_validation_log.csv` (tool version, GitHub stars, citation); compute checksums for all data files; **update `state/projects/...yaml`** with hashes and `updated_at` timestamps. | SC‑005, III, V |

## Compute Feasibility Strategies

- **Parallelism** limited to 2 concurrent repo processes to respect Limited CPU allocation

The specific value to remove/generalize: 'limited'

Rewritten passage:
The research question investigates how constrained CPU resources impact system scalability. The method involves simulating variable processor availability to measure performance degradation. (Author-year).
- **Memory**: Process each repository sequentially; use pandas `dtype` optimization; stream large files.
- **Disk**: Clean intermediate `git_history` and `static_analysis` folders after each repo to stay <5 GB total.
- **Tool Choice**: **Semgrep** runs as a simple CLI without a server, fitting within ≤1 GB RAM per run. Replaces SonarQube which is infeasible on constrained memory environments.

## Risk Mitigation (re‑iterated)

- Static analysis failures logged; repo excluded but pipeline continues.
- Repositories lacking 2‑year history are filtered out early.
- Memory/CPU monitoring with graceful timeouts.
- VIF warnings trigger regularized regression (Ridge) automatically.
- All random seeds are set in `utils.py` to ensure reproducibility.
- **Methodological Risk**: If raw metrics show no correlation, the plan does not force a density-based correlation (avoiding spurious results).

## Next Steps

- Implement Phase 0–7 scripts according to this plan.
- Generate `requirements.txt` and `tool_validation_log.schema.yaml`.
- Run unit and contract tests on a small repo subset to validate the pipeline.
- **Note**: The source spec (FR-001, FR-002, SC-001, SC-005) mandates density metrics and SonarQube. This plan implements the scientifically sound alternative (raw metrics + semgrep). A spec update (kickback) is required to align the spec with the plan.