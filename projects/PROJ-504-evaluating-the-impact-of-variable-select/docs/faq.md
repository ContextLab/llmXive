# Frequently Asked Questions

## General

### What is the primary research question?
This project evaluates how variable selection methods (Forward Stepwise, Backward Elimination, LASSO) impact statistical power in linear regression across varying SNR and sparsity levels.

### Why use OpenML datasets?
OpenML provides real-world regression tasks with diverse covariance structures, ensuring the results generalize beyond synthetic data.

## Methodology

### How is "Power" defined here?
Empirical Power = (Number of true non-zero coefficients selected AND significant with p < 0.05) / (Total number of true non-zero coefficients).

### Why use Kruskal-Wallis instead of ANOVA?
Power distributions are often non-normal. Kruskal-Wallis is a non-parametric test that does not assume normality, making it robust for this analysis.

### What is the role of the "watchdog"?
The `watchdog.py` module monitors runtime and memory usage. If the 6-hour runtime limit or 6.5 GB RAM limit is approached, it triggers a graceful shutdown to prevent data loss.

## Technical

### How do I add a new dataset?
Add the OpenML ID to the `openml_ids` list in `code/config.py`. The downloader will fetch and validate it automatically.

### Can I run this on a GPU?
No. The pipeline is CPU-only by design (see `config.py` constraints). GPU acceleration is not supported for these specific statistical operations.

### What if the pipeline fails mid-run?
Partial results are saved automatically if the watchdog triggers or a crash occurs. Check the `results/` directory for `partial_run_<timestamp>.csv`.

## Results Interpretation

### What does a "high power rate" indicate?
A high power rate (close to 1.0) means the selection method successfully identifies true predictors with high frequency under the given conditions.

### How do I interpret the Dunn's post-hoc results?
Dunn's test with Holm correction identifies which specific pairs of methods differ significantly. A low adjusted p-value (< 0.05) indicates a statistically significant difference in power.

### Why are some datasets excluded?
Datasets with a condition number > 10^10 (indicating perfect multicollinearity) are excluded to ensure numerical stability in OLS refitting.
