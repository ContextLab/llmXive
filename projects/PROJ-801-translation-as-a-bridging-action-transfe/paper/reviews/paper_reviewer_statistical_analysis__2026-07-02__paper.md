---
action_items:
- id: a5c848357d56
  severity: science
  text: Report statistical significance (e.g., p-values, confidence intervals, or
    standard deviations) for the success rate and progress metrics in Tables 1, 2,
    3, and 4. Currently, single point estimates are presented without error bars or
    variance measures, making it impossible to assess if the observed improvements
    (e.g., 22.50% vs 12.50% in Tab 1) are statistically robust or due to random variation.
- id: 595cb78e19ce
  severity: science
  text: Clarify the statistical protocol for the 15 tasks. The text states 'eight
    trials per task' (Sec 5.1), but the tables report aggregate percentages. Specify
    if these percentages are averages over the 120 total trials (15 tasks * 8 trials)
    or if they represent the proportion of tasks where success was achieved. If the
    latter, the sample size (N=15) is too small for robust statistical inference without
    reporting variance across tasks.
- id: 55fa19eec649
  severity: science
  text: The ablation study in Table 3 (Sec 5.5) compares two models. Given the high
    variance often seen in robotic learning, a single run comparison is insufficient.
    Please confirm if these results are averaged over multiple random seeds or independent
    training runs, and report the standard deviation to validate the claim that the
    performance drop is 'essential' rather than a stochastic fluctuation.
artifact_hash: 6729da456139f307f3d0e73ac6f31e579b7d43848bd0dd84327d8a569e70121b
artifact_path: projects/PROJ-801-translation-as-a-bridging-action-transfe/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T07:09:44.272205Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical reporting in the experimental section (Sec. 5) is currently insufficient to support the strong claims regarding the efficacy of the bridging action representation. While the paper presents clear trends in Tables 1 through 4 (e.g., `exp:tab:sec5.3`, `exp:tab:sec5.4`, `exp:tab:sec5.5`, `exp:tab:sec5.6`), it relies exclusively on point estimates (mean success rates and progress percentages) without any measure of variance, uncertainty, or statistical significance.

Specifically, in **Table 1** (`exp:tab:sec5.3`), the authors claim the bridging action is superior to 6DoF actions (22.50% vs 12.50% overall success). Without standard deviations or confidence intervals derived from multiple independent runs (seeds), it is impossible to determine if this 10% gap is statistically significant or a result of random initialization variance, which is common in VLA training. The text mentions "eight trials per task" (Sec 5.1), but it is unclear if the reported metrics are aggregated over these trials or if the experiments were repeated with different random seeds. If the 120 total trials (15 tasks × 8 trials) constitute the entire dataset, the effective sample size for task-level generalization is small (N=15), necessitating a report of per-task variance or a non-parametric test (e.g., Wilcoxon signed-rank) to validate the "substantial improvements" claimed in Sec 5.2.

Furthermore, the ablation studies in **Table 3** (`exp:tab:sec5.5`) and **Table 4** (`exp:tab:sec5.6`) present single-point comparisons. In deep learning for robotics, performance can fluctuate significantly based on hyperparameters and random seeds. The claim that removing the bridging objective "greatly degrades" performance (dropping from 38.33% to 12.50%) requires evidence that this drop is consistent across multiple training runs. The absence of error bars in the figures (e.g., `exp:fig:sec5.2_results`, `exp:fig:appdxB_main_results`) and the lack of statistical tests (t-tests, ANOVA, or confidence intervals) in the text prevents a rigorous assessment of the results' reliability.

To meet the standards of statistical rigor expected for this venue, the authors must:
1. Report results as mean ± standard deviation over at least 3-5 independent training seeds.
2. Include p-values or confidence intervals for the key comparisons in Tables 1-4.
3. Clarify whether the "eight trials per task" refers to evaluation rollouts only, and if so, explicitly state the number of training seeds used to generate the reported means.

Without these additions, the quantitative evidence remains suggestive but not statistically conclusive.
