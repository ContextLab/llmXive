# Analysis Methodology

## Objective

To quantify the deviation of empirical p-value distributions from the theoretical
Uniform(0,1) distribution under various high-dimensional conditions.

## Metrics

### 1. Kolmogorov-Smirnov (KS) Statistic

The primary metric for deviation is the KS statistic:
$$ D = \max_x | F_{empirical}(x) - x | $$
Where $F_{empirical}$ is the cumulative distribution of the collected p-values.
- **Interpretation**:
 - $D \approx 0$: P-values are uniform (test is valid).
 - $D > 0.05$ (or similar threshold): Significant deviation (test is invalid).
 - High $D$ with excess small p-values indicates **anti-conservative bias**
 (too many false positives).

### 2. QQ-Plot Deviation

Quantile-Quantile plots are generated to visually inspect the distribution:
- **X-axis**: Theoretical quantiles of Uniform(0,1).
- **Y-axis**: Empirical quantiles of observed p-values.
- **Deviation**: A curve below the $y=x$ line indicates an excess of small
 p-values (anti-conservative). A curve above indicates conservative behavior.

## Reference Standards

### Gold Standard: Permutation Test

Since standard asymptotic assumptions may fail in high dimensions, we use a
permutation-based reference to determine the "true" p-value distribution
for a given dataset realization.

**Procedure**:
1. Compute the observed test statistic $T_{obs}$.
2. Permute group labels $B$ times (e.g., $B=1000$).
3. Compute $T_{perm}$ for each permutation.
4. Empirical p-value $p_{perm} = (\text{count}(T_{perm} \ge T_{obs}) + 1) / (B+1)$.

We compare the distribution of standard analytical p-values against the
distribution of these permutation-based p-values.

## Statistical Power & Iteration Count

To ensure the KS statistic is estimated with sufficient precision, we perform
a power analysis (see `code/utils/simulation.py`, T008) to determine the
minimum number of simulation iterations ($N$) required to detect a KS deviation
of $> 0.05$ with power $\ge 0.8$.

## Sensitivity Analysis

We systematically vary the correlation parameter $\rho$ to map the relationship
between correlation strength and p-value invalidity.
- **Input**: $\rho \in \{0.0, 0.1, 0.3, 0.5, 0.7, 0.9\}$.
- **Output**: `data/results/sensitivity.csv` containing `rho` and `ks_stat`.

## Confidence Intervals

Bootstrap resampling is used to estimate the uncertainty of the KS statistic.
- **Method**: Resample the p-value trajectory with replacement 1000 times.
- **Output**: 95% confidence intervals stored in `data/results/bootstrap_cis.json`.

## Execution Flow

1. **Data Generation**: Run `code/generate_data.py` to create datasets.
2. **Hypothesis Testing**: Run `code/run_tests.py` to collect p-values.
3. **Analysis**: Run `code/analyze_pvalues.py` to compute KS statistics and
 permutation references.
4. **Visualization**: Run `code/plot_qq.py` to generate diagnostic plots.
5. **Sensitivity**: Run `code/sensitivity_analysis.py` to aggregate results
 across $\rho$.

All results are aggregated and stored in the `data/results/` directory.
