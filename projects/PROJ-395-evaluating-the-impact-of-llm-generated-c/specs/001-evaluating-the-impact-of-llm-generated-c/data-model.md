# Data Model: Evaluating the Impact of LLM-Generated Code on Memory Usage

## Entity Relationship Overview

The data model consists of four core entities: `CodeSolution`, `CodeFeature`, `MemoryMeasurement`, and `StatisticalResult`. These entities flow through the pipeline from raw dataset download to final statistical reporting.

## Entity Definitions

### 1. CodeSolution
Represents a single code artifact (either LLM-generated or Human-written) for a specific benchmark problem.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `problem_id` | String | Unique identifier from the benchmark (e.g., `HumanEval/0`). | Primary Key |
| `source_type` | Enum | `LLM` or `Human`. | Not Null |
| `code_text` | Text | The full source code string. | Not Null |
| `generation_model` | String | Name of the LLM used (e.g., `tinyllama-1.1b`). | Nullable (for Human) |
| `generation_params` | JSON | Parameters used for generation (temp, tokens). | Nullable |
| `syntax_valid` | Boolean | Whether the code parses correctly. | Not Null |
| `error_type` | String | Type of error if invalid (e.g., `SyntaxError`, `Timeout`). | Nullable |

### 2. CodeFeature
Static analysis attributes extracted from a `CodeSolution`.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `solution_id` | String | Foreign Key to `CodeSolution.problem_id` + `source_type`. | Primary Key |
| `lines_of_code` | Integer | Total lines of code (excluding comments/blanks). | ≥ 1 |
| `cyclomatic_complexity` | Integer | McCabe complexity score. | ≥ 1 |
| `library_import_count` | Integer | Number of `import` or `from` statements. | ≥ 0 |
| `memory_per_loc` | Float | Normalized efficiency metric (Peak Memory / LOC). **Descriptive only, excluded from modeling.** | > 0 |

### 3. MemoryMeasurement
The result of profiling a `CodeSolution`.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `measurement_id` | UUID | Unique run identifier. | Primary Key |
| `solution_id` | String | FK to `CodeSolution`. | Not Null |
| `run_number` | Integer | Which of the 3 runs this is (1, 2, or 3). | 1-3 |
| `peak_memory_bytes` | Integer | Peak memory usage in bytes. | 0 to [deferred] (7GB) |
| `steady_state_bytes` | Integer | **Median memory of the final [deferred] of execution steps.** | ≥ 0 |
| `execution_time_ms` | Integer | Duration of execution. | > 0 |
| `status` | Enum | `SUCCESS`, `TIMEOUT`, `OOM`, `SYNTAX_ERROR`. | Not Null |
| `iqr_peak` | Float | Interquartile Range of peak memory across runs. | ≥ 0 |

### 4. StatisticalResult
Aggregated analysis outputs.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `analysis_id` | UUID | Unique analysis run. | Primary Key |
| `test_name` | String | Name of the test (e.g., `KaplanMeier_Peak`). | Not Null |
| `p_value_raw` | Float | Raw p-value. | 0.0 - 1.0 |
| `p_value_corrected` | Float | Holm-Bonferroni corrected p-value. | 0.0 - 1.0 |
| `effect_size` | Float | Rank-Biserial or Log-Rank statistic. | -1.0 to 1.0 |
| `effect_size_category` | String | "Small", "Medium", "Large" based on Cohen's benchmarks. | Nullable |
| `confidence_interval` | String | e.g., "[0.05, 0.15]". | Nullable |
| `sample_size` | Integer | N used for this test. | > 0 |
| `vif_flags` | JSON | List of predictors with VIF > 5. | Nullable |

## Data Flow

1.  **Ingestion**: `HumanEval` dataset → `CodeSolution` (Human).
2.  **Generation**: `CodeSolution` (LLM) created via `generate.py`.
3.  **Profiling**: `CodeSolution` → `MemoryMeasurement` (3 runs).
4.  **Feature Extraction**: `CodeSolution` → `CodeFeature`.
5.  **Aggregation**: `MemoryMeasurement` (median) + `CodeFeature` → `StatisticalResult`.
    -   *Note*: `memory_per_loc` is calculated but **not** passed to regression models.
    -   *Note*: Residualization is applied before comparing groups to control for code size.