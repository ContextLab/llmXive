# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 6 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The primary metric, *Parameter Coverage Score*, only measures whether parameter names appear in the docstring. This operationalisation does not fully capture the construct of *documentation completeness*, which also includes descriptions of return values, exceptions, and overall narrative quality. Relying solely on parameter name overlap may misclassify a docstring as complete when it merely lists parameters without meaningful explanation.
- The study samples the top‑20 PyPI repositories, which are likely to have higher‑quality human docstrings than average. This selection bias could confound the comparison, as LLM‑generated docstrings may appear relatively weaker simply because the human baseline is unusually strong. The plan does not include a strategy to mitigate or acknowledge this potential confound.
- The plan references FR‑007 (implicit deterministic generation) in the Generation phase, but FR‑007 does not exist in the specification. This constitutes an over‑reach beyond the defined functional requirements.
- Success Criterion SC‑003 (semantic similarity measurement) is listed in the specification but is not mapped to any phase or task in the plan’s coverage table, leaving it unaddressed.
- The `dataset.schema.yaml` contract defines required fields `generation_status` and `error_message` for each DocstringPair, but the plan’s Generation phase only mentions a `generated_docstring` field (and later a `coverage_score`). No provision is made to record generation status or error details, causing a contract mismatch.
- The `results.schema.yaml` contract expects a `GlobalResults` object with fields `total_pairs`, `human_scores`, `llm_scores`, `wilcoxon_statistic`, `wilcoxon_p_value`, `significance`, and `execution_time_seconds`. The plan’s final report schema instead provides `total_methods`, `human_coverage_mean`, `llm_coverage_mean`, `wilcoxon_statistic`, `wilcoxon_pvalue`, and `small_sample_warning`, which do not satisfy the contract’s required structure.
