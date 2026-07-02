---
action_items:
- id: f4fbbea39db6
  severity: science
  text: "The claim that the public subset is representative of the full pool relies\
    \ on a single correlation (r=0.89) for one agent configuration (Appendix~\ref{app:fullpool}).\
    \ Validate this across multiple models or explicitly discuss the limitation."
- id: b64f5ffda2af
  severity: science
  text: "The failure taxonomy relies on an LLM classifier without reported inter-rater\
    \ reliability or human validation (Appendix~\ref{app:failure-taxonomy}). Add reliability\
    \ metrics to support the conclusion that 'Understanding' errors dominate."
- id: 94e097ce3b47
  severity: science
  text: "Table~\ref{tab:main-results} reports standard deviations from repeated runs\
    \ of single instances but lacks variance across the 150 diverse tasks. Report\
    \ standard error of the mean across tasks to assess statistical significance of\
    \ harness differences."
artifact_hash: 326ff13c3b60fc13345363439d3391333425191b488bb3324c7d31083263c3e8
artifact_path: projects/PROJ-688-agents-last-exam/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T03:12:13.558317Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a large-scale benchmark (ALE) with 150 public task instances and extensive experimental results. The scientific evidence regarding the benchmark's construction and the magnitude of current agent failures is generally strong, supported by a clear taxonomy and deterministic evaluation modes. However, there are specific gaps in the statistical rigor and validation of the analytical claims that require attention.

First, the claim that the public subset of tasks is representative of the full private pool (Appendix~\ref{app:fullpool}) is supported by a scatter plot showing a Pearson correlation of $r=0.89$ between pass rates on the public and full sets. Crucially, this analysis is performed for only **one** agent configuration (Claude Code + Opus 4.7). It is not demonstrated whether this correlation holds for other models or harnesses, which is a significant limitation given the paper's goal of providing a general evaluation instrument. The authors should either extend this analysis to multiple configurations or explicitly qualify the claim as specific to the tested configuration.

Second, the failure taxonomy analysis (Section~\ref{sec:experiment-analysis}, Appendix~\ref{app:failure-taxonomy}) relies entirely on an LLM (OpenAI Codex) to classify the root causes of agent failures into categories like "Understanding," "Approach," and "Execution." The manuscript does not provide any measure of inter-rater reliability (e.g., Cohen's kappa) or a human validation study to verify the accuracy of these automated classifications. Given that the paper draws major conclusions about the nature of current agent limitations (e.g., "dominant bottleneck is domain knowledge") from this taxonomy, the lack of validation for the classification method weakens the evidentiary support for these claims.

Finally, while Table~\ref{tab:main-results} reports standard deviations for a subset of runs, these appear to be derived from repeating the same task instance a few times rather than capturing the variance across the diverse set of 150 tasks. For a benchmark with such heterogeneous tasks, the standard error of the mean across tasks or the distribution of scores per task is essential to determine if the observed differences between harnesses (e.g., the 1-2% gaps) are statistically significant or within the noise of task difficulty variance. The current reporting makes it difficult to assess the robustness of the comparative results.
