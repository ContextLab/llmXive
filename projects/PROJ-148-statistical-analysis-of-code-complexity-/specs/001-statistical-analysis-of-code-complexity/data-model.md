# Data Model: Statistical Analysis of Code Complexity Metrics and Bug Prediction

## Core Entities

### FunctionMetric
Represents a single Java function/method together with its static‑analysis metrics and outcome label.

| Attribute | Type | Description |
|-----------|------|-------------|
| `file_path` | string | Relative path to the `.java` source file |
| `function_name` | string | Name of the function or method |
| `start_line` | integer | Starting line number (1‑based) |
| `end_line` | integer | Ending line number (1‑based) |
| `cyclomatic_complexity` | integer | Cyclomatic complexity (non‑negative) |
| `loc` | integer | Lines of Code (non‑negative) |
| `token_count` | integer | Number of lexical tokens (non‑negative) |
| `nesting_depth` | integer | Maximum nesting depth (non‑negative) |
| `halstead_volume` | float | Halstead Volume |
| `bug_label` | integer (0/1) | 1 = function modified in a bug‑fix commit, 0 = otherwise |
| `project_id` | string | Identifier of the originating repository |