# Feature Specification: Evaluating the Effectiveness of Prompt Engineering for LLM-Based Code Translation

**Feature Branch**: `001-prompt-engineering-code-translation`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Evaluating the Effectiveness of Prompt Engineering for LLM-Based Code Translation"

## User Scenarios & Testing

### User Story 1 - Dataset Acquisition and Preprocessing (Priority: P1)

The system MUST download, filter, and prepare the Python-to-JavaScript translation pairs from the specified HuggingFace datasets (CodeTrans and BigCode) to create a reproducible, CPU-tractable evaluation corpus of at least 200 snippets.

**Why this priority**: Without a standardized, accessible dataset, no experiments can be run. This is the foundational block for all subsequent prompt testing and analysis.

**Independent Test**: Can be fully tested by verifying the script logs a memory usage peak < 7GB during execution or confirms that data is processed in chunks such that no single object exceeds 7GB, and confirming the existence of a local CSV file containing ≥ 200 valid Python/JavaScript pairs.

**Acceptance Scenarios**:

1. **Given** the HuggingFace dataset URLs are accessible, **When** the ingestion script runs, **Then** a local dataset file is created containing ≥ 200 valid Python/JavaScript pairs.
2. **Given** a raw dataset entry with missing or corrupted code, **When** the preprocessing step runs, **Then** that entry is excluded, and a log of excluded entries is generated without crashing the pipeline.
3. **Given** the dataset size exceeds available RAM, **When** the script executes, **Then** it samples or chunks the data to ensure the total memory footprint remains ≤ 7 GB.

---

### User Story 2 - Prompt Condition Execution (Priority: P2)

The system MUST execute the four distinct prompt engineering conditions (Zero-shot Basic, Zero-shot+Style, Few-shot, Few-shot+Style) against the prepared dataset using the CodeLlama model via HuggingFace Inference API, storing the generated outputs deterministically.

**Why this priority**: This is the core experimental intervention. It generates the raw data (translated code) required to measure correctness and quality.

**Independent Test**: Can be fully tested by running the execution script with a fixed seed and verifying that the output directory contains a distinct set of subdirectories corresponding to each experimental condition, each populated with generated JavaScript files matching the input snippets.

**Acceptance Scenarios**:

1. **Given** a Python code snippet and a selected prompt condition, **When** the LLM inference is triggered, **Then** the system MUST enforce a 120-second timeout per request; if the response is not received within this window, the system logs a timeout failure and proceeds to the next item without crashing.
2. **Given** the API rate limit is reached, **When** the request queue is full, **Then** the system waits and retries the request up to 3 times with exponential backoff before marking the specific translation as failed.
3. **Given** the LLM returns malformed JSON or non-code text, **When** the output is parsed, **Then** the system logs the error and stores the raw response for manual review rather than crashing.

---

### User Story 3 - Functional Correctness and Quality Analysis (Priority: P3)

The system MUST evaluate the generated JavaScript against a *translated* version of the original Python unit tests (converted to JavaScript) and compute code quality metrics (cyclomatic complexity, lines of code) using JS-native tools to generate the final statistical report.

**Why this priority**: This transforms raw outputs into scientific results, answering the research question regarding correctness and quality differences between prompt strategies.

**Independent Test**: Can be fully tested by running the analysis script on a small subset of pre-generated outputs and verifying that the final CSV contains columns for `pass_rate`, `complexity`, `prompt_condition`, and `p_value` with valid statistical test results.

**Acceptance Scenarios**:

1. **Given** a translated JavaScript file and the corresponding translated test suite, **When** the Node.js test runner executes, **Then** the system records a binary pass/fail status for each snippet.
2. **Given** a set of translated snippets, **When** the quality metrics are computed, **Then** the system outputs a CSV row with the cyclomatic complexity and lines of code for each translation using `eslint` complexity rules.
3. **Given** the collected metrics across all conditions, **When** the statistical analysis runs, **Then** the system generates a summary report (CSV/JSON) containing columns for `chi_square_p_value`, `anova_f_statistic`, and `confidence_interval` with 95% confidence bounds.

---

### Edge Cases

