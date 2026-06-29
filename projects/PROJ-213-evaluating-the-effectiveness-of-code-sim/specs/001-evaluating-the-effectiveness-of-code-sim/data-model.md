# Data Model: Evaluating the Effectiveness of Code Simplification on LLM Performance

## Entity Definitions

### HumanEvalProblem

Represents a single HumanEval benchmark item.

| Field | Type | Description |
|-------|------|-------------|
| problem_id | string | Unique identifier (e.g., "HumanEval/0") |
| prompt_code | string | Original code snippet (prompt) |
| reference_solution | string | Reference solution code |
| test_harness | string | Unit test code for validation |

### SimplifiedProblem

Derived from HumanEvalProblem after AST transformation.

| Field | Type | Description |
|-------|------|-------------|
| problem_id | string | Same as source HumanEvalProblem |
| simplified_code | string | AST-transformed code (dead-code removed, boolean reduced) |
| parse_success | boolean | True if AST parsing succeeded |
| semantic_preserved | boolean | True if test harness passes on simplified code |
| parse_error | string | Error message if parse failed (nullable) |
| semantic_error | string | Error message if semantics changed (nullable) |

### InferenceResult

Captures inference metrics for a single problem.

| Field | Type | Description |
|-------|------|-------------|
| problem_id | string | Unique identifier |
| input_type | enum | "raw" or "simplified" |
| pass_1 | boolean | True if generated code passes test harness |
| token_count | integer | Total tokens in input prompt |
| inference_time_ms | float | Wall-clock inference time in milliseconds |
| status | enum | "success", "timeout", "error" |
| error_message | string | Error details if status != "success" (nullable) |

### ParseFailure

Logged when AST parsing fails.

| Field | Type | Description |
|-------|------|-------------|
| problem_id | string | Unique identifier |
| error_type | string | AST parsing error category |
| timestamp | datetime | When failure occurred |
| stack_trace | string | Truncated stack trace snippet |

### FlaggedSnippet

Logged when simplification alters semantics.

| Field | Type | Description |
|-------|------|-------------|
| problem_id | string | Unique identifier |
| error_type | string | Semantic change category (e.g., "syntax_error", "test_failure") |
| code_diff | string | Diff between original and simplified code |

## File Formats

### metrics_raw.csv

| Column | Type | Description |
|--------|------|-------------|
| problem_id | string | Unique identifier |
| input_type | string | "raw" |
| pass_1 | boolean | Pass@1 result |
| token_count | integer | Input token count |
| inference_time_ms | float | Inference time in ms |
| status | string | "success", "timeout", "error" |

### metrics_simplified.csv

| Column | Type | Description |
|--------|------|-------------|
| problem_id | string | Unique identifier |
| input_type | string | "simplified" |
| pass_1 | boolean | Pass@1 result |
| token_count | integer | Input token count |
| inference_time_ms | float | Inference time in ms |
| status | string | "success", "timeout", "error" |

### parse_failures.log

| Field | Type | Description |
|-------|------|-------------|
| problem_id | string | Unique identifier |
| error_type | string | AST error category |
| timestamp | datetime | Failure time |
| stack_trace | string | Truncated trace |

### flagged_snippets.csv

| Column | Type | Description |
|--------|------|-------------|
| problem_id | string | Unique identifier |
| error_type | string | Semantic change category |
| code_diff | string | Original vs. simplified diff |

## Data Flow

```
HumanEval (raw) → download.py → data/raw/humaneval.jsonl
                                ↓
                        simplify.py → data/processed/simplified/
                                ↓
                        inference.py → data/processed/metrics_*.csv
                                ↓
                        analyze.py → analysis_report.pdf
```
