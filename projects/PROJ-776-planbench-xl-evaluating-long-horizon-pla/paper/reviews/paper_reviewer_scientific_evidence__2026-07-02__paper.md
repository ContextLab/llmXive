---
action_items:
- id: 9b7412d1a94e
  severity: science
  text: Clarify the statistical basis for the 'strong correlation' claims (e.g., r=0.902
    between Mean EDT and Accuracy). The analysis compares only 10 data points (one
    per model). A Pearson correlation on N=10 is highly susceptible to outliers and
    lacks statistical power. Please report p-values, confidence intervals for the
    correlation coefficients, or justify the claim with a more robust statistical
    test.
- id: 3c634bc05891
  severity: science
  text: Address the potential circularity in the 'progress call' definition used for
    error analysis. A call is 'progress' if it produces a value needed by a ground-truth
    path. However, if the ground-truth path is not unique or if the agent finds a
    valid alternative path not in the original ground-truth set, this metric may penalize
    valid recovery. Explicitly state how alternative valid paths are handled in the
    error annotation.
- id: f9c69b197733
  severity: science
  text: Provide the standard deviation or variance for the accuracy metrics in Table
    3, not just the 95% confidence interval radius. While the radius is provided in
    Table 2, the raw variance is necessary to assess the stability of the performance
    differences between models (e.g., the gap between Gemini-3.1-Pro and GPT-5.4)
    and to verify if the differences are statistically significant beyond the bootstrap
    intervals.
artifact_hash: 0fb9253adef42dcbc903c972875abcf8435cbde0a29a43054fe5430b0edd419c
artifact_path: projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T13:34:39.516896Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling benchmark for long-horizon planning under retrieval constraints, supported by a substantial dataset (327 tasks, 1,665 tools) and a rigorous experimental setup involving 10 diverse LLMs. The use of bootstrap resampling (10,000 iterations) to generate confidence intervals for the primary metrics (Table 2) is a strong methodological choice that enhances the reliability of the reported performance bounds. The error analysis, particularly the categorization of "Irrecoverable Drift," offers valuable qualitative evidence regarding agent failure modes.

However, the statistical evidence supporting the correlation claims in Section 4.2 requires strengthening. The authors report strong Pearson correlations (e.g., r=0.902 between Mean EDT and Accuracy) based on a sample size of N=10 (one data point per model). In statistical terms, a correlation coefficient derived from only 10 observations is highly sensitive to outliers and lacks the power to definitively establish a linear relationship without reporting p-values or confidence intervals for the correlation itself. While the trend is visually plausible, the claim of a "strong correlation" is statistically tenuous at this sample size. The authors should either provide the p-values and confidence intervals for these correlation coefficients or temper the language to reflect the exploratory nature of these findings given the limited N.

Additionally, the definition of "progress calls" in the error analysis (Section 6.1) relies on the existence of a ground-truth path. The paper mentions that tasks are constructed to have solvable paths, but it does not explicitly address how the metric handles cases where an agent discovers a *valid* alternative path that differs from the specific ground-truth path used for annotation. If an agent successfully solves a task via a novel path not in the original ground-truth set, but the metric penalizes steps that deviate from the specific ground-truth sequence, the "progress" metric could be biased. Clarifying the handling of alternative valid solution paths in the error annotation protocol is necessary to ensure the validity of the "Irrecoverable Drift" conclusions.

Finally, while Table 2 provides 95% confidence interval radii, the raw standard deviations or variances for the accuracy metrics in Table 3 are not explicitly listed. Including these would allow for a more direct assessment of the statistical significance of the performance gaps between top-performing models (e.g., the ~25% gap between Gemini-3.1-Pro and GPT-5.4) and would complement the bootstrap analysis.
