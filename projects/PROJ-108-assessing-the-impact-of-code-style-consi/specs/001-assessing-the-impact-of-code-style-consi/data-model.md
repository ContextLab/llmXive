# Data Model: Assessing the Impact of Code Style Consistency on LLM Code Understanding

## Entity Definitions

### CodeSample
Represents a single unit of analysis.
- `file_path`: string (unique identifier)
- `source_code`: string (raw code content)
- `style_score`: float (0.0 to 1.0, normalized)
- `consistency_group`: string (enum: "High", "Medium", "Low")
- `file_size_lines`: float (proxy for complexity, to avoid multicollinearity with style metrics)
- `file_age_days`: float (computed from git history or null if unavailable)
- `dataset_source`: string (e.g., "codesearchnet", "defects4j")

### InferenceResult
Represents the output of the LLM for a specific sample.
- `sample_id`: string (foreign key to CodeSample)
- `model_version`: string (e.g., "starcoder-1b")
- `generated_summary`: string (max 64 tokens)
- `predicted_bug_line`: int (or null)
- `inference_time_ms`: float
- `status`: string (enum: "success", "timeout", "oom", "error")

### PerformanceMetric
Quantitative evaluation linking InferenceResult to Ground Truth.
- `result_id`: string (foreign key to InferenceResult)
- `task_type`: string (enum: "summarization", "bug_localization")
- `bleu_score`: float (or null if no reference)
- `precision`: float
- `recall`: float
- `f1_score`: float
- `ground_truth_exists`: boolean

### StatisticalReport
Aggregated results of the analysis.
- `report_id`: string
- `test_type`: string (enum: "ancova", "t_test", "correlation", "regression")
- `test_statistic`: float (F or t value)
- `p_value`: float
- `effect_size`: float (Cohen's d or eta-squared)
- `confidence_interval_lower`: float
- `confidence_interval_upper`: float
- `covariate_coefficients`: object (e.g., {"file_size": 0.5})
- `correction_applied`: string (e.g., "bonferroni")
- `power_estimate`: float (Achieved power, not post-hoc)
- `r_squared`: float (for regression analysis)
- `conclusion`: string

## Relationships
- `CodeSample` (1) --> (N) `InferenceResult`
- `InferenceResult` (1) --> (1) `PerformanceMetric`
- `StatisticalReport` aggregates multiple `PerformanceMetric` instances grouped by `consistency_group`.