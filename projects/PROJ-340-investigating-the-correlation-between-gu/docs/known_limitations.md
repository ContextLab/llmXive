# Known Limitations

This document outlines the current limitations and constraints of the PROJ-340 pipeline.

## 1. Data Source Requirements
- **Real Data Only**: The production pipeline strictly requires a verified real data source. It will not fall back to synthetic data. If `data/config/real_data_sources.yaml` is misconfigured or the URL is unreachable, the pipeline will fail with a `RealDataFetchError`.
- **Data Format**: Input data must be in CSV or TSV format with specific column requirements defined in `data/config/required_variables.yaml`.

## 2. Computational Constraints
- **Execution Time**: The pipeline includes a hard 6-hour timeout for CI environments. Large datasets may exceed this limit. Users are advised to sample data or use high-performance computing resources for full-scale runs.
- **Memory Usage**: The current implementation loads the entire dataset into memory. For datasets >10GB, consider using the streaming stub (future work) or reducing the dataset size.

## 3. Statistical Limitations
- **Power Analysis**: Power calculations are based on observed effect sizes and may be underpowered for small sample sizes (N < 30). The `power_analysis_report.json` will flag "Underpowered" conditions.
- **Correlation vs. Causation**: The pipeline explicitly prevents causal language in reports. Correlations detected are associative only.

## 4. Compositional Data Handling
- **Assumption**: The pipeline assumes microbiome data is compositional (relative abundance). If the sum of abundances deviates significantly from 1, a CLR transformation is applied.
- **Zero-Inflation**: Zero-inflated models (ZINB) are used for highly sparse data (>30% zeros). However, extreme sparsity may lead to convergence issues in the ZINB fitting step.

## 5. Known Bugs & Workarounds
- **Circular Import in Stress Test**: A known circular import exists between `main.py` and `run_stress_test.py` when running stress tests. Avoid running `run_stress_test.py` directly; use the main pipeline with a timeout flag instead.
- **VIF Calculation**: Variance Inflation Factor (VIF) calculation is skipped for definitionally related taxa pairs (parent-child) to avoid perfect multicollinearity errors.

## 6. Future Improvements
- **Streaming Support**: Full support for streaming large datasets without loading them entirely into memory.
- **GPU Acceleration**: Potential integration of GPU-accelerated correlation methods for massive datasets.
- **Interactive Visualization**: Web-based dashboard for exploring correlation matrices and sensitivity analyses.
