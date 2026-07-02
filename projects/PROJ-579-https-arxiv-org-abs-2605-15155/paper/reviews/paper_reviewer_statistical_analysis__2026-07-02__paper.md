---
action_items:
- id: 506a37528961
  severity: science
  text: Report statistical significance (e.g., p-values, confidence intervals, or
    standard deviations over seeds) for the performance gains in Table 1. The current
    presentation of single-point estimates (e.g., +9.4% on ALFWorld) does not allow
    assessment of whether improvements are robust or due to random variance.
- id: dd108afbad89
  severity: science
  text: Clarify the number of random seeds used for all experiments. The 'Implementation
    Details' section mentions training steps and batch sizes but omits the number
    of independent runs used to generate the mean scores in Table 1 and the ablation
    studies.
- id: e3d06f355181
  severity: science
  text: Provide error bars or variance metrics in the training dynamics figures (e.g.,
    Figure 7b_alfworld_gap_gate, ablation plots). The curves show mean trends, but
    without uncertainty bands, it is difficult to judge the stability of the gating
    mechanism across different training runs.
artifact_hash: a2fe5096ad1b93f50db064c40f59b84672b255d5a406d9c082d97d449a5f037d
artifact_path: projects/PROJ-579-https-arxiv-org-abs-2605-15155/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:53:55.699854Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical rigor of the experimental evaluation requires strengthening to support the claims of "substantial improvements" and "consistent gains." While the methodological design (sigmoid gating) is theoretically sound, the empirical validation lacks standard statistical reporting required for reproducibility and confidence in the results.

**1. Lack of Variance and Significance Reporting:**
Table 1 (`tables/experiment.tex`) presents performance metrics as single scalar values (e.g., 84.4% for SDAR on ALFWorld-3B). There is no indication of the number of random seeds used, nor are standard deviations or confidence intervals provided. In reinforcement learning, performance can vary significantly based on initialization and stochasticity. Without reporting variance (e.g., mean ± std) or conducting statistical significance tests (e.g., t-tests or Wilcoxon signed-rank tests) against baselines like GRPO, it is impossible to determine if the reported gains (e.g., +9.4%) are statistically significant or merely artifacts of a specific random seed. The claim of "consistent outperformance" is not statistically substantiated.

**2. Missing Experimental Reproducibility Details:**
The "Implementation Details" section (Section 4) specifies hyperparameters like $\lambda=0.01$ and $\beta=5.0$ but fails to state the number of independent training runs (seeds) performed for each configuration. For a robust statistical analysis, results should be averaged over at least 3-5 seeds. The absence of this information prevents the calculation of confidence intervals and undermines the reliability of the ablation studies (Section 4.3), where small differences between gating strategies (e.g., Gap vs. Soft-OR) are discussed.

**3. Uncertainty in Training Dynamics:**
Figures illustrating training dynamics (e.g., `figures/7b_alfworld_gap_gate.pdf`, `figures/ablations_tip.pdf`) display single curves representing the mean behavior. To properly assess the stability of the proposed gating mechanism versus the instability of baselines (like naive GRPO+OPSD), these plots should include shaded regions representing standard deviation or confidence intervals across seeds. This would visually demonstrate whether the "stable optimization" claimed in the text is a consistent property or an average of divergent runs.

**Recommendation:**
The authors should re-run experiments with multiple random seeds (minimum 3), report mean ± standard deviation in all tables, and include error bars in all training curves. Additionally, statistical significance tests should be performed to validate that the improvements over baselines are not due to chance.
