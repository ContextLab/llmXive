---
action_items:
- id: 3240396e7611
  severity: writing
  text: "Table 1 and Table 2 report pass@1 accuracy to two decimal places (e.g., 66.71%)\
    \ without any measure of uncertainty (SD, SE, or CI) or mention of the number\
    \ of random seeds used. In RL experiments, performance is highly stochastic; reporting\
    \ a single point estimate implies false precision. Report mean \xB1 SD over at\
    \ least 3 independent seeds for all methods, or explicitly state that results\
    \ are from a single run and rephrase claims of 'stability' accordingly."
- id: a4ea30bf8189
  severity: writing
  text: The 'Stable' column in Table 1 is a binary qualitative judgment (checkmark/cross)
    derived from visual inspection of training curves (Figure 1) rather than a statistical
    test of variance or a formal stability metric (e.g., coefficient of variation
    over the final 20% of training). Define a quantitative stability metric (e.g.,
    max drop from peak, or variance of the last 100 steps) and report it numerically
    to support the binary classification.
- id: f326c6dba5a7
  severity: writing
  text: The paper claims MIPU is 'significantly better' or 'more stable' than baselines
    in the abstract and conclusion, but no hypothesis tests (e.g., paired t-tests
    or Wilcoxon signed-rank tests) are reported in the text or tables to support these
    comparative claims. If multiple seeds are run, perform a statistical test on the
    final scores and report p-values; if only one run is available, remove the word
    'significantly' and qualify the comparison as 'observed improvement'.
artifact_hash: 532a85457b6c71e1e8174b90594afc6d1be5ab1b35a438039d06e81d212f0a7d
artifact_path: projects/PROJ-994-the-mirage-of-optimizing-training-polici/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T03:26:56.422393Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical reporting in this paper lacks the necessary uncertainty quantification required to validate the comparative claims made. While the experimental design (FP8 rollout, specific benchmarks) is described, the results in **Table 1** (Main Results) and **Table 2** (Ablation) present performance metrics (pass@1 accuracy) as precise point estimates (e.g., 66.71%, 53.97%) without any accompanying standard deviation, standard error, or confidence intervals. In reinforcement learning, where training dynamics are stochastic and sensitive to random seeds, reporting a single number (or a number derived from an unspecified number of runs) creates an illusion of precision that the data does not support.

Specifically, the claim that MIPU is "more stable" is supported by a binary "Stable" column in Table 1 and visual inspection of **Figure 1**, rather than a quantitative metric of variance or a statistical test of the training trajectory's volatility. Without reporting the variance across multiple independent runs (seeds), it is impossible to determine if the observed differences between MIPU and baselines (e.g., the 1.05% gain on Qwen3-4B) are statistically significant or merely noise. The text uses terms like "significantly better" and "stable" without the statistical machinery (p-values, effect sizes, or variance measures) to back them up.

To rectify this, the authors should report results as mean ± standard deviation over at least 3-5 independent seeds for all methods. If the computational cost prohibits multiple seeds, the authors must explicitly state that results are from a single run, remove claims of statistical significance, and replace the binary "Stable" column with a quantitative metric of training stability (e.g., the standard deviation of the score over the final 20% of training steps).
