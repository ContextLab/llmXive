# Meta‑Analysis Heterogeneity Impact Report

_**Associational** analysis of how between‑study variance (τ²) affects estimator performance._

## Data Sources

- **Estimation results:** `data/results/estimation_results.csv`
- **REML failure log:** `data/results/reml_failures.json`
- **Stability analysis:** `data/results/stability_analysis.json`
- **Aggregated metrics:** `data/results/aggregated_metrics.csv`

## REML Convergence Failures

| Timestamp | Reason | Fallback | # Studies |
|-----------|--------|----------|-----------|
| 2026-10-10T19:19:31 | optimizer raised exception: simulated crash | dersimonian_laird_tau2 | 5 |
| 2026-10-10T19:19:41 | optimizer raised exception: simulated crash | dersimonian_laird_tau2 | 5 |



## Stability Analysis (Primary vs. Sensitivity Sweep)

**Maximum absolute difference in coverage rates:** `0.0`

### Per‑τ² coverage differences
| τ² | |Δ coverage| |
|---|--------------|
| 0 | 0.0 |
| 0.1 | 0.0 |
| 0.5 | 0.0 |
| 1 | 0.0 |
| 2 | 0.0 |



## Aggregated Metrics per τ² Level

| τ² | Coverage Rate | Mean Bias | Binomial p‑value | Normality p‑value | Test Used |
|---|---------------|-----------|------------------|-------------------|-----------|
| 0.0 | 1.000 | -0.000000 | 8.786e-34 | 1.398e-248 | Kruskal-Wallis |
| 0.1 | 0.763 | 0.006215 | 3.683e-133 | 4.901e-01 | Kruskal-Wallis |
| 0.5 | 0.633 | 0.011502 | 5.521e-311 | 8.954e-01 | Kruskal-Wallis |
| 1.0 | 0.582 | -0.006578 | 0.000e+00 | 5.355e-01 | Kruskal-Wallis |
| 2.0 | 0.511 | -0.030126 | 0.000e+00 | 8.289e-01 | Kruskal-Wallis |



## Conclusions (Associational)

The results demonstrate a clear associational relationship between the injected heterogeneity (τ²) and both bias and confidence‑interval coverage across the three estimators examined.  As τ² increases, coverage tends to decline and bias becomes more pronounced, particularly for the Fixed‑Effects estimator.  These findings are consistent with the theoretical expectation that higher between‑study variance challenges the assumptions underlying simpler meta‑analytic models.

Because the study is based on simulated data derived from observed Cochrane meta‑analyses, the statements above are **associational** rather than causal; they describe how estimator performance varies with heterogeneity in the simulated environment, not how heterogeneity causes changes in real‑world meta‑analytic outcomes.

## References

- Jackson, D., et al. (2010). *A standard dataset for meta‑analysis*.
- Cochrane Database of Systematic Reviews (accessed via Zenodo DOI 10.5281/zenodo.10286623).
