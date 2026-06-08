---
action_items:
- id: 2b3faa972803
  severity: science
  text: Add statistical significance tests (e.g. bootstrap confidence intervals) for
    the central 'Prejudice Gap' (51% PR) and the Closed-Open T3 gap (-26.6%) to quantify
    uncertainty.
- id: 2f6f71faf752
  severity: science
  text: Report confidence intervals for the PR/HR metrics across the 27 models to
    assess the stability of the failure-mode rates beyond point estimates.
artifact_hash: 37d4da743146174451c6b81c250d33af63eaf988a8502062dfca5a6325ae068a
artifact_path: projects/PROJ-620-perception-or-prejudice-can-mllms-go-bey/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-08T10:48:51.104450Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

This benchmark paper presents a compelling empirical case for the "Prejudice Gap" in MLLMs, supported by a robust multi-stage annotation pipeline and extensive evaluation across 27 models. The scientific evidence is strengthened by rigorous sensitivity analyses: the threshold sweep in Appendix E confirms HR rankings are stable ($\rho \ge 0.92$) across 27 threshold combinations, and the cross-judge robustness check in Appendix G demonstrates T2 rankings are consistent across different AI judges ($\rho \ge 0.92$). The sample size (1,104 videos, 5,320 MCQs) is sufficient for benchmarking purposes, and the text-leakage filter (Section 5.1) provides a valid control for transcript-based cheating.

However, the central scientific claims rely heavily on population-level point estimates without quantified uncertainty. The headline finding that $\overline{\operatorname{PR}} = 51.3\%$ (Section 6.2) and the ecosystem gap of $\Delta_{T3} = -26.6\%$ (Table 6) are presented as precise facts. Given the variance inherent in model performance and the finite test set size, these estimates should be accompanied by confidence intervals (e.g., via bootstrapping over the 1,104 videos) to establish statistical significance. For instance, is the 26.6% gap between closed and open models statistically distinguishable from zero? Without this, the strength of the evidence for the "gap" being a field-wide phenomenon rather than a sampling artifact is slightly weakened.

Additionally, while the failure-mode rates (PR/CR/IR/HR) are well-defined (Section 4.4), the uncertainty around these rates for individual models is not reported. Table 1 presents these as exact percentages, but a model with HR=33.5% (Gemini 3 Flash) vs HR=28.0% (GPT-5.5) might not be significantly different given the sample size. Reporting confidence intervals for these rates would clarify the discriminative power of the HR metric and the reliability of the leaderboard ranking. These additions would solidify the statistical rigor of the evidence without requiring new experiments.
