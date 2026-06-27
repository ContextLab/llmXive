# Feature Specification: Evaluating the Impact of Prompt Complexity on LLM Code Generation Performance

**Feature Branch**: `001-prompt-complexity-evaluation`  
**Created**: 2026-06-26  
**Status**: Draft  
**Input**: User description: "Evaluate how prompt complexity (token length and structural elements) affects code generation correctness, efficiency, and stylistic quality"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate and Evaluate Code from Multiple Prompt Complexity Levels (Priority: P1)

For each programming problem in the HumanEval dataset, the system MUST generate 5 prompt variants at controlled complexity levels (simple, moderate, complex, very complex, degenerate), query an LLM for each prompt, and capture the generated code with metadata including token counts and structural element counts.

**Why this priority**: This is the core research capability without which no evaluation can occur. It establishes the independent variable (prompt complexity) and dependent variable (generated code) relationship.

**Independent Test**: Can be fully tested by generating prompts for a single HumanEval problem, querying the LLM, and verifying that 5 distinct code samples are captured with correct metadata tags.

**Acceptance Scenarios**:

1. **Given** a HumanEval problem with problem description and unit tests, **When** the system generates 5 prompt variants, **Then** each variant MUST have a distinct complexity label and recorded token count
2. **Given** 5 prompt variants for the same problem, **When** the LLM is queried, **Then** the system MUST capture all 5 generated code samples with associated prompt metadata
3. **Given** a degenerate prompt variant with redundant instructions, **When** the system generates it, **Then** the token count MUST exceed the simple variant by at least 200 tokens

---

### User Story 2 - Execute Unit Tests and Collect Pass/Fail Rates (Priority: P2)

For each generated code sample, the system MUST execute the HumanEval unit tests and record pass/fail outcomes, then aggregate results by complexity level to compute pass rates.

**Why this priority**: This provides the primary correctness metric. Without automated testing, code quality cannot be measured objectively.

**Independent Test**: Can be fully tested by running 5 generated code samples against HumanEval unit tests and verifying pass/fail counts are recorded per complexity level.

**Acceptance Scenarios**:

1. **Given** a generated code sample, **When** unit tests are executed, **Then** the system MUST record pass count, fail count, and total test count
2. **Given** all code samples for one complexity level, **When** results are aggregated, **Then** the pass rate MUST be calculated as (pass count / total test count) × 100
3. **Given** a code sample that raises an exception during execution, **When** the test runner catches it, **Then** the sample MUST be marked as failed with the exception type logged

---

### User Story 3 - Perform Statistical Analysis and Visualize Complexity-Performance Curves (Priority: P3)

The system MUST perform ANOVA or Kruskal-Wallis tests to compare performance metrics across complexity levels, apply multiple-comparison correction, and generate plots showing complexity vs. performance tradeoff curves with inflection points identified.

**Why this priority**: This delivers the research output—the evidence on optimal prompt complexity thresholds. It answers the research question.

**Independent Test**: Can be fully tested by running statistical analysis on aggregated pass rates and readability scores, verifying that effect sizes and p-values are computed with family-wise error correction applied.

**Acceptance Scenarios**:

1. **Given** pass rates across 5 complexity levels, **When** ANOVA or Kruskal-Wallis test is performed, **Then** the system MUST report test statistic, p-value, and effect size
2. **Given** multiple hypothesis tests, **When** family-wise error correction is applied, **Then** the system MUST use Bonferroni or Holm-Bonferroni correction with adjusted significance threshold ≤ 0.05
3. **Given** complexity-performance data, **When** curves are plotted, **Then** the system MUST identify and mark the complexity level with peak performance and the inflection point where diminishing returns begin

---

### Edge Cases

- What happens when the LLM fails to generate valid Python code (syntax error preventing execution)? The system MUST mark the sample as failed and log the error message.
- How does the system handle HumanEval problems where unit tests timeout (>30 seconds)? The system MUST count the problem as failed and log the timeout.
- What happens when the LLM generates code that passes tests but contains security vulnerabilities? The system MUST flag these samples for manual review but still record them as passing.
- How does the system handle missing or corrupted HumanEval dataset files? The system MUST raise an error and halt execution rather than proceeding with incomplete data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate 5 prompt variants per HumanEval problem with controlled complexity levels (simple ≤ 50 tokens, moderate 51-150 tokens, complex 151-300 tokens, very complex 301-500 tokens, degenerate > 500 tokens) (See US-1)
- **FR-002**: System MUST query the LLM and capture generated code with metadata including prompt complexity label, token count, and structural element count (See US-1)
- **FR-003**: System MUST execute generated code against HumanEval unit tests with a 30-second timeout per test and record pass/fail outcomes (See US-2)
- **FR-004**: System MUST run static analysis using ruff or pylint on generated code to extract readability scores and cyclomatic complexity metrics (See US-3)
- **FR-005**: System MUST perform ANOVA or Kruskal-Wallis test to compare performance metrics across 5 complexity levels with family-wise error correction applied (See US-3)
- **FR-006**: System MUST apply Bonferroni correction when > 1 hypothesis test is performed, adjusting significance threshold to 0.05 / number of tests (See US-3)
- **FR-007**: System MUST generate complexity vs. performance curves identifying the complexity level with peak pass rate and the inflection point where diminishing returns begin (See US-3)
- **FR-008**: System MUST use validated readability metrics (e.g., cyclomatic complexity, lines of code, indentation consistency) with citable validation sources (See US-3)

*Example of marking unclear requirements:*

- **FR-009**: System MUST [NEEDS CLARIFICATION: does HumanEval dataset contain the specific structural element counts needed to classify prompts as "complex" vs "very complex" based on examples and constraints?]

### Key Entities

- **HumanEvalProblem**: A programming problem with description, starter code, and unit tests; key attributes include problem_id, description_text, test_code
- **PromptVariant**: A generated prompt with complexity level; key attributes include problem_id, complexity_label, token_count, structural_element_count, prompt_text
- **GeneratedCode**: Code output from LLM query; key attributes include problem_id, complexity_label, code_text, execution_status, pass_count, fail_count
- **AnalysisResult**: Statistical analysis output; key attributes include test_type, test_statistic, p_value, effect_size, corrected_significance_threshold

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Pass rate is measured across 5 complexity levels using HumanEval unit test outcomes as reference (See US-2)
- **SC-002**: Readability scores are measured using validated metrics (cyclomatic complexity, lines of code) with citable validation sources as reference (See US-3)
- **SC-003**: Statistical significance is measured against family-wise error corrected threshold (α ≤ 0.05 / number of tests) as reference (See US-3)
- **SC-004**: Effect sizes are measured using Cohen's d or eta-squared with standard interpretation thresholds as reference (See US-3)
- **SC-005**: Complexity-performance curves are measured against the observed data points with inflection point identified where performance plateau or decline begins (See US-3)

## Assumptions

- The HumanEval dataset contains a collection of programming problems with complete unit tests that can be executed in isolation without external dependencies.
- An open-source LLM (e.g., CodeLlama-7B) can be queried via HuggingFace Inference API or loaded locally as a GGUF model that runs on CPU-only hardware within the 6-hour job limit.
- Prompt complexity classification (simple ≤ 50 tokens, moderate 51-150 tokens, complex 151-300 tokens, very complex 301-500 tokens, degenerate > 500 tokens) is based on community-standard token counting methods (e.g., tiktoken or HuggingFace tokenizer).
- The research design is observational with no random assignment to complexity levels; therefore all findings MUST be framed as ASSOCIATIONAL, not causal, per reviewer alan-turing-simulated's guidance on inference framing.
- Token length alone may not fully capture prompt complexity; the system MUST also measure structural elements (examples, constraints, multi-paragraph instructions) as a second dimension of complexity, addressing the methodological concern raised by reviewer alan-turing-simulated.
- The HumanEval dataset may not contain all variables needed to classify structural elements (e.g., number of examples or constraint types); if the dataset lacks these, the system MUST record a [NEEDS CLARIFICATION: does HumanEval dataset contain structural element metadata?] marker for the Clarifier Agent to resolve.
- Statistical power analysis is deferred to the research phase; the system MUST include an FR/SC requiring sample-size consideration with acknowledgment of power limitations given the fixed 164 problems.
- Readability metrics MUST use validated instruments (e.g., cyclomatic complexity from McCabe, lines of code, indentation consistency) with citable validation sources; if the idea does not specify which metrics, the system MUST use ruff/pylint defaults and record this under Assumptions.
- Predictor collinearity between token length and structural element counts MUST be diagnosed (e.g., variance inflation factor); the system MUST NOT claim independent predictive effects for both variables if they are definitionally related.
- Any threshold introduced (e.g., complexity level boundaries, significance thresholds) MUST carry both (a) a one-line justification naming its community-standard basis and (b) an FR/SC requiring sensitivity analysis sweeping the cutoff over {0.01, 0.05, 0.1} and reporting how false-positive / false-negative rates vary.
- The entire analysis MUST run on GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM, ~14 GB disk, NO GPU, ≤6 h per job); no GPU/CUDA, no 8-bit or 4-bit quantization, no large-model training from scratch.
- Data must fit ~7 GB RAM / ~14 GB disk; if the full HumanEval dataset plus generated code exceeds this, the system MUST sample or subset and record the scoping decision under Assumptions.
- The LLM query method MUST be CPU-tractable; if the idea implies a heavy method, the system MUST specify a CPU-tractable approximation (e.g., smaller model, sampled subset, cached responses) and record this under Assumptions.
