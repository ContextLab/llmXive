# Project Plan: Investigating the Correlation Between Code Churn and Technical Debt

## Summary

This study uses **Raw Metrics** (`total_lines_changed`, `debt_score`) as the primary analysis, with `avg_loc` as a covariate in a Log-Log Linear Model, strictly adhering to Spec FR-001. The methodology explicitly avoids "Density Metrics" to prevent spurious correlations identified in prior literature. We employ Semgrep (v1.30.0) for static analysis, ensuring CPU-only feasibility and multi-language support, as mandated by the Spec's Methodological Correction.

## Objectives

1. Quantify the correlation between raw code churn and technical debt.
2. Control for file size (`avg_loc`) and contributor count to isolate the effect.
3. Perform sensitivity analysis on file size thresholds (5, 10, 20 LOC).
4. Aggregate results via Fisher-transformed meta-analysis.

## Methodology

### Data Acquisition
- **Source**: Public GitHub repositories selected via a pinned list (`data/raw/repos_metadata.csv`).
- **Churn**: Calculated using `pydriller` on the last 12 months of git history (Total Lines Changed = Additions + Deletions).
- **Debt**: Calculated using `semgrep==1.30.0` (Cyclomatic Complexity + Maintainability Index gap for Python; Code Smells + Complexity for other languages).
- **Covariates**: `avg_loc` (average lines of code per file), `contributor_count`.

### Statistical Analysis
- **Primary**: Pearson and Spearman correlation on raw metrics, controlling for `avg_loc`.
- **Meta-Analysis**: Fisher's Z transformation of per-repo correlation coefficients, aggregated via inverse-variance weighting.
- **Sensitivity**: Re-running analysis on subsets filtered by `avg_loc >= threshold` (thresholds: 5, 10, 20).
- **VIF Check**: Variance Inflation Factor check on covariates; if VIF > 5, Ridge regression is considered (though not the primary output).

## Data Integrity & Reproducibility

- **Real Data Only**: The pipeline strictly fetches real data from public repositories. No synthetic data generation or fallbacks are permitted.
- **Fail Loudly**: If a repository clone fails or a tool is unavailable, the pipeline aborts with a clear error to prevent silent fabrication.
- **Versioning**: All artifacts are checksummed and logged in `data/logs/pipeline.log` and `data/logs/spec_verification.log`.

## Methodological Correction

The initial plan narrative contained contradictions regarding the use of "Density Metrics" and "SonarQube". This plan has been corrected to align with the Spec:
- **Metrics**: Switched from Density to **Raw Metrics** (`total_lines_changed`, `debt_score`) to align with Spec FR-001 and avoid spurious correlation.
- **Tooling**: Switched from SonarQube to **Semgrep** (v1.30.0) to ensure CPU-only feasibility and compliance with Spec SC-005.
- **Statistical Method**: Replaced Bonferroni correction with **Meta-analysis** of Fisher-transformed coefficients per Spec FR-006.

## Constitution Exception

To resolve the divergence between the initial Plan and the Spec's mandate for Raw Metrics/Semgrep, the following Constitution Exception is documented:
- **Princip VI (Use Standard Tools)**: Exception granted to use Semgrep (v1.30.0) instead of the initially proposed SonarQube, as SonarQube is not feasible in the target CI environment.
- **Principle VII (Avoid Spurious Correlation)**: Exception granted to use Raw Metrics instead of Density Metrics, as mandated by the Spec's Methodological Correction.

| Principle | Exception | Resolution |
|:--- |:--- |:--- |
| VI | SonarQube -> Semgrep | Spec mandates Semgrep for feasibility. |
| VII | Density -> Raw Metrics | Spec mandates Raw Metrics to avoid spurious correlation. |

## Execution

1. **Setup**: Run `python code/setup_dirs.py` and `python code/setup_linting.py`.
2. **Verification**: Run `python code/spec_verification.py` to confirm alignment.
3. **Pipeline**: Run `python code/main.py`.
4. **Output**: `data/results/summary_report.txt`, `data/results/plots/`, `data/processed/unified_metrics.csv`.

## Next Steps

- Ensure `data/raw/repos_metadata.csv` is populated with real, reachable repositories.
- Verify `semgrep` installation and rule configuration.
- Execute the pipeline on the full dataset.