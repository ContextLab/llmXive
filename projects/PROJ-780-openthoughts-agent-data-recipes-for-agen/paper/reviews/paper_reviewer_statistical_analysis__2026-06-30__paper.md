---
action_items:
- id: fae291a4c002
  severity: science
  text: Report p-values or confidence intervals for all benchmark comparisons (e.g.,
    Table 1). Claims of superiority (e.g., Top-4 vs Top-2) lack statistical significance
    testing across the n=3 runs.
- id: 4c4320a97604
  severity: science
  text: Address the multiple-comparisons problem in the >100 ablation study (Section
    3.1). Apply corrections (e.g., Bonferroni) to p-values or explicitly label results
    as exploratory to avoid false positives.
- id: 2f4404317a05
  severity: science
  text: Provide formal statistical tests (e.g., ANOVA) for scaling claims in Figure
    2. Visual error bar overlap suggests the 'plateau' vs 'improvement' distinction
    may not be significant without trend analysis.
- id: 19c0c0b83814
  severity: science
  text: Quantify uncertainty for the teacher model drop (Section 3.5). A confidence
    interval for the ~5pp difference is required to validate the claim that GPT-5.3
    is a worse teacher.
artifact_hash: 1762f575d6ad502232c74311f4c0e12a6d2ed21a38bf5e7d1493821d45367039
artifact_path: projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T18:54:59.720071Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents an extensive empirical study of data recipes for agentic models, but the statistical rigor is insufficient to support the strength of the claims.

First, while standard errors (SE) are reported for benchmark scores (e.g., Table 1, 2, 3), no statistical significance tests are performed. For instance, in Table 1, the difference between "Top 4" (29.33 ± 1.63) and "Top 2" (29.00 ± 1.60) on SWE-Bench is small relative to the SE. Without paired t-tests or non-parametric equivalents across the three runs, it is impossible to distinguish signal from noise. Claims of "best performance" require p-values or confidence intervals.

Second, the study involves >100 ablations and 95 task generation strategies. The paper ignores the multiple-comparisons problem. With 95 hypotheses tested, the probability of false positives is high. Authors must apply corrections (e.g., Bonferroni or Benjamini-Hochberg) or explicitly state results are exploratory.

Third, the scaling claims in Figure 2 lack statistical backing. The assertion that Method 1 "plateaus" while Method 3 "improves" relies on visual inspection. Given error bar overlap between 31.6K and 100K for Method 1, a formal test for trend or slope comparison is necessary to reject the null hypothesis of constant performance.

Finally, the conclusion regarding the "worse teacher" model (Section 3.5) cites a ~5pp drop without quantifying uncertainty. A confidence interval for the difference in means is needed to validate this conclusion.

To resolve these issues, the authors must: (1) perform and report statistical significance tests for all key comparisons; (2) apply multiple-comparison corrections; and (3) provide confidence intervals for all reported performance differences.
