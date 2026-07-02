---
action_items:
- id: 18ef470d4f27
  severity: writing
  text: Clarify the statistical method used to compute the 95% confidence intervals
    reported in Figures 3, 4, 5, and 6. The text mentions '95% CIs over all runs'
    but does not specify if these are standard error of the mean (SEM), standard deviation
    (SD), or bootstrap intervals, nor does it state the distributional assumptions
    (e.g., normality) used for the calculation.
- id: 9e6f93e9df4a
  severity: science
  text: The curation pipeline (Section 3.2) uses a binary acceptance threshold (delta=0.001)
    and a consensus rule (3/5 models). The statistical power of this selection process
    is not discussed. There is a risk of selection bias where datasets with high variance
    might be rejected or accepted based on random seed fluctuations rather than true
    signal. A sensitivity analysis or power calculation for the curation threshold
    is needed.
- id: 152706f953d0
  severity: science
  text: In Appendix A.1, regression targets are discretized into 20 bins for the TAR
    fine-tuning step. The paper claims this is 'more stable' but does not provide
    statistical evidence (e.g., comparison of MSE or R^2) that this discretization
    preserves the predictive signal better than direct regression fine-tuning. This
    methodological choice requires justification or an ablation study.
artifact_hash: 28e097e31933ecce294eb34fd92a9e53c4dcbbab117fcc0a77af75a314777084
artifact_path: projects/PROJ-577-multabench-benchmarking-multimodal-tabul/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:49:24.216326Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis presented in MulTaBench is generally robust in its experimental design, utilizing multiple random seeds (n=5) and diverse tabular learners to establish the superiority of Target-Aware Representations (TAR) over frozen embeddings. The use of 95% confidence intervals in the main results figures (e.g., Figure 3, Figure 4) correctly conveys the variability across seeds. However, several critical statistical details are missing or require clarification to ensure full reproducibility and validity of the claims.

First, the method for calculating the reported 95% confidence intervals is not explicitly defined in the text or appendices. It is unclear whether these intervals represent the standard error of the mean (SEM), the standard deviation (SD) of the performance metric, or a bootstrap-derived interval. Furthermore, the assumption of normality required for standard parametric confidence intervals is not verified, which is particularly relevant given the small number of seeds (n=5) used for aggregation. The authors should explicitly state the formula or method used (e.g., "95% CI calculated as mean ± 1.96 * SEM assuming normal distribution") to allow for proper interpretation of the error bars.

Second, the curation pipeline described in Section 3.2 and Appendix A.3 relies on a binary decision rule: a dataset is accepted only if the performance gain (Delta) exceeds a fixed threshold (delta=0.001) for at least 3 out of 5 models. This approach introduces a potential selection bias. Datasets with high variance in performance across seeds might fail the threshold due to random fluctuation rather than a lack of true "Joint Signal" or "Task-awareness." Conversely, datasets with low variance but small effect sizes might pass. The paper does not discuss the statistical power of this selection mechanism or the probability of Type I/II errors in the curation process. A sensitivity analysis varying the threshold (delta) or the consensus fraction (rho) would strengthen the robustness of the benchmark selection.

Third, the handling of regression targets in the TAR fine-tuning step (Appendix A.1) involves discretizing continuous labels into 20 equal-frequency bins and optimizing for cross-entropy. While the authors state this is "more stable," they provide no statistical comparison to a direct regression fine-tuning objective (e.g., MSE or MAE). Discretization inherently discards information and introduces quantization error. Without an ablation study showing that the discretized approach yields comparable or superior downstream performance (R^2) compared to direct regression fine-tuning, this methodological choice remains an unverified assumption that could impact the validity of the TAR gains reported for regression tasks.

Finally, while the paper reports win rates in Table 10 of the Appendix, it does not provide statistical significance tests (e.g., paired t-tests or Wilcoxon signed-rank tests) to confirm that the observed win rates (e.g., 91.5% for CatBoost) are significantly different from chance (50%) or from each other. Given the large number of dataset-model pairs, even small effect sizes could be statistically significant, but the current presentation lacks this formal inference.
