---
action_items:
- id: 74ff1fd686dc
  severity: writing
  text: The statistical analysis in this paper is generally sound in its experimental
    design, particularly the use of multiple random seeds (n=5) to estimate variance
    in demonstration ordering (Section 4.3, Appendix B). The distinction between non-reasoning
    and reasoning tasks is well-supported by the observed trends in Figures 1 and
    2. However, several specific statistical and methodological details require clarification
    to ensure full reproducibility and rigor. First, Algorithm 1 in Appendix C contain
artifact_hash: da80d19d18126d829231e022c90784234c941daee73db4750a219950884e0e6f
artifact_path: projects/PROJ-563-many-shot-cot-icl-making-in-context-lear/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T23:26:14.089209Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in this paper is generally sound in its experimental design, particularly the use of multiple random seeds (n=5) to estimate variance in demonstration ordering (Section 4.3, Appendix B). The distinction between non-reasoning and reasoning tasks is well-supported by the observed trends in Figures 1 and 2. However, several specific statistical and methodological details require clarification to ensure full reproducibility and rigor.

First, **Algorithm 1** in Appendix C contains a critical syntax error in the pseudocode. Line 18 reads `m[j] <- m[j] + x * score`, where the variable `x` is undefined. The surrounding text suggests the intent is to aggregate scores from PCA and UMAP projections (likely by averaging), but the current formula is mathematically invalid. This must be corrected to clearly define how the smoothness score $\mathbf{m}$ is computed from the multiple dimensionality reduction runs.

Second, while the paper reports means and standard deviations (e.g., Table 3, Table 4), it lacks formal **statistical significance testing**. The claim that CDS yields "consistent gains" (Abstract, Section 5) relies on visual inspection of mean differences. Given the small sample size of seeds (n=5), the authors should perform paired statistical tests (e.g., paired t-test or Wilcoxon signed-rank test) between the CDS and baseline (Origin/High-Curv) conditions for each task/model pair. Reporting p-values or 95% confidence intervals for the performance differences would strengthen the evidence that the observed improvements are not due to random variation in the seed selection.

Third, the **curvature metric** is highly sensitive to the dimensionality reduction step. The paper states that PCA or UMAP is used to project embeddings before calculating angles (Section 4.2, Algorithm 1), but does not specify the target dimensionality or, for UMAP, the hyperparameters (e.g., `n_neighbors`, `min_dist`). Since the geometric properties of the trajectory (and thus the calculated curvature) depend heavily on these choices, these parameters must be explicitly reported in the appendix to allow for exact reproduction of the smoothness scores.

Finally, in the **similarity analysis** (Section 4.1), the authors compare "most-similar" vs. "most-dissimilar" sets. The statistical power of this comparison depends on the number of test queries. While the text implies averaging across models, the number of test instances per task is not explicitly stated in the context of the statistical aggregation. Clarifying the total number of test queries used to generate the curves in Figure 3 would help assess the robustness of the "failure of similarity" claim.
