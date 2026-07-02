---
action_items:
- id: 75104aae45e3
  severity: science
  text: Report variance measures (standard deviation or standard error) for all aggregate
    metrics (F1, Precision, Recall, Token counts) in Tables 1 and 2. Currently, only
    point estimates are provided, preventing assessment of statistical significance
    or effect stability across the 200+ instance benchmarks.
- id: 02e6af0fcd93
  severity: science
  text: Clarify the statistical aggregation method for the 'Standalone Exploration
    Evaluation' (Appendix e000). The text states 'Scoring & Compute per-instance precision...
    then report instance-wise averages.' Confirm if the reported F1 is the mean of
    per-instance F1 scores or the F1 computed from aggregated true/false positives
    across all instances, as these yield different results for imbalanced data.
- id: c5d8deab7c76
  severity: writing
  text: The RL reward function (Eq 1 & 2, Appendix e000) includes a hard penalty for
    format violations. Specify if the reported 'RL reward' curves in Figure 1 are
    normalized or raw, and whether the KL coefficient (0.0) implies no KL-divergence
    penalty was applied during the reported runs, which may affect the stability of
    the policy updates.
artifact_hash: aacf7bdcf1a98366e0f188ee3913f0ca169df04fd292176ee0c4b5c0f02dc68b
artifact_path: projects/PROJ-716-fastcontext-training-efficient-repositor/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T22:41:30.085860Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical reporting in the manuscript requires clarification to ensure the robustness of the reported gains. While the experimental design (SFT followed by RL on a held-out set) is sound, the presentation of results lacks necessary statistical context.

First, the primary results tables (Table 1: End-to-End Results; Table 2: Standalone Exploration Quality) report only point estimates (e.g., F1 = 73.71, Score = 71.7). Given the sample sizes (e.g., 200 instances for SWE-bench Pro, 300 tasks for cost analysis), the absence of variance measures (standard deviation, standard error, or confidence intervals) makes it impossible to determine if the observed improvements (e.g., the 5.5% accuracy gain) are statistically significant or within the noise of the evaluation. For instance, in the standalone evaluation, reporting the distribution of F1 scores across instances would better illustrate the consistency of the explorer's performance compared to baselines.

Second, the aggregation method for the exploration metrics in Appendix e000 (Section "Standalone exploration evaluation protocol") needs explicit definition. The text mentions computing per-instance precision/recall/F1 and then averaging. In information retrieval tasks with varying numbers of ground-truth citations per instance, the "macro-average" (mean of per-instance F1) and "micro-average" (F1 of aggregated counts) can differ significantly. The authors must specify which metric is reported to allow for correct interpretation and reproducibility.

Finally, regarding the RL optimization details in Appendix e000, the KL coefficient is listed as 0.0. While this simplifies the reward function, it removes the regularization term that typically prevents policy collapse in GRPO. The authors should briefly discuss the stability of the training curves (Figure 1) in this context or confirm that the reward signal was sufficiently sparse and well-defined to prevent divergence without KL regularization. The current text does not address this potential statistical risk in the training dynamics.
