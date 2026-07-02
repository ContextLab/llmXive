# Feature Specification: Evaluating the Impact of Prompt Complexity on LLM Code Generation Performance

**Feature Branch**: `001-prompt-complexity-evaluation`  
**Created**: 2026-06-26  
**Status**: Draft  
**Input**: User description: "Evaluate how prompt complexity (token length and structural elements) affects code generation correctness, efficiency, and stylistic quality"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate and Evaluate Code from Multiple Prompt Complexity Levels (Priority: P1)

For each programming problem in the HumanEval dataset, the system MUST generate multiple prompt variants at controlled complexity levels. (simple, moderate, complex, very complex, degenerate), query an LLM for each prompt, and capture the generated code with metadata including token counts and structural element counts.

**Why this priority**: This is the core research capability without which no evaluation can occur. It establishes the independent variable (prompt complexity) and dependent variable (generated code) relationship.

**Independent Test**: Can be fully tested by generating prompts for a single HumanEval problem, querying the LLM, and verifying that 5 distinct code samples are captured with correct metadata tags.

**Acceptance Scenarios**:

1. **Given** a HumanEval problem with problem description and unit tests, **When** the system generates 5 prompt variants, **Then** each variant MUST have a distinct complexity label and recorded token count
2. **Given** 5 prompt variants for the same problem, **When** the LLM is queried, **Then** the system MUST capture all 5 generated code samples with associated prompt metadata
3. **Given** a degenerate prompt variant with redundant instructions, **When** the system generates it, **Then** the token count MUST be the maximum among the 5 variants, ideally exceeding the 'very complex' variant by ≥ 100 tokens; if the delta is < 100 tokens, the system MUST flag the sample for manual review rather than failing the test.

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

The system MUST perform ANOVA or Kruskal-Wallis tests to compare performance metrics across complexity levels, apply multiple-comparison correction, and generate plots showing complexity vs. performance tradeoff curves with inflection points identified. The analysis MUST control for code length as a covariate when evaluating readability metrics.

**Why this priority**: This delivers the research output—the evidence on optimal prompt complexity thresholds. It answers the research question.

**Independent Test**: Can be fully tested by running statistical analysis on aggregated pass rates and readability scores, verifying that effect sizes and p-values are computed with family-wise error correction applied and code length is controlled for.

**Acceptance Scenarios**:

1. **Given** pass rates across 5 complexity levels, **When** ANOVA or Kruskal-Wallis test is performed, **Then** the system MUST report test statistic, p-value, and effect size
2. **Given** multiple hypothesis tests, **When** family-wise error correction is applied, **Then** the system MUST use Bonferroni or Holm-Bonferroni correction with adjusted significance threshold ≤ 0.05 for all post-hoc pairwise comparisons
3. **Given** complexity-performance data, **When** curves are plotted, **Then** the system MUST identify and mark the complexity level with peak performance and the inflection point where diminishing returns begin
4. **Given** 'degenerate' prompts, **When** structural analysis is run, **Then** the system MUST verify that the structural element count is higher than in 'very complex' prompts, ensuring the 'degenerate' label reflects structural redundancy, not just length.

---

### Edge Cases

- What happens when the LLM fails to generate valid Python code (syntax error preventing execution)? The system MUST mark the sample as failed and log the error message.
- How does the system handle HumanEval problems where unit tests timeout (>30 seconds)? The system MUST count the problem as failed and log the timeout.
- What happens when the LLM generates code that passes tests but contains security vulnerabilities? The system MUST flag these samples for manual review but still record them as passing.
- How does the system handle missing or corrupted HumanEval dataset files? The system MUST raise an error and halt execution rather than proceeding with incomplete data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate multiple prompt variants per HumanEval problem with controlled complexity levels defined by structural composition: simple (problem statement only), moderate (+1 example), complex (+constraints), very complex (+multi-step instructions), degenerate (+redundant constraints/examples). Token counts (using tiktoken cl100k_base, counting only prompt text) MUST serve as secondary indicators: simple ≤ 50 tokens, moderate 51-150 tokens, complex 151-300 tokens, very complex 301-500 tokens, degenerate > 500 tokens. (See US-1)
- **FR-002**: System MUST query the LLM and capture generated code with metadata including prompt complexity label, token count, and structural element count. (See US-1)
- **FR-003**: System MUST execute generated code against HumanEval unit tests with a bounded timeout per test and record pass/fail outcomes. (See US-2)
- **FR-004**: System MUST run static analysis using ruff or pylint on generated code to extract readability scores and cyclomatic complexity metrics. (See US-3)
- **FR-005**: System MUST perform ANOVA or Kruskal-Wallis test to compare performance metrics across 5 complexity levels with family-wise error correction applied. (See US-3)
- **FR-006**: System MUST apply Bonferroni or Holm-Bonferroni correction to all post-hoc pairwise comparisons when > 1 hypothesis test is performed, adjusting significance threshold to 0.05 / number of tests. (See US-3)
- **FR-007**: System MUST generate complexity vs. performance curves identifying the complexity level with peak pass rate and the inflection point where diminishing returns begin. (See US-3)
- **FR-008**: System MUST use validated readability metrics (cyclomatic complexity via ruff/pylint, lines of code, indentation consistency) as defined in standard software engineering literature. (See US-3)
- **FR-009**: System MUST implement a dynamic parser to count structural elements (number of code examples, constraint blocks, instruction paragraphs) in generated prompts and store them as metadata. (See US-1)
- **FR-010**: System MUST perform a sensitivity analysis by re-binning data using shifted thresholds (±10 tokens) and report the variance in pass rates across bins to validate the robustness of complexity boundaries. (See US-3)
- **FR-011**: System MUST calculate a structural complexity score based on the count and type of structural elements (e.g., examples=1, constraints=2, instructions=1.5) and report it alongside token count. (See US-1)
- **FR-012**: System MUST include code length (lines of code) as a covariate in the statistical model when testing the effect of prompt complexity on readability metrics to control for confounding. (See US-3)
- **FR-013**: System MUST report the correlation coefficient between token count and structural element count to diagnose potential collinearity. (See US-3)

### Key Entities

- **HumanEvalProblem**: A programming problem with description, starter code, and unit tests; key attributes include problem_id, description_text, test_code
- **PromptVariant**: A generated prompt with complexity level; key attributes include problem_id, complexity_label, token_count, structural_element_count, prompt_text, structural_complexity_score
- **GeneratedCode**: Code output from LLM query; key attributes include problem_id, complexity_label, code_text, execution_status, pass_count, fail_count, lines_of_code
- **AnalysisResult**: Statistical analysis output; key attributes include test_type, test_statistic, p_value, effect_size, corrected_significance_threshold, covariate_adjusted_p_value

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Pass rate is measured across 5 complexity levels using HumanEval unit test outcomes as reference (See US-2)
- **SC-002**: Readability scores are measured using validated metrics (cyclomatic complexity, lines of code) with citable validation sources as reference (See US-3)
- **SC-003**: Statistical significance is measured against family-wise error corrected threshold (α ≤ 0.05 / number of tests) as reference (See US-3)
- **SC-004**: Effect sizes (Cohen's d or eta-squared) are measured against standard interpretation thresholds (Cohen's d: small/medium/large; eta-squared: small/medium/large) as reference (See US-3)
- **SC-005**: Complexity-performance curves are measured against the observed data points with inflection point identified where performance plateau or decline begins (See US-3)
- **SC-006**: Sensitivity analysis results are measured against the variance in pass rates across shifted thresholds (±10 tokens) as reference (See US-3)

## Assumptions

- The HumanEval dataset contains a collection of programming problems with complete unit tests that can be executed in isolation without external dependencies.
- An open-source LLM (e.g., CodeLlama-7B) can be queried via HuggingFace Inference API or loaded locally as a GGUF model that runs on CPU-only hardware within the 6-hour job limit.
- Prompt complexity classification is based on structural composition (examples, constraints, instructions) with token counts as secondary indicators using community-standard token counting methods (tiktoken cl100k_base).
- The research design is observational with no random assignment to complexity levels; therefore all findings MUST be framed as ASSOCIATIONAL, not causal, per reviewer alan-turing-simulated's guidance on inference framing.
- The HumanEval dataset lacks pre-calculated structural element counts; the system MUST derive these dynamically by parsing prompt text for structural markers (e.g., 'Example:', 'Constraint:').
- Statistical power analysis is deferred to the research phase; the system MUST include an FR/SC requiring sample-size consideration with acknowledgment of power limitations given the fixed 164 problems.
- Readability metrics MUST use validated instruments (e.g., cyclomatic complexity from McCabe, lines of code, indentation consistency) with citable validation sources; if the idea does not specify which metrics, the system MUST use ruff/pylint defaults and record this under Assumptions.
- Predictor collinearity between token length and structural element counts MUST be diagnosed (e.g., variance inflation factor); the system MUST NOT claim independent predictive effects for both variables if they are definitionally related.
- Any threshold introduced (e.g., complexity level boundaries, significance thresholds) MUST carry both (a) a one-line justification naming its community-standard basis and (b) an FR/SC requiring sensitivity analysis sweeping the cutoff over {0.01, 0.05, 0.1} and reporting how false-positive / false-negative rates vary.
- The entire analysis MUST run on GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM, ~14 GB disk, NO GPU, ≤6 h per job); no GPU/CUDA, no 8-bit or 4-bit quantization, no large-model training from scratch.
- Data must fit within available system memory and disk storage.; if the full HumanEval dataset plus generated code exceeds this, the system MUST sample or subset and record the scoping decision under Assumptions.
- The LLM query method MUST be CPU-tractable; if the idea implies a heavy method, the system MUST specify a CPU-tractable approximation (e.g., smaller model, sampled subset, cached responses) and record this under Assumptions.
- A target delta of ≥ 100 tokens between 'very complex' and 'degenerate' variants is a generation guideline; if the generator cannot achieve this, the system MUST flag the sample rather than failing the test.