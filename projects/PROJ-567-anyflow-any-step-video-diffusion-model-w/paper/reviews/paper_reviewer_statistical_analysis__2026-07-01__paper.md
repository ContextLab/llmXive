---
action_items:
- id: 6394e1bca57c
  severity: science
  text: The manuscript claims statistical significance via paired t-tests with Bonferroni
    correction (Section 5, 'Statistical significance' paragraph) but fails to report
    the resulting p-values, t-statistics, or degrees of freedom. Without these values,
    the claim of significance is unverifiable.
- id: a1d49b874c4d
  severity: science
  text: The evaluation protocol states 200 prompts with 3 seeds (600 videos) for VBench.
    However, the reported scores in Tables 1-3 are single point estimates (e.g., 84.05)
    without the standard deviation or 95% confidence intervals explicitly listed in
    the tables, despite the text claiming they are reported. The tables must include
    these variance metrics to assess the robustness of the improvements.
- id: fcf85d3fb590
  severity: science
  text: The comparison of AnyFlow against baselines (e.g., rCM, Krea-Realtime) mixes
    re-evaluated results with scores 'taken directly from original papers' (Section
    5, 'Evaluation Setting'). This introduces potential confounding variables (different
    hardware, random seeds, or prompt sets) that invalidate the paired t-test assumption
    of identical conditions. A unified re-evaluation of all baselines is required.
artifact_hash: 3aad81d8a133042c5a798b8bf30d90974b62e8f4dc5a0e7e17e6ccdaa711ef9d
artifact_path: projects/PROJ-567-anyflow-any-step-video-diffusion-model-w/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:05:05.149694Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis presented in Section 5 contains critical omissions that prevent the verification of the paper's central claims regarding performance improvements.

First, while the text explicitly states that "All reported improvements are evaluated with paired t-tests and Bonferroni correction" (Section 5, paragraph starting "Statistical significance"), the manuscript fails to provide the necessary statistical evidence. No p-values, t-statistics, or degrees of freedom are reported in the text or tables. Without these values, the assertion that the improvements are statistically significant is unsubstantiated. The authors must report the specific p-values for the comparisons in Tables 1, 2, and 3 to validate the use of the t-test.

Second, there is a discrepancy between the text and the tables regarding uncertainty quantification. The text mentions reporting "mean ± standard deviation and 95% confidence intervals in Table 4" (likely referring to the main results tables, though the numbering is ambiguous). However, Tables `t2v_comparison`, `i2v_comparison`, and `ablation_anyflow` present only single point estimates (e.g., 84.05, 87.87). The absence of standard deviations or confidence intervals in the tables makes it impossible to visually assess the overlap between distributions or the stability of the reported gains across the three random seeds.

Third, the experimental design for the main comparisons introduces a potential confound. The authors state that baseline scores for methods like rCM and Krea-Realtime were "taken directly from their original papers" (Section 5, 'Evaluation Setting'), while AnyFlow was re-evaluated. Even if the prompt sets are identical, differences in random seeds, hardware environments, or implementation details between the original papers and the current re-evaluation violate the assumption of a controlled paired comparison required for a valid t-test. To ensure the statistical validity of the "outperforming" claims, all baselines must be re-evaluated under the exact same protocol (same seeds, same hardware, same prompt set) as AnyFlow.

Finally, the sample size of 200 prompts (600 total videos) is reasonable, but the power of the test depends on the variance of the VBench scores. Given that VBench scores are often bounded and potentially non-normally distributed, the authors should verify the normality assumption of the t-test or consider non-parametric alternatives (e.g., Wilcoxon signed-rank test) if the data distribution is skewed, and report the results accordingly.
