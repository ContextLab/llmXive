# Specification: Evaluating the Impact of Prompt Complexity on LLM Code Generation Performance

## Project Overview
This project evaluates how varying levels of prompt complexity affect the performance of Large Language Models (LLMs) in generating code that passes unit tests. The study uses the HumanEval benchmark and controls for structural composition and token count.

## User Stories

### US-1: Generate and Evaluate Code from Multiple Prompt Complexity Levels
**As a** researcher,
**I want** to generate multiple prompt variants (simple, moderate, complex, very complex, degenerate) for each HumanEval problem,
**So that** I can evaluate how prompt complexity influences code generation success rates.

**Acceptance Criteria:**
1. **Prompt Generation**: The system MUST generate 5 distinct variants per problem based on structural composition.
2. **Token Count Validation**: Token counts MUST be validated against defined thresholds using `tiktoken cl100k_base`.
3. **Manual Review Flagging**: The system MUST identify and flag samples where the 'degenerate' prompt token delta (vs 'very complex') is < 100 tokens. These samples MUST be written to `data/results/manual_review_queue.csv` with columns `problem_id`, `variant_label`, `token_delta`, `reason` for manual review. This ensures that structural complexity is not artificially inflated without corresponding token growth.
4. **Data Capture**: All generated code, metadata, and execution results MUST be stored in `data/processed/prompt_variants.parquet`.

### US-2: Execute Unit Tests and Collect Pass/Fail Rates
**As a** researcher,
**I want** to execute the generated code against HumanEval unit tests,
**So that** I can collect pass/fail rates for each complexity level.

**Acceptance Criteria:**
1. **Execution**: The system MUST execute generated code with a configurable timeout.
2. **Error Handling**: Syntax errors and runtime exceptions MUST be caught and logged.
3. **Aggregation**: Pass rates MUST be aggregated by complexity level and written to `data/results/execution_outcomes.csv`.

### US-3: Perform Statistical Analysis and Visualize Complexity-Performance Curves
**As a** researcher,
**I want** to perform statistical analysis (LMM) and visualize the results,
**So that** I can determine the relationship between prompt complexity and code generation performance.

**Acceptance Criteria:**
1. **LMM Analysis**: The system MUST fit Linear Mixed Models with random intercepts for problem difficulty.
2. **Multiple Comparison Correction**: Bonferroni or Holm-Bonferroni correction MUST be applied.
3. **Covariate Adjustment**: Prompt token count MUST be used as a covariate.
4. **Structural Element Validation**: If the structural element count for 'degenerate' prompts is not strictly higher than 'very complex' prompts, the system MUST flag these instances for manual review. This validates the assumption that structural complexity correlates with prompt length and content density.
5. **Visualization**: Complexity vs. performance curves MUST be generated with inflection points identified.
6. **Reporting**: Final statistical results MUST be written to `data/results/analysis_summary.csv`.

## Functional Requirements

FR-001: System MUST generate multiple prompt variants per HumanEval problem with controlled complexity levels defined by structural composition: simple (problem statement only), moderate (+1 example), complex (+constraints), very complex (+multi-step instructions), degenerate (+redundant constraints/examples). Token counts (using tiktoken cl100k_base, counting only prompt text) MUST serve as secondary indicators: simple ≤ 50 tokens, moderate 51-150 tokens, complex 151-300 tokens, very complex 301-500 tokens, degenerate > 500 tokens. (See US-1)

FR-002: System MUST download the HumanEval dataset from Hugging Face Hub.

FR-003: System MUST use `tiktoken` for token counting.

FR-004: System MUST execute generated code in a sandboxed environment.

FR-005: System MUST perform statistical analysis using Linear Mixed Models (LMM) to account for nested data structures (multiple variants per problem) with random intercepts for problem difficulty. ANOVA or Kruskal-Wallis tests are explicitly NOT permitted as the primary analysis method due to violation of independence assumptions.

FR-006: System MUST apply multiple comparison correction (Bonferroni or Holm-Bonferroni).

FR-007: System MUST visualize complexity vs. performance curves.

FR-008: System MUST calculate cyclomatic complexity and lines of code using standard definitions (McCabe 1976, Ruff Documentation v0.1.0).

FR-009: System MUST flag security vulnerabilities in generated code.

FR-010: System MUST perform sensitivity analysis by re-binning data with shifted thresholds.

FR-011: System MUST calculate effect sizes (Cohen's d, eta-squared).

FR-012: System MUST use prompt token count as the primary covariate for readability metrics and statistical control, replacing the original 'code length (lines of code)' requirement. This aligns with the structural complexity definition in FR-001.

FR-013: System MUST check for collinearity between token count and structural element count.

## Non-Functional Requirements

NFR-001: The system MUST run within 6 hours on a CPU-only environment.

NFR-002: All data artifacts MUST be versioned and checksummed.

NFR-003: The system MUST be modular and extensible.

## Assumptions

1. **HumanEval Availability**: The HumanEval dataset is available and accessible via the Hugging Face Hub (`openai/openai_humaneval`).
2. **CPU Constraints**: The LLM inference and code execution will run on CPU-only environments; therefore, timeouts and batch sizes are tuned for CPU performance.
3. **Tokenization Consistency**:The `tiktoken cl100k_base` tokenizer accurately reflects the tokenization behavior of the target LLM for the purpose of complexity estimation.
4. **Statistical Power**: The sample size of HumanEval (164 (Wikipedia: Language model benchmark, https://en.wikipedia.org/wiki/Language_model_benchmark) problems) is sufficient to detect medium-to-large effect sizes in pass rates across complexity levels, though power may be limited for small effects.
5. **Code Execution Safety**: Generated code is executed in a sandboxed environment to prevent security vulnerabilities.

## Glossary
- **HumanEval**: A benchmark for evaluating the code generation capabilities of LLMs.
- **LMM**: Linear Mixed Model.
- **Token**: A unit of text processed by the LLM.
- **Structural Element**: Examples, constraints, instructions, etc., that compose a prompt.