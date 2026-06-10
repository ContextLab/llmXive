---
action_items:
- id: 48228e810ff8
  severity: science
  text: Report standard deviations or 95% confidence intervals for all metrics in
    Table 1 (Section 6.1) to quantify variance over the three independent runs mentioned
    in the caption.
- id: 4a796f027136
  severity: science
  text: Include statistical significance tests (e.g., bootstrap or paired t-test)
    for comparisons between TIDE and baselines to support claims of 'consistent outperformance'.
- id: e5edb64c74d6
  severity: writing
  text: Clarify the random seeds and temperature settings for the LLM judge (GPT-5
    mini) to ensure reproducibility of the evaluation scores.
artifact_hash: ba0baa17db4681e44851057971abf7e28abd129eef36849b4fb4fc0aac6085dd
artifact_path: projects/PROJ-669-tide-proactive-multi-problem-discovery-v/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-10T10:57:58.756836Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in Section 5 and Section 6 requires strengthening to support the paper's claims of robust performance. While the experimental design compares TIDE against appropriate baselines (Single-Agent, Multi-Agent) across two settings and four LLMs, the reporting of results lacks necessary statistical rigor.

First, Table 1 (`tab_main.tex`) presents point estimates for Coverage and F1 but omits measures of variance. The caption states results are averaged over "three independent runs," yet standard deviations or confidence intervals are not reported. Given the stochastic nature of LLM inference and the LLM-based judge (G-Eval), variance is expected. Without error bars or confidence intervals, it is difficult to assess whether the observed differences (e.g., Workspace Retrieval Cov: 69.06 vs. 47.60 for GPT) are statistically reliable or within the noise margin of the evaluation protocol.

Second, the paper claims TIDE "consistently outperforms" baselines (Abstract, Section 6.1) without reporting statistical significance tests. With 24 comparisons in Table 1 alone (4 models × 3 baselines × 3 metrics × 2 settings, though aggregated), the risk of Type I errors is non-negligible. I recommend adding bootstrap resampling or paired t-tests over the 30 workspace and 20 repository instances to validate that the improvements are significant at a standard alpha level (e.g., p < 0.05), potentially with a correction for multiple comparisons (e.g., Bonferroni or FDR).

Third, the evaluation relies on an LLM judge (GPT-5 mini). Section 5.3 describes the metric aggregation but does not specify the judge's sampling temperature or the number of votes per instance. To ensure reproducibility, the prompt temperature and seed should be fixed and reported in the Implementation Details (Section 5.4).

Finally, the F1 definition in Section 5.3 is custom (harmonic mean of coverage and matched score over predictions). While acceptable, the statistical properties of this metric should be briefly discussed, particularly regarding its sensitivity to the number of gold vs. predicted problems. Adding these statistical controls will significantly bolster the empirical claims.
