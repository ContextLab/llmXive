# Data Model: Evaluating the Impact of Code Generation Models on Code Documentation Completeness

## Overview

This document defines the data structures used in the pipeline. All data is stored in JSON format to ensure reproducibility and ease of parsing. Versioning hashes are recorded in `state/` for every artifact.

## Entities

### 1. MethodSignature
Represents a single public method extracted from a repository.

| Field | Type | Description |
| :--- | :--- | :--- |
| `repo_name` | string | Name of the repository (e.g., "requests"). |
| `file_path` | string | Relative path to the source file within the repo. |
| `method_name` | string | Name of the public method. |
| `parameters` | list[string] | List of parameter names extracted from the AST signature (excluding 'self', 'cls'). |
| `source_code` | string | The raw source code of the method (truncated if necessary). |
| `human_docstring` | string | The existing human-written docstring (or `null` if absent). |

### 2. DocstringPair
Extends `MethodSignature` with the generated docstring and calculated scores.

| Field | Type | Description |
| :--- | :--- | :--- |
| `repo_name` | string | Inherited from `MethodSignature`. |
| `file_path` | string | Inherited. |
| `method_name` | string | Inherited. |
| `parameters` | list[string] | Inherited. |
| `human_docstring` | string | Inherited. |
| `generated_docstring` | string | The LLM-generated docstring. |
| `parameter_coverage_score` | float | Primary metric: (matched params / total params). Range [0.0, 1.0]. Calculated using `docstring_parser`. |
| `semantic_similarity_score` | float | Auxiliary metric: Cosine similarity between human and generated embeddings. Range [-1.0, 1.0]. |
| `generation_status` | string | "success", "timeout", "error". |
| `error_message` | string | Description of error if `generation_status` != "success". |

### 3. RepositoryStats
Aggregated statistics for a single repository.

| Field | Type | Description |
| :--- | :--- | :--- |
| `repo_name` | string | Repository name. |
| `total_methods` | integer | Total methods extracted (fixed number). |
| `successful_generations` | integer | Count of successful generations. |
| `avg_human_coverage` | float | Mean `parameter_coverage_score` for human docstrings (vs AST). |
| `avg_llm_coverage` | float | Mean `parameter_coverage_score` for LLM docstrings. |
| `avg_similarity` | float | Mean `semantic_similarity_score`. |

### 4. GlobalResults
Final aggregated results for the Wilcoxon test.

| Field | Type | Description |
| :--- | :--- | :--- |
| `total_pairs` | integer | Total number of valid pairs (Human vs LLM). |
| `human_scores` | list[float] | List of all human coverage scores. |
| `llm_scores` | list[float] | List of all LLM coverage scores. |
| `wilcoxon_statistic` | float | Test statistic from Wilcoxon signed-rank test. |
| `wilcoxon_p_value` | float | P-value from the test. |
| `significance` | boolean | `true` if p-value < 0.05 AND difference > 0.05 (MES). |
| `execution_time_seconds` | float | Total runtime of the pipeline. |

## Data Flow

1.  **Extraction**: `extract.py` reads repo source -> writes `data/raw/{repo_name}_methods.json` (List of `MethodSignature`).
2.  **Generation**: `generate.py` reads `data/raw/{repo_name}_methods.json` -> writes `data/processed/{repo_name}_results.json` (List of `DocstringPair`).
3.  **Analysis**: `analyze.py` reads all `data/processed/*.json` -> writes `data/processed/global_results.json` (Single `GlobalResults` object).
4.  **Versioning**: Content hashes for all files in `data/` are recorded in `state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml` under `artifact_hashes`.

## Constraints

-   **Max Methods**: 100 per repository (Fixed Sample).
-   **Null Handling**: `human_docstring` must be `null` (JSON null) if missing, not empty string.
-   **Float Precision**: Scores rounded to 4 decimal places.
-   **Encoding**: UTF-8.
-   **Versioning**: Every file in `data/` must be checksummed and recorded in `state/`.