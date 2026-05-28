# Idea — follow-up to Regression Shrinkage and Selection via the Lasso (statistics)

Anchor paper: Regression Shrinkage and Selection via the Lasso (Tibshirani R et al., 1996; DOI 10.1111/j.2517-6161.1996.tb02080.x, https://doi.org/10.1111/j.2517-6161.1996.tb02080.x).

Research question: Across 30 UCI regression benchmark datasets, how does Lasso's variable-selection stability (measured by Jaccard overlap across bootstrap replicates) depend on sample size, predictor dimensionality, and the chosen lambda criterion (CV-min vs. CV-1SE)?

Hypothesis: Selection stability scales sub-linearly with n/p; the 1SE criterion yields more stable selections than CV-min on most datasets but with measurable predictive-MSE cost.

Methods: Bootstrap-resample each dataset 500 times; fit Lasso with both criteria; report stability + held-out MSE per dataset + pooled.

Feasibility: implementable with free-model LLM panels + publicly available data; no paid services or proprietary compute required.
