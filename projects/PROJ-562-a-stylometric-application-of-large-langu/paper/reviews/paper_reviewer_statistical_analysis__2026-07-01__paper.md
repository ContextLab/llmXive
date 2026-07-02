---
action_items:
- id: 835b00148662
  severity: writing
  text: Table 1 reports non-integer degrees of freedom (e.g., 31.53) for t-tests with
    n=10 seeds, implying Welch's t-test was used. The manuscript must explicitly state
    that Welch's correction was applied to justify these values and the assumption
    of unequal variances.
- id: 94b1f40749d3
  severity: science
  text: Ablation comparisons (e.g., intact vs. content-only) use the same 10 seeds,
    creating paired data. However, reported df values (e.g., 11.77) suggest independent
    Welch's t-tests were used. Re-analyze using paired t-tests or repeated-measures
    ANOVA to correctly model dependencies and increase power.
- id: e35353e4789a
  severity: writing
  text: The claim of '100% accuracy' is based on n=10 seeds. The 95% Clopper-Pearson
    confidence interval for this proportion is approx [0.74, 1.0]. Report this interval
    or qualify the claim to acknowledge the uncertainty inherent in the small sample
    size.
artifact_hash: 148021f63314c6cbe2b6159eaaaecc4e6c793ec5541ddbe74681664a10cdde19
artifact_path: projects/PROJ-562-a-stylometric-application-of-large-langu/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T21:25:10.068221Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in the manuscript is generally robust, utilizing cross-entropy loss distributions from 10 random seeds to enable parametric testing. However, specific issues regarding test selection and reporting require correction to ensure statistical rigor.

First, Table 1 and the Results section report non-integer degrees of freedom (e.g., df=31.53 for Baum) for comparisons involving 10 seeds. This indicates the use of Welch's t-test, which does not assume equal variances. The manuscript currently fails to explicitly state that Welch's correction was applied. The text must be updated to clarify that "Welch's t-tests were performed to account for potential heterogeneity of variance," justifying the non-integer df values.

Second, the ablation studies (Section 3.4) compare models trained on different corpus types (intact, content-only, etc.) using the same 10 random seeds. This design creates paired (dependent) data. However, the reported statistics (e.g., "t(11.77) = 3.21") imply the use of independent Welch's t-tests. Applying an independent test to paired data reduces statistical power and may yield incorrect inferences. The authors should re-analyze these comparisons using paired t-tests (df=9) or a repeated-measures ANOVA. If independent tests are retained, a strong justification for treating the seeds as independent across different model architectures is required.

Finally, the claim of "perfect (100%) classification accuracy" relies on a sample size of only 10. The 95% confidence interval for a proportion of 1.0 with n=10 is approximately [0.74, 1.0] (Clopper-Pearson). Presenting this as an absolute fact without acknowledging the wide confidence interval is statistically imprecise. The manuscript should report the confidence interval or phrase the result as "100% accuracy across all 10 random seeds" to accurately reflect the uncertainty.
