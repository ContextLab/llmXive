---
action_items:
- id: b1c2e9d2ea41
  severity: science
  text: Report statistical significance for the reported performance gains (e.g.,
    +0.19 on SWE-Bench Pro). The paper presents point estimates in Table 1 but lacks
    confidence intervals, p-values, or variance estimates across multiple random seeds
    to confirm the gains are not due to stochasticity.
- id: f9c5da471cab
  severity: science
  text: Clarify the statistical basis for the 'Best-of-N' selection. The paper reports
    a single 'Chosen' score in Table 4 against a 'Mean' and 'Lowest', but does not
    specify if the 'Mean' is derived from a distribution of N=3 candidates across
    multiple seeds or a single run. Re-run experiments with multiple seeds to provide
    standard deviations for all reported metrics.
- id: 72d45c1a935e
  severity: science
  text: The coreset selection uses a DPP with a fixed weight theta=0.7. Provide a
    sensitivity analysis or justification for this specific hyperparameter choice.
    Without reporting performance variance across different theta values, the robustness
    of the coreset selection strategy remains unverified.
artifact_hash: 1dfb81df34347455cd78b0f836bbc4b7178b6fbb2681f9f18e5c917a00048d5b
artifact_path: projects/PROJ-690-evolving-agents-in-the-dark-retrospectiv/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T07:19:48.100253Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a novel framework for retrospective harness optimization, but the statistical rigor of the reported results is insufficient to support the strong claims of consistent improvement.

**Lack of Variance and Significance Testing:**
The primary results in Table 1 (Main Results) and Table 4 (Best-of-N) report single point estimates (e.g., 0.78 vs 0.59 for SWE-Bench Pro). In LLM agent evaluation, performance is highly stochastic due to sampling variance and non-deterministic environments. The paper fails to report standard deviations, confidence intervals, or results from multiple independent runs (seeds). Without this, it is impossible to determine if the observed +0.19 improvement is statistically significant or an artifact of a single lucky run. The "Mean" and "Std" columns in Table 4 are ambiguous; it is unclear if these are calculated over the N=3 candidates in a single run or over multiple experimental seeds. If the latter, the sample size (N=3) is likely too small to estimate population variance reliably.

**Hyperparameter Sensitivity:**
The coreset selection relies on a Determinantal Point Process (DPP) with a fixed difficulty/diversity trade-off parameter $\theta=0.7$ (Section 5.1, Appendix Table 1). The paper asserts this balances difficulty and diversity but provides no ablation study or sensitivity analysis showing how performance varies with $\theta$. A single hyperparameter setting without variance reporting suggests the results may not be robust.

**Best-of-N Selection Bias:**
The "Best-of-N" strategy (Section 5.3) selects the candidate with the highest self-preference score. The paper reports that the "Chosen" candidate outperforms the "Lowest" (Table 4), but this is a tautological result of selection. The critical statistical question is whether the *selected* candidate generalizes to the held-out test set better than the baseline *on average* across multiple seeds. The current presentation conflates the selection mechanism's internal score with external test performance without providing the necessary distributional data.

**Recommendation:**
The authors must re-run the experiments with at least 3-5 independent random seeds for all datasets. They should report mean $\pm$ standard deviation for all pass rates in Table 1 and Table 4. A statistical test (e.g., paired t-test or bootstrap) should be performed to confirm the significance of the improvements over baselines. Additionally, a sensitivity analysis for the DPP weight $\theta$ is required to demonstrate the robustness of the coreset selection.