- What happens when the HuggingFace API is unavailable or the dataset repository is removed? (System must fail gracefully with a clear error message and not attempt infinite retries).
- How does the system handle translated code that causes an infinite loop during testing? (The test runner must enforce a 10-second timeout per test case).
- How does the system handle code snippets that are too complex for the LLM to translate at all (e.g., returning "I cannot do that")? (These are logged as "failed translation" and counted as functional failures).
- What happens if the JavaScript test runner fails to execute a specific test case due to environment incompatibility? (The system must skip that specific test case, log it as "skipped," and not treat it as a pass or fail).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and cache the CodeTrans and BigCode datasets, filtering for a final corpus of ≥ 200 Python-to-JavaScript pairs, ensuring the total dataset size does not exceed 7 GB RAM. (See US-1)
- **FR-002**: System MUST generate and apply four distinct prompt templates (Zero-shot Basic, Zero-shot+Style, Few-shot, Few-shot+Style) to every code snippet in the dataset using the CodeLlama-7B model via HuggingFace Inference API. (See US-2)
- **FR-003**: System MUST translate the original Python unit tests to JavaScript, execute them against the generated JavaScript code in a Node.js runtime, and record a binary pass/fail result for each execution. (See US-3)
- **FR-004**: System MUST compute cyclomatic complexity and lines of code for every generated JavaScript translation using the `eslint` complexity plugin. (See US-3)
- **FR-005**: System MUST perform statistical analysis (Chi-square for correctness, ANOVA for quality) on the aggregated results, including multiple-comparison corrections (e.g., Bonferroni) where >1 hypothesis is tested. (See US-3)
- **FR-006**: System MUST log all prompts, model versions, seeds, and raw outputs to a version-controlled CSV for reproducibility. (See US-2)

### Key Entities

- **CodeSnippet**: Represents a single translation task containing `python_source`, `expected_js_reference`, and `source_dataset_id`.
- **PromptCondition**: Represents one of the four experimental setups. The mapping of named conditions to attributes is defined as follows:
  | Condition Name | instruction_detail | style_specification |
  | :--- | :--- | :--- |
  | Zero-shot Basic | `zero-shot` | `absent` |
  | Zero-shot+Style | `zero-shot` | `present` |
  | Few-shot | `few-shot` | `absent` |
  | Few-shot+Style | `few-shot` | `present` |
- **TranslationResult**: Represents the output of a single run, containing `generated_js`, `test_pass_status`, `complexity_score`, and `execution_time`.
- **StatisticalSummary**: Represents the aggregate analysis result, containing `p_value`, `confidence_interval`, and `effect_size`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Statistical significance (p-value) of correctness rate differences between prompt conditions is measured and recorded against the baseline Zero-shot Basic condition. (See FR-005)
- **SC-002**: Code quality metrics (cyclomatic complexity, lines of code) are measured and recorded for each prompt condition to determine if specific strategies reduce complexity or bloat. (See FR-004, FR-005)
- **SC-003**: The total execution time for the full snippet experiment is measured against the GitHub Actions free-tier limit to ensure feasibility. (See FR-002)
- **SC-004**: The memory footprint of the dataset and analysis pipeline is measured against the available RAM limit of the CI runner. (See FR-001)

## Assumptions

- **Assumption about data availability**: The HuggingFace datasets `codeparrot/code-trans-py-js` and `bigcode/evaluation` will remain publicly accessible and contain sufficient valid Python-to-JavaScript pairs to reach the N ≥ 200 target.
- **Assumption about API reliability**: The HuggingFace Inference API (CodeLlamaB endpoint) will remain available and not impose rate limits that prevent completing the required total number of requests (a sufficient volume of snippets across all experimental conditions) within the 6-hour window.
- **Assumption about test translation**: A valid mechanism exists to translate the Python unit tests to JavaScript (e.g., via the same LLM or a dedicated transpiler) such that the translated tests preserve the semantic intent of the original assertions.
- **Assumption about model behavior**: The CodeLlama-7B model will not hallucinate infinite loops or syntax errors that crash the test runner; any such behavior will be treated as a functional failure.
- **Assumption about statistical power**: The sample size of N=200 is sufficient to detect a medium effect size (Cohen's h ≈ 0.5) in correctness rates with [deferred] power; if the effect is smaller, the study may be underpowered, which is acknowledged as a limitation.
- **Assumption about threshold justification**: The default significance threshold of α = 0.05 is used for all statistical tests, consistent with community standards in software engineering research; a sensitivity analysis sweeping α across a range of low values will be performed to ensure robustness.