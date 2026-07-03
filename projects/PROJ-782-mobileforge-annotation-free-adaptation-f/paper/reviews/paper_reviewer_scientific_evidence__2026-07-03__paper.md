---
action_items:
- id: 3aeed2d19257
  severity: science
  text: Report statistical significance (e.g., p-values, confidence intervals, or
    standard deviations over multiple seeds) for the key performance gains in Table
    1 (AndroidWorld) and Table 2 (MobileWorld). Single-run point estimates (e.g.,
    67.2% vs 69.0%) are insufficient to claim robust improvement given the variance
    typical in RLHF/GRPO training.
- id: a62b574bd92f
  severity: science
  text: Clarify the sample size and selection bias in the 'Evaluator model' ablation
    (Table 5). The claim that Gemini 2.5 Pro yields higher Pass@3 (71%) than Qwen3-VL-8B
    (70%) is based on a single run of 200 tasks. Provide variance estimates or a larger
    sample size to confirm this difference is not due to stochasticity or task-specific
    noise.
- id: be25b5559ca5
  severity: science
  text: The 'Task filtering' ablation (Table 4) shows identical AndroidWorld performance
    (48.3%) for two different filtering strategies but different MobileWorld results.
    Explain the statistical stability of this metric; a 0.0% difference in the primary
    metric despite a change in training data composition suggests potential overfitting
    or lack of sensitivity in the evaluation protocol.
artifact_hash: eb6909e8c26be542682832f5d7b13c92b92b728f8b94fb6c9612acad1621be79
artifact_path: projects/PROJ-782-mobileforge-annotation-free-adaptation-f/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T06:30:46.034643Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling framework for annotation-free adaptation, but the scientific evidence supporting the magnitude and robustness of the reported gains requires strengthening. While the absolute performance numbers are impressive, the lack of statistical rigor in the experimental section is a significant gap.

First, the primary results in Table 1 (AndroidWorld) and Table 2 (MobileWorld) are presented as single-point estimates (e.g., 67.2% Pass@3). In reinforcement learning and policy optimization, performance can vary significantly based on random seeds, initialization, and the specific subset of tasks sampled. Without reporting standard deviations over multiple independent runs (e.g., 3-5 seeds) or confidence intervals, it is impossible to determine if the observed improvements (e.g., the +9.0% relative gain on MobileWorld) are statistically significant or within the noise floor of the training process. The claim of "strongest open-data mobile GUI agent" relies on these point estimates being robust, which is currently unproven.

Second, the ablation studies suffer from similar issues. In Table 5 (Evaluator model ablation), the difference between the Gemini 2.5 Pro evaluator (71% Pass@3) and the Qwen3-VL-8B evaluator (70% Pass@3) is marginal (1 percentage point) and based on a small sample size (200 tasks). Without error bars or a statistical test, this difference is indistinguishable from random fluctuation. Similarly, Table 4 shows that changing the task filtering strategy results in identical AndroidWorld scores (48.3%) but divergent MobileWorld scores. This suggests the AndroidWorld metric may lack the sensitivity to detect the nuances of the training data changes, or the results are unstable.

Finally, the "Curriculum grounding" ablation (Table 6) compares functional coverage percentages but does not link these coverage metrics directly to performance gains with statistical backing. While the shift in distribution is clear, the causal link between specific functional coverage increases and the final success rates needs more rigorous quantification beyond the provided tables.

To meet the standards of scientific evidence, the authors should re-run key experiments with multiple seeds to report variance, or at minimum, provide a power analysis or bootstrap confidence intervals for the reported metrics. The current evidence supports the *direction* of the improvement but not the *statistical certainty* of the claims.
