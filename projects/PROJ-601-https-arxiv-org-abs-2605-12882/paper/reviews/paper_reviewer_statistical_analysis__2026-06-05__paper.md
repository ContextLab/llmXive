---
action_items:
- id: 591006ab0b4d
  severity: science
  text: Compute 95% confidence intervals for all metrics in Table 2 (SAA, Recall,
    etc.) using bootstrap or analytical methods given N=1897. Perform pairwise significance
    testing (e.g., bootstrap t-test) for top model comparisons to substantiate 'best'
    claims.
- id: aa5450bd8869
  severity: science
  text: Address multiple-comparisons handling when highlighting 'best' and 'second-best'
    across 20 models. Explicitly state if corrections (e.g., Bonferroni, FDR) were
    applied to avoid false positives in ranking.
artifact_hash: 343bba3cbfbb16bee3f79c8a33c3a51555292623f2cdbd016ca7ae51e6fbc39c
artifact_path: projects/PROJ-601-https-arxiv-org-abs-2605-12882/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-05T21:43:08.454567Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical rigor of the benchmark evaluation requires strengthening to support the strong claims regarding model superiority and the "Attribution Hallucination" phenomenon.

**Metric Definitions and Variance:** While Section 4.1 (Evaluation Metrics) clearly defines the formulas for Recall, Relevance, and SAA, the reported results in Table 2 (Main Results) lack measures of variance (standard deviation or standard error). With N=1,897 questions, point estimates are stable, but without Confidence Intervals (CIs), it is impossible to determine if the observed differences between models (e.g., Gemini-3.1-Pro SAA 76.0 vs. Gemini-3-Flash SAA 69.3) are statistically significant or within the margin of error. The current presentation treats these point estimates as absolute truths.

**Multiple Comparisons:** The paper evaluates 20 models, resulting in 190 pairwise comparisons. Table 2 highlights the "best" and "second-best" results for each metric. However, there is no mention of multiple-comparisons correction (e.g., Bonferroni or False Discovery Rate). Highlighting top performers without statistical adjustment inflates the risk of Type I errors, potentially misranking models based on noise.

**Judge Variance:** The Relevance and Answer Correctness metrics rely on LLM judges ($\mathcal{J}_{\text{rel}}$, $\mathcal{J}_{\text{ans}}$). Appendix "Analysis of Different Judges" uses the Friedman test to validate judges against humans (p > 0.05), which is appropriate. However, this variance is not propagated into the main model scores. The uncertainty introduced by the LLM judge should ideally be reflected in the main metrics, or at least acknowledged as a source of noise in the SAA calculation.

**Recommendations:** To meet statistical standards for benchmarking, please calculate 95% CIs for all aggregated metrics in Table 2 using bootstrap resampling (e.g., 1000 iterations). Additionally, apply pairwise significance testing for the top model rankings and explicitly state if multiple-comparison corrections were applied. This will substantiate the claim that one model is statistically superior to another rather than just numerically higher.
