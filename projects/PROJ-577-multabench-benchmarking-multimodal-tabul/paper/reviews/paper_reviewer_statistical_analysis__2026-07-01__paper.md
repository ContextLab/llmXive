---
action_items:
- id: 3a6fe4e3bc13
  severity: writing
  text: The paper reports 95% confidence intervals (CIs) for performance metrics (e.g.,
    Fig 4, Fig 5) but fails to specify the statistical method used for their calculation
    (e.g., bootstrap, t-distribution, or standard error of the mean). Given the use
    of 5 random seeds, the method for aggregating variance across seeds and datasets
    must be explicitly defined to ensure reproducibility.
- id: 7f5ec054c0ac
  severity: science
  text: The curation pipeline (Sec 3.2) applies a binary acceptance threshold (delta=0.001)
    to model performance gains. The paper does not report statistical significance
    tests (e.g., paired t-tests or Wilcoxon signed-rank tests) to verify that these
    gains are distinguishable from random noise, raising concerns about the robustness
    of the dataset selection criteria.
- id: bcf616dec320
  severity: science
  text: In Appendix A.1, regression targets are discretized into 20 bins for the TAR
    finetuning step. The paper does not provide a statistical justification for this
    specific bin count or analyze how this discretization affects the variance and
    bias of the final regression metrics compared to direct regression finetuning.
- id: d28fb43e73fc
  severity: science
  text: The 'No PCA' ablation (Appendix A.4) excludes datasets with >5 text features
    and limits analysis to two learners. The paper does not discuss the statistical
    power of this reduced sample or whether the exclusion criteria introduce selection
    bias that invalidates the generalizability of the 'no artifact' claim.
artifact_hash: 28e097e31933ecce294eb34fd92a9e53c4dcbbab117fcc0a77af75a314777084
artifact_path: projects/PROJ-577-multabench-benchmarking-multimodal-tabul/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:50:39.147645Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The paper presents a comprehensive benchmark and argues for the necessity of Target-Aware Representations (TAR) in Multimodal Tabular Learning. While the experimental design is extensive, the statistical reporting and analysis require clarification to fully support the claims of robustness and significance.

First, regarding **statistical significance and error bars**: The paper consistently reports 95% confidence intervals (CIs) in figures (e.g., Figure 4, Figure 5, Figure 7) and tables. However, the methodology for calculating these intervals is not explicitly defined in the text or the checklist. Specifically, it is unclear whether these CIs are derived from the standard error of the mean (assuming normality), bootstrap resampling, or the standard deviation of the 5 random seeds. Given the small number of seeds (n=5), the assumption of normality for t-distribution-based CIs may be weak. The authors must explicitly state the calculation method (e.g., "95% CI calculated via bootstrap with 1000 resamples over the 5 seeds") to ensure the reported uncertainty is interpretable and reproducible.

Second, the **curation pipeline's acceptance criteria** rely on a fixed performance gain threshold ($\delta=0.001$) as described in Appendix A.1. The paper asserts that datasets passing this threshold exhibit "Joint Signal" and "Task-awareness." However, there is no mention of statistical hypothesis testing (e.g., paired t-tests or Wilcoxon signed-rank tests) to determine if the observed gains between "Joint TAR" and "Joint Frozen" conditions are statistically significant or merely artifacts of random variance. Without significance testing, the binary classification of datasets as "accepted" or "rejected" based on a small delta is statistically fragile. The authors should either perform significance tests on the curation metrics or justify the threshold $\delta$ with a power analysis or noise floor estimation.

Third, the **handling of regression targets** in the TAR finetuning step (Appendix A.1) involves discretizing continuous labels into 20 equal-frequency bins. While the authors note this improves stability, they do not provide a statistical analysis of the information loss or bias introduced by this discretization. Specifically, does the discretization artificially inflate the apparent gain of TAR by smoothing the loss landscape? A sensitivity analysis varying the number of bins (e.g., 10, 20, 50) or a comparison with direct regression finetuning (if stable) would strengthen the statistical validity of this preprocessing choice.

Finally, the **"No PCA" ablation study** (Appendix A.4) excludes datasets with more than 5 text features and restricts the analysis to LightGBM and CatBoost. The paper claims this proves the gains are not artifacts of dimensionality reduction. However, the exclusion of a significant portion of the benchmark (text-heavy datasets) and the reduction of the model pool introduces potential selection bias. The authors should discuss the statistical power of this reduced sample and whether the results on the remaining 33 datasets are representative of the full MulTaBench distribution.

Addressing these points will significantly enhance the statistical rigor and reproducibility of the benchmark's conclusions.
