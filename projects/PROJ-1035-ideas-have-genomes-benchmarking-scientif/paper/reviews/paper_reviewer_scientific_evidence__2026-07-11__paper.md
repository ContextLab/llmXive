---
action_items:
- id: 865b3798aa8a
  severity: writing
  text: The paper presents a novel benchmark for scientific lineage reasoning, but
    the evidentiary strength of the experimental results is currently insufficient
    to support the specific claims of system differentiation and ranking stability.
    The primary concern is the complete absence of variance reporting in the main
    results. Table 1 presents exact accuracy scores for 14 different systems on the
    \geneexam{} benchmark (1,029 instances) as single point estimates (e.g., 27.3%
    for Claude Code vs 23.1% for
artifact_hash: 3ad519eab3effcd18457f63d397b7e31c9b86e08766b51b9bcdd374f35279468
artifact_path: projects/PROJ-1035-ideas-have-genomes-benchmarking-scientif/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-11T02:53:23.094228Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a novel benchmark for scientific lineage reasoning, but the evidentiary strength of the experimental results is currently insufficient to support the specific claims of system differentiation and ranking stability.

The primary concern is the complete absence of variance reporting in the main results. Table 1 presents exact accuracy scores for 14 different systems on the \geneexam{} benchmark (1,029 instances) as single point estimates (e.g., 27.3% for Claude Code vs 23.1% for GPT-5.5). In LLM evaluation, performance on a fixed test set can fluctuate significantly based on random seed, temperature, or prompt phrasing. A difference of 1-2 percentage points is well within the margin of error for a single run on a dataset of this size. Without reporting standard deviations across multiple seeds or confidence intervals, the claim that "structured lineage context reshuffles system rankings" (Section 5.3) is not statistically grounded. The observed ranking changes could easily be artifacts of a lucky seed for one system and an unlucky one for another, rather than a genuine effect of the lineage context.

Similarly, the \genearena{} results rely on a Population-Evolution Score (PES) derived from a panel of three model judges. The paper reports Krippendorff's $\alpha$ for agreement but does not report the variance of the PES scores themselves across different judge seeds or runs. If the judge panel's scoring is noisy, the small differences in reported PES (e.g., 86.5 vs 86.7) are uninterpretable. The claim that "Variation and Selection stay nearly constant... while Heredity explains the gap" requires evidence that these sub-scores are stable across runs, not just that they are constant in a single snapshot.

To close this gap, the authors must report results across at least 3-5 random seeds for both the \geneexam{} and \genearena{} evaluations. This should include mean $\pm$ standard deviation for all accuracy and PES metrics. Additionally, the stability of the system rankings should be verified; if the ranking changes significantly across seeds, the claim of a "reshuffle" is not robust. Finally, the variance of the judge panel's scores should be reported to ensure that the PES metric is distinguishing signal from noise. Without these additions, the reported "compositional bottleneck" and specific system comparisons remain suggestive but not conclusive.
