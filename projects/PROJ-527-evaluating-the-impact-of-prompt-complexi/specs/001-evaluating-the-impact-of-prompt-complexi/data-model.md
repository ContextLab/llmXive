# Data Model: Evaluating the Impact of Prompt Complexity on LLM Code Generation Performance

## Entities & Relationships

### 1. HumanEvalProblem
Represents a single programming problem from the HumanEval dataset.
- **problem_id**: `string` (Primary Key)
- **description_text**: `string` (The problem statement)
- **test_code**: `string` (Unit tests)
- **canonical_solution**: `string` (Reference solution, optional for validation)
- **canonical_solution_length**: `integer` (Proxy for problem difficulty, used as control variable)

### 2. PromptVariant
Represents a specific prompt generated for a HumanEvalProblem.
- **variant_id**: `string` (Primary Key, e.g., `problem_id_complexity`)
- **problem_id**: `string` (Foreign Key -> HumanEvalProblem)
- **complexity_label**: `enum` (simple, moderate, complex, very_complex, degenerate)
- **prompt_text**: `string` (The full prompt sent to the LLM)
- **token_count**: `integer` (Count via tiktoken)
- **structural_element_count**: `integer` (Count of examples, constraints, etc.)
- **structural_complexity_score**: `float` (Weighted score: examples=1, constraints=2, etc.)
- **residualized_structure_score**: `float` (Residual of structural_count regressed on token_count, for collinearity control)

### 3. GeneratedCode
Represents the code output from an LLM query for a specific PromptVariant.
- **generation_id**: `string` (Primary Key)
- **variant_id**: `string` (Foreign Key -> PromptVariant)
- **code_text**: `string` (The generated code)
- **execution_status**: `enum` (success, syntax_error, runtime_error, timeout)
- **exception_message**: `string` (If failed)
- **pass_count**: `integer` (Number of passed unit tests)
- **fail_count**: `integer` (Number of failed unit tests)
- **lines_of_code**: `integer` (From static analysis)
- **cyclomatic_complexity**: `float` (From static analysis)
- **readability_score**: `float` (Aggregated score from ruff/pylint)

### 4. AnalysisResult
Represents the aggregated statistical findings.
- **analysis_id**: `string` (Primary Key)
- **test_type**: `string` (e.g., "Linear Mixed Model", "LMM")
- **fixed_effects_coefficients**: `json` (Coefficients for complexity, token count, residualized structure)
- **random_effects_variance**: `json` (Variance attributed to problem_id)
- **p_value_fixed**: `float`
- **effect_size**: `float` (Marginal R2 or Cohen's f2)
- **corrected_significance_threshold**: `float`
- **covariate_adjusted_p_value**: `float` (If applicable)
- **inflection_point**: `string` (Complexity label where performance peaks/declines)

## Data Flow

1.  **Ingestion**: `HumanEvalProblem` loaded from HuggingFace.
2.  **Generation**: `PromptVariant` created for each problem; `GeneratedCode` created after LLM query.
3.  **Execution**: `GeneratedCode` tested; metrics (pass/fail, complexity) stored.
4.  **Collinearity Resolution**: `residualized_structure_score` calculated from `token_count` and `structural_element_count`.
5.  **Aggregation**: `AnalysisResult` computed from `GeneratedCode` table using LMM.

## Storage Format

- **Raw Data**: Parquet/JSONL in `data/raw/`.
- **Processed Data**: CSV/Parquet in `data/processed/` (checksummed).
- **Artifacts**: Checksums recorded in `state/projects/...yaml`.