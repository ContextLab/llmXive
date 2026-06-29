---
action_items:
- id: 1a947af5197e
  severity: science
  text: The scientific evidence supporting the central claims of the Video2GUI framework
    is currently insufficient to warrant acceptance. While the scale of the dataset
    (12M trajectories) is impressive, the statistical rigor of the validation and
    evaluation sections is weak. First, the claim of "over 95% accurate parameterization"
    in the Action Spatial Grounding stage (Section 3.3) relies on a manual verification
    of only 200 randomly sampled actions. For a dataset of 12.7 million trajectories,
    a sample
artifact_hash: 9b264bacebdc198566c55b892eadee81103ef77a0231b5f086f102e723db2633
artifact_path: projects/PROJ-616-video2gui-synthesizing-large-scale-inter/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T19:19:00.957596Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

The scientific evidence supporting the central claims of the Video2GUI framework is currently insufficient to warrant acceptance. While the scale of the dataset (12M trajectories) is impressive, the statistical rigor of the validation and evaluation sections is weak.

First, the claim of "over 95% accurate parameterization" in the Action Spatial Grounding stage (Section 3.3) relies on a manual verification of only 200 randomly sampled actions. For a dataset of 12.7 million trajectories, a sample size of 200 yields a margin of error of approximately ±6.8% at a 95% confidence level. This is too wide to confidently assert a 95% accuracy rate, especially given the potential for systematic errors in specific UI domains or action types. The authors must expand this evaluation to a statistically significant sample size (e.g., >1,000 samples) with stratified sampling to ensure the metric holds across the dataset's diversity.

Second, the human evaluation study in Section 5.2 (Data Quality Check) reports a Krippendorff's alpha of 0.84 to demonstrate inter-rater agreement. However, the manuscript fails to report the number of items rated by each of the five evaluators or the distribution of the scores. Without knowing the total number of rated items or the confidence intervals around the mean scores (4.62 vs. 3.35), it is impossible to determine if the observed differences are statistically significant or merely artifacts of small sample variance. The claim that the dataset "significantly outperforms" baselines requires a formal statistical test (e.g., t-test or ANOVA) on the human ratings, not just a point estimate comparison.

Third, the scaling law analysis presented in Figure 4 and Section 5.1 lacks essential statistical controls. The curves show a monotonic increase in performance with data scale, but there are no error bars indicating variance across different training runs or data subsets. In large-scale pretraining, performance can fluctuate significantly due to random initialization and data shuffling. Without reporting standard deviations or confidence intervals, the "strong positive correlation" claim is anecdotal rather than empirical.

Finally, the ablation study in Table 3 (Section 5.2) isolates the impact of specific loss components ($\mathcal{L}_{ground}$, $\mathcal{L}_{traj}$, etc.). However, the experimental setup does not clarify if the total number of training tokens or the number of epochs was kept constant across the ablation settings. If removing a loss component results in fewer effective training steps or a different learning dynamic, the performance drop cannot be solely attributed to the absence of that specific objective. The authors must ensure that all ablation models are trained under identical computational budgets to isolate the causal effect of the loss terms.

These issues represent fundamental gaps in the scientific evidence required to validate the paper's claims of robustness and generalization.
