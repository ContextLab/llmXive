# Evaluating Resting-State fMRI Entropy as a Biomarker for Attention-Deficit Traits

**Abstract**

This study evaluates resting-state fMRI entropy as a biomarker for
attention-deficit traits. We computed Sample Entropy (m=2, r=0.2*SD)
across 200 brain parcels for 100 subjects
from the ADHD-200 dataset. Our primary analysis compared entropy-only
predictive models against functional connectivity baselines using
Ridge Regression. Results show a delta correlation of Δr = 0.0523
with permutation p-value = 0.0120. We identified 15 significant parcels
after FDR correction. These findings suggest that
entropy-based features capture unique variance in attention-deficit
symptom severity beyond traditional connectivity measures.

**Methods**

**Data Acquisition and Preprocessing**
We utilized the ADHD-200 dataset from OpenNeuro. Subjects underwent
standard preprocessing including motion scrubbing (FD > 0.2mm) and
truncation to N=120 volumes.

**Entropy Calculation**
Sample Entropy was computed for each of 200 brain parcels using
parameters m=2 and r=0.2×SD. Zero-variance parcels were imputed
with cohort medians.

**Modeling Approach**
We trained Ridge Regression models for ADHD-RS prediction using:
(1) Entropy-only features, (2) Connectivity-baseline (200 PCA components),
and (3) Combined features. Performance was evaluated via 5-fold
stratified cross-validation.

**Statistical Validation**
Significance was assessed using 1,000 permutations (p < 0.05 threshold).
FDR correction was applied to parcel-level coefficients.

**Results**

**Primary Analysis**
The entropy-only model achieved a mean Pearson correlation of
r_entropy, while the connectivity-baseline model achieved r_conn.
The raw difference was Δr = 0.0523.

**Statistical Significance**
Permutation testing (n=1000) yielded p = 0.0120,
significantly
exceeding the α=0.05 threshold.

**Effect Size Confidence**
The 95% bootstrap confidence interval for ΔAUC had a lower bound
of 0.0612,
exceeding
the 0.05 effect size threshold.

**Sensitivity Analysis**
The sensitivity sweep showed variance of 0.000234 for
correlation and 0.000156 for AUC across r-parameter
variations.

**Parcel-Level Findings**
FDR correction identified 15 significant parcels
associated with attention-deficit traits.

**Discussion**

Our findings provide promising evidence that resting-state fMRI
entropy captures unique information about attention-deficit traits
beyond traditional functional connectivity. The entropy-only model
demonstrated statistically significant
performance improvements over connectivity baselines.

**Limitations**
- Sample size constraints (N < P) require cautious interpretation
- Motion confounds remain a potential concern despite scrubbing
- Generalizability to other populations needs further validation

**Future Directions**
Future work should validate these findings in larger cohorts and
explore the biological mechanisms underlying entropy differences
in attention-deficit populations.

**Appendix: Model Metrics Summary**
- Δr (Entropy vs Connectivity): 0.0523
- ΔAUC CI Lower Bound: 0.0612
- Permutation p-value: 0.0120
- Sensitivity Variance (r): 0.000234
- Sensitivity Variance (AUC): 0.000156
- Significant Parcels: 15

---
*Generated automatically from model_metrics.json on 2024-01-15*
