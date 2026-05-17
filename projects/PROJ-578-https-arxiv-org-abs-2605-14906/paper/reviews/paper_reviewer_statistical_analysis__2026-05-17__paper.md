---
artifact_hash: d50a4f0b1e568c7504bc9f36b9def267fba709bab11751ed7e3ec317ba0682a2
artifact_path: projects/PROJ-578-https-arxiv-org-abs-2605-14906/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:17:17.038294Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The evaluation framework employs LLM-as-Judge with cross-validation (Appendix \ref{app:judge_validation}), which is appropriate for the task. However, the statistical rigor of the comparative analysis requires strengthening to support the reported rankings and degradation claims.

1. **Significance Testing:** Claims regarding model performance differences (Section 4.2, e.g., "degrades least overall (a 2.11% drop)") lack hypothesis testing. With $N=789$, accuracy differences under 5% may not be statistically significant. Please apply McNemar's test or bootstrap hypothesis testing for pairwise model comparisons to validate ranking claims.

2. **Confidence Intervals:** Figure \ref{fig:context_degradation} reports 95% CI bands, but the caption specifies these are for "LVLM average" and "agent average". This aggregates variance across models, obscuring individual model uncertainty. Per-model confidence intervals are necessary to support specific claims about degradation rates (e.g., GLM-4.6V AR drop).

3. **Multiple Comparisons:** The study evaluates 27 models across 5 types and 4 contexts (540+ comparisons). No correction for multiple comparisons (e.g., FDR or Bonferroni) is noted when identifying top performers or significant gaps. This increases Type I error risk.

4. **Agent Subset Uncertainty:** Appendix \ref{app:canonical195} provides bootstrap CIs for the 195-question subset ($\pm 6%$). However, intervals for text-only agents overlap significantly (e.g., Mem0 vs. Memory-T1 at 32K). The text claims text-only pipelines are "uniformly above" multimodal ones, but overlapping CIs suggest these differences may not be robust. Clarify if pairwise differences are statistically significant.

Reproducibility is supported by code release, but statistical scripts (e.g., for CIs and tests) should be explicitly included in the repository.
