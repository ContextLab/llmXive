---
action_items:
- id: 48415507a69c
  severity: science
  text: Report standard deviations or confidence intervals for all main results in
    Table 1 and Table 3. RL training is stochastic; point estimates alone are insufficient
    to claim statistical significance.
- id: f94eb0689b54
  severity: science
  text: Specify the number of random seeds used for training and evaluation in the
    'Implementation Details' section. Current text does not mention seed count.
- id: 8db8b7fcd5c9
  severity: science
  text: Clarify the '150 steps' training duration mentioned in 'Implementation Details'.
    Is this total steps, per epoch, or per task? This is unusually low for RL and
    requires justification.
- id: 727fb9bde7ce
  severity: science
  text: Confirm that hyperparameter tuning (e.g., beta=5, lambda=0.01) was performed
    on a validation set, not the test set, to avoid data leakage.
artifact_hash: a2fe5096ad1b93f50db064c40f59b84672b255d5a406d9c082d97d449a5f037d
artifact_path: projects/PROJ-579-https-arxiv-org-abs-2605-15155/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T02:20:58.945420Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

This review focuses on the strength of scientific evidence supporting the central claims of "Self-Distilled Agentic Reinforcement Learning."

**Strengths:**
The paper presents a comprehensive evaluation across three diverse benchmarks (ALFWorld, Search-QA, WebShop) and multiple model scales (1.7B, 3B, 7B). The inclusion of ablation studies on gating strategies (Figure 3), hyperparameters (Figures 4-6), and retrieval methods (Table 3) demonstrates a systematic approach to validating the proposed token-level gating mechanism. The open-source code link (`https://github.com/ZJU-REAL/SDAR`) supports reproducibility.

**Concerns:**
1.  **Statistical Significance:** Table 1 and Table 3 report performance as point estimates (e.g., 84.4%, 86.8%) without standard deviations or confidence intervals. Reinforcement learning results are inherently noisy due to stochastic policy updates and environment interactions. Without reporting variance across multiple random seeds (e.g., 3-5 seeds), it is impossible to determine if the reported gains (e.g., +9.4% on ALFWorld) are statistically significant or due to random variance.
2.  **Training Steps:** The "Implementation Details" section states "Training on 8 H800 GPUs for 150 steps." This is an unusually low number of steps for RL training, which typically requires thousands of steps to converge. It is unclear if this refers to total steps, steps per task, or epochs. This ambiguity affects the assessment of compute efficiency and convergence.
3.  **Hyperparameter Tuning:** The ablation studies (Figures 4-6) identify optimal values for $\beta$ and $\lambda$. The text does not explicitly state whether these were tuned on a held-out validation set or the test set. Tuning on the test set would invalidate the generalization claims.
4.  **Sample Size:** WebShop evaluation uses "128 validation tasks." While standard for the benchmark, the small sample size increases the variance of the accuracy metric. Reporting confidence intervals is even more critical here.
5.  **Baseline Fairness:** The claim that "naïve GRPO+OPSD destabilises" requires evidence that the baselines were trained with the same compute budget (steps, GPUs) as the proposed method. The text mentions "All algorithms detailed in Appendix," but the main text should confirm fairness.

**Recommendation:**
The methodology is sound, but the statistical evidence is incomplete. Please add variance metrics, clarify training steps, and confirm validation-based tuning to strengthen the scientific claims.
