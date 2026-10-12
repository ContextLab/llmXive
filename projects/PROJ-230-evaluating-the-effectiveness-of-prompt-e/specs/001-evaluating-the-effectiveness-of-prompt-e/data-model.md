# Data Model: Evaluating the Effectiveness of Prompt Engineering for LLM-Based Code Translation

## Entities

### CodeSnippet
Represents a single translation task.
- `id`: Unique identifier (string)
- `python_source`: Original Python code (string)
- `source_dataset_id`: Identifier of the source dataset (string)
- `dataset_url`: URL of the dataset source (string)

### PromptCondition
Represents one of the four experimental setups.
- `condition_name`: One of "zero_shot_basic", "zero_shot_style", "few_shot_basic", "few_shot_style" (string)
- `instruction_detail`: "zero-shot" or "few-shot" (string)
- `style_specification`: "absent" or "present" (string)
- `prompt_template`: Full prompt text (string)

### TranslationResult
Represents the output of a single run.
- `snippet_id`: Reference to CodeSnippet (string)
- `condition_name`: Reference to PromptCondition (string)
- `generated_js`: Generated JavaScript code (string)
- `test_pass_status`: "pass", "fail", "skipped", "timeout" (string)
- `complexity_score`: Cyclomatic complexity (integer)
- `lines_of_code`: Number of lines (integer)
- `execution_time`: Time in seconds (float)
- `raw_response`: Raw API response (string)
- `seed`: Random seed used (integer)
- `timestamp`: Execution timestamp (datetime)
- `model_source`: "HF_API" or "Ollama_local" (string, optional; used if fallback to Ollama 7B was triggered)

### StatisticalSummary
Represents the aggregate analysis result.
- `metric`: "correctness", "complexity", "lines_of_code", or "power_limitation" (string)
- `comparison`: e.g., "zero_shot_style vs zero_shot_basic" (string)
- `p_value`: P-value from statistical test (float)
- `confidence_interval_lower`: Lower bound of 95% CI (float)
- `confidence_interval_upper`: Upper bound of 95% CI (float)
- `effect_size`: Cohen's h, eta-squared, or Cohen's f (float)
- `observed_power`: Post-hoc observed power for the comparison (float, optional)
- `correction_method`: "bonferroni" or "none" (string)

## Relationships

- `CodeSnippet` → `TranslationResult`: One-to-many (one snippet translated under multiple conditions)
- `PromptCondition` → `TranslationResult`: One-to-many (one condition applied to multiple snippets)
- `TranslationResult` → `StatisticalSummary`: Many-to-one (multiple results aggregated into one summary)

## Data Flow

1. **Ingestion**: `CodeSnippet` entities created from HF datasets.
2. **Prompting**: `PromptCondition` templates loaded; `TranslationResult` generated via API.
3. **I/O Extraction**: I/O pairs extracted from original Python code (fixed synthetic inputs).
4. **Validation**: `TranslationResult` enriched with test pass/fail (JS execution against I/O pairs) and quality metrics.
5. **Analysis**: `StatisticalSummary` computed from aggregated `TranslationResult` with confounder checks and power analysis.

## Storage Format

- **Raw Data**: Parquet files from HF datasets stored in `data/raw/`.
- **Processed Data**: CSV files in `data/processed/` (CodeSnippet).
- **Evaluation Data**: CSV files in `data/evaluation/` (io_pairs, validation_results, quality_metrics, statistical_summary).
- **Prompts**: Text files in `data/prompts/`.