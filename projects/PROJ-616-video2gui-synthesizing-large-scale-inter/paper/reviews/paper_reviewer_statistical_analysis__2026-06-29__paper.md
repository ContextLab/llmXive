---
action_items:
- id: c77714faf995
  severity: science
  text: The human evaluation section (Sec 5.4) reports a Krippendorff's alpha of 0.84
    for 5 raters on 300 samples but provides no confidence intervals or standard errors.
    Given the small sample size relative to the dataset scale, the statistical significance
    of the quality difference between WildGUI (4.62) and baselines (3.35, 4.05) is
    unverified. A formal statistical test (e.g., permutation test or bootstrapped
    CI) is required to support the claim of 'significantly outperforming'.
- id: 578c35e5c78d
  severity: science
  text: The scaling law analysis (Fig 4, Sec 5.1) presents performance curves with
    single-point estimates for each data scale (0, 50B, 200B tokens). There is no
    indication of variance (e.g., error bars from multiple seeds or runs) or statistical
    significance testing between the 'Stage 2 Only' baseline and the pre-trained models.
    The claim of a 'strong positive correlation' is descriptive but lacks statistical
    rigor to rule out random fluctuation.
- id: 9d98d2b97fe4
  severity: science
  text: The ablation study (Table 3) reports single-run performance metrics (e.g.,
    31.9 vs 24.1 on AndroidWorld) without reporting standard deviations or p-values.
    The claim that removing L_traj causes a 'significant drop' is not statistically
    substantiated. The authors must report results averaged over multiple random seeds
    or provide a statistical test to validate the contribution of each loss component.
- id: 183a3f7833b8
  severity: science
  text: The video scoring model validation (Appendix Sec A.2) claims 'strong alignment'
    with ground truth based on a test set of only 100 videos. No statistical metrics
    (e.g., Pearson/Spearman correlation coefficients with confidence intervals, or
    MSE with variance) are provided to quantify this alignment. The threshold selection
    (score >= 4.2) appears arbitrary without a statistical justification or analysis
    of the score distribution.
artifact_hash: 9b264bacebdc198566c55b892eadee81103ef77a0231b5f086f102e723db2633
artifact_path: projects/PROJ-616-video2gui-synthesizing-large-scale-inter/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T19:19:30.632376Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The statistical analysis supporting the claims in this paper is insufficient and lacks necessary rigor for a dataset-scale contribution.

First, the **human evaluation** (Section 5.4) relies on a small sample size (300 data points rated by 5 experts) to validate a dataset of 12 million trajectories. While a Krippendorff's $\alpha$ of 0.84 is reported, the paper fails to provide confidence intervals for the mean scores (4.62 vs. 3.35/4.05). Without bootstrapped confidence intervals or a formal hypothesis test (e.g., a permutation test), the assertion that WildGUI "significantly outperforms" baselines is statistically unsupported. The variance in human ratings is high, and the current analysis does not rule out the possibility that the observed differences are due to chance.

Second, the **scaling law analysis** (Section 5.1, Figure 4) presents performance trends based on single experimental runs for each data scale (0, 50B, 200B tokens). The absence of error bars (representing standard deviation across multiple seeds) or statistical significance tests makes it impossible to determine if the observed improvements are robust or merely artifacts of specific random initializations. The claim of a "strong positive correlation" is purely descriptive; a regression analysis with $R^2$ values and p-values is required to substantiate the scaling relationship.

Third, the **ablation studies** (Table 3) report point estimates for performance metrics (e.g., a drop from 31.9% to 24.1% on AndroidWorld) without any measure of variance. In deep learning experiments, performance can fluctuate significantly based on hyperparameters and random seeds. Claiming that a specific loss component is "crucial" based on a single run is methodologically weak. The authors must report results averaged over at least 3-5 seeds with standard deviations and perform statistical tests (e.g., t-tests) to validate the significance of the ablation results.

Finally, the **video scoring model validation** (Appendix A.2) uses a test set of only 100 videos to claim "strong alignment" with ground truth. No quantitative metrics (e.g., correlation coefficients with confidence intervals) are provided. The selection of the threshold (4.2) appears arbitrary without an analysis of the score distribution or a receiver operating characteristic (ROC) curve analysis to justify the trade-off between precision and recall in the filtering pipeline.

To proceed, the authors must re-run key experiments with multiple seeds to report variance, apply statistical tests to all comparative claims, and provide confidence intervals for all human evaluation metrics.
