# Analysis Protocol: Variable Selection and Statistical Power

## 1. Data Acquisition Protocol

### 1.1 Dataset Selection Criteria
- Source: OpenML repository
- Type: Regression tasks only
- Minimum rows: 100
- Minimum predictors: 3
- Condition number threshold: < 10^10 (to avoid perfect multicollinearity)
- Target count: 10 diverse datasets

### 1.2 Fetching Procedure
1. Use `code/data/downloader.py` with `fetch_datasets()`
2. Implement time-based exponential backoff for API retries
3. Generate SHA-256 checksums for all downloaded files
4. Validate condition numbers and row/column constraints
5. Fail hard if < 10 valid datasets after retries

## 2. Simulation Protocol

### 2.1 Parameters
- SNR levels: Low to moderate (configurable in `code/config.py`)
- Sparsity levels: {0.0, 0.2, 0.4}
- Simulations per condition: Determined by pilot run (T004)
- Random seed: Pinned for reproducibility

### 2.2 Outcome Generation
1. Extract covariance structure from real dataset (X matrix)
2. Generate ground-truth coefficients with specified sparsity
3. Create synthetic Y vectors: Y = Xβ + ε
4. Noise ε scaled to achieve target SNR
5. Record true coefficients for power calculation

### 2.3 Memory Efficiency
- Process simulations in chunks
- Monitor RAM usage via `psutil`
- Abort if > 6.5 GB threshold

## 3. Variable Selection Protocol

### 3.1 Methods Implemented
1. **Forward Stepwise**: AIC criterion with early stopping
2. **Backward Elimination**: AIC criterion
3. **LASSO**: Cross-validated lambda selection

### 3.2 Execution Constraints
- CPU-only execution (no GPU dependencies)
- Early stopping for stepwise if AIC doesn't improve for N steps
- Predictor pruning for highly correlated variables

## 4. Power Calculation Protocol

### 4.1 Definition
Empirical Power = (True Positives) / (Total True Non-Zero Coefficients)

Where:
- True Positive: Coefficient is non-zero AND selected AND p < α
- Denominator: Only true non-zero coefficients (exclude true zeros)

### 4.2 Statistical Significance
- Primary α: 0.05
- Sensitivity analysis: α ∈ {0.01, 0.05, 0.10}
- P-values from refitted OLS on selected variables

### 4.3 Collinearity Diagnostics
- Calculate VIF for all selected models
- Record condition numbers
- Flag extreme multicollinearity

## 5. Statistical Comparison Protocol

### 5.1 Unit of Analysis
- Individual simulation-level rows (n=24,000)
- **NOT** aggregated means

### 5.2 Tests Performed
1. **Kruskal-Wallis**: Non-parametric test for differences across methods
2. **Dunn's Post-Hoc**: Pairwise comparisons with Holm correction
3. **Sensitivity Analysis**: Power rates across α thresholds

### 5.3 Validation
- Assert input dataframe has individual rows before running tests
- Verify schema compliance via contract tests
- Compare summary stats to raw CSV values

## 6. Visualization Protocol

### 6.1 Power Curves
- X-axis: SNR levels
- Y-axis: Power rate
- Facets: Sparsity levels
- Lines: Selection methods (color-coded)
- Separate plots for each α threshold

### 6.2 Output Format
- Save to `results/plots/`
- Formats: PNG (high resolution)
- Consistent styling via seaborn

## 7. Reporting Protocol

### 7.1 Final Report Sections
1. Executive Summary
2. Statistical Results (Kruskal-Wallis, Dunn's test)
3. Power Curves
4. Methodology Notes
5. Sensitivity Analysis

### 7.2 Verification
- Recompute mean power per condition from CSV
- Compare to reported values in summary
- Ensure all plots are generated

## 8. Quality Assurance

### 8.1 Data Hygiene
- SHA-256 checksums for all raw files
- Validation of condition numbers
- Schema validation for processed data

### 8.2 Reproducibility
- Pinned random seeds
- Deterministic file naming
- Checksum comparison for re-runs

### 8.3 Resource Monitoring
- Runtime watchdog (6-hour limit)
- Memory profiling (6.5 GB limit)
- Graceful shutdown with partial results

## 9. Error Handling

### 9.1 Fail-Loudly Principles
- No synthetic fallbacks for missing data
- Hard failures for API timeouts after retries
- Abort if resource limits exceeded

### 9.2 Logging
- All simulation parameters logged per run
- Error stack traces captured
- Performance metrics recorded

## 10. Version Control

- All code changes tracked in git
- Checksums stored in `state/checksums.json`
- Pipeline version recorded in output metadata
