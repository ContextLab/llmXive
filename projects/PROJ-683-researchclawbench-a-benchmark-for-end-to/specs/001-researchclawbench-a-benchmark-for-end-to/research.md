# Research: Reproduce & Validate ResearchClawBench

## Executive Summary

This research document validates the feasibility of reproducing the ResearchClawBench benchmark on a free-tier CPU CI runner. The primary challenge is the potential dependency on heavy LLM inference or GPU-accelerated models. The strategy is to utilize a `mock` agent configuration to bypass external API calls and heavy computation, focusing validation on the **pipeline mechanics** (data loading, rubric parsing, scoring logic, and aggregation).

Crucially, this research addresses the **Construct Validity** of the scoring engine. Instead of relying on a generic "mock" agent that might trivially pass all checks, the plan employs a **Synthetic Ground Truth** strategy. We will generate specific "Golden" (perfect) and "Negative" (deliberately flawed) synthetic artifacts to verify that the scoring engine correctly *interprets* the rubric criteria (e.g., detecting a missing figure) rather than just summing weights.

## Dataset Strategy

The project relies on **vendored data** contained within the `external/ResearchClawBench` submodule. No external dataset downloads are required for the validation phase.

| Dataset Name | Source / Location | Variables / Content | Fit for Purpose |
| :--- | :--- | :--- | :--- |
| **ResearchClawBench Tasks** | `external/ResearchClawBench/tasks/` | `task_info.json`, `data/` (CSV, PDF, Images), `target_study/checklist.json` | **Perfect Fit**. The spec explicitly requires running the vendored code. The data is already present in the repository. |
| **Synthetic Ground Truth** | `src/validation/synthetic_generator.py` | Programmatically generated artifacts (text, PDFs, CSVs) designed to match or violate specific rubric criteria. | **Perfect Fit**. Used to verify the scoring engine's ability to parse and score artifacts without needing real agent generation. Includes "Negative Cases" to test deduction logic. |

**Constraint Check**: The `spec.md` mentions "Astronomy_000" or "Chemistry_000" as representative tasks. The plan assumes these exist in the vendored `tasks/` directory. If a specific task ID is missing, the plan mandates a fallback to any available task in `tasks/` to ensure the pipeline is tested.

## Technical Feasibility

### Compute Environment
- **Target**: GitHub Actions Free Tier (2 CPU, 7 GB RAM, 14 GB Disk).
- **GPU Requirement**: **None**. The validation uses a `mock` agent. If the vendored code attempts to load a GPU model, the `mock` configuration will override this or the code will be patched to skip model loading.
- **Memory**: The `mock` agent and standard Python data processing (pandas/json) will easily fit within 7 GB RAM.
- **Disk**: The vendored code and task data are assumed to fit within the 14 GB limit (typical for such benchmarks). If the full dataset exceeds this, the plan restricts execution to a **single task** (`Astronomy_000`).

### Methodological Rigor (Validation Logic)

Since this is a software validation benchmark, "statistical rigor" applies to the correctness of the scoring and aggregation algorithms, specifically their **Construct Validity**.

1.  **Rubric Weight Validation**:
    -   **Method**: The `rubric_checker.py` script will sum all weights in `checklist.json`.
    -   **Constraint**: Sum must equal `100.0` (or `1.0` depending on format) within a tolerance of `±0.01`.
    -   **Rationale**: Ensures the scoring engine does not produce biased results due to malformed rubrics (FR-002, SC-002).

2.  **Construct Validity of Scoring (Synthetic Ground Truth)**:
    -   **Method**: The `synthetic_generator.py` script will create two types of test artifacts for a given rubric:
        *   **Golden Case**: An output containing *all* required elements (e.g., a figure with the correct dimensions, a CSV with the correct outlier).
        *   **Negative Case**: An output explicitly *missing* a required element (e.g., no figure, or a CSV without the outlier).
    -   **Validation**: The `scorer.py` engine is run against these artifacts.
 * *Golden Case*: Must yield a score equal to the sum of weights ([deferred]).
 * *Negative Case*: Must yield a score equal to `[deferred] - weight_of_missing_criterion`.
    -   **Rationale**: This proves the scoring engine *reads* the content (e.g., checks for a file's existence, parses a PDF) rather than just returning a hardcoded value or summing weights blindly. It breaks the circular validation by providing an independent ground truth (the intentional omission).

3.  **Aggregation Accuracy**:
    -   **Method**: `aggregator.py` will compute mean and standard deviation.
    -   **Validation**: Unit tests will compare the script's output against manually calculated values for a known set of inputs.
    -   **Rationale**: Ensures the leaderboard generation logic is mathematically sound (FR-005, SC-003). Note: This validates the *arithmetic* of aggregation. Real-world variance (statistical distribution) is outside the scope of this reproduction pipeline, as it requires running multiple distinct agents which is computationally expensive and not part of the "mechanical reproduction" goal.

4.  **Error Handling**:
    -   **Method**: Verify that `FileNotFoundError` is raised when `tasks/<ID>/data/` is missing files.
    -   **Rationale**: Confirms robustness against incomplete data (FR-003, SC-004).

## Reviewer Feedback Integration

### Stephen Wolfram Simulated
> *Recommendation: Extend benchmark with "Rule-Space Discovery" task (Cellular Automata).*

**Decision**: **Deferred / Out of Scope**.
**Rationale**: The current feature scope is strictly **reproduction and validation** of the *existing* ResearchClawBench implementation (spec: "Reproduce & validate: ResearchClawBench... The code is vendored"). Adding a new task type ("Rule-Space Discovery") constitutes a **feature expansion** (creating new content), not a validation of the existing benchmark.
**Action**: This suggestion is noted as a potential future feature (`002-rule-space-discovery`) but will not be implemented in this phase. The plan focuses on verifying the *mechanism* of the benchmark, which would eventually support such a task if added.

### Alan Turing Simulated
> *Feedback: Specification measures *efficiency* rather than *plasticity*.*
> *Feedback: Research is treated as monolithic.*

**Decision**: **Acknowledged, but Scope Limited**.
**Rationale**: The `spec.md` explicitly defines the goal as "Reproduce & Validate" the benchmark's *existence* and *mechanics*. It does not claim to measure the "plasticity" of the agents or the philosophical nature of research. The plan adheres to the spec: it validates that the benchmark *runs* and *scores* correctly.
**Action**: The plan includes a `mock` agent to ensure the pipeline runs without external dependencies. The "plasticity" of the agent is irrelevant to the *validation of the pipeline*. The plan will document that the benchmark's ability to distinguish between "child" and "adult" machine capabilities is a property of the *agent* being tested, not the *validation pipeline*.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Vendored code requires GPU** | High (Pipeline fails) | Use `mock` agent config to bypass model loading. If code hardcodes GPU, patch `src/cli/rcb_runner.py` to force CPU or skip model init. |
| **Task data missing** | High (Pipeline fails) | Implement `FileNotFoundError` check (FR-003). If `Astronomy_000` missing, fall back to `Chemistry_000` or first available task. |
| **Rubric weights malformed** | Medium (Invalid scores) | Implement strict validation in `rubric_checker.py` (FR-002). Fail fast if sum != 100. |
| **External API Rate Limits** | Medium (Test timeout) | The `mock` agent eliminates API calls. If real calls are needed, implement exponential backoff (FR-006) and limit retries to a predefined threshold. The retry logic is implemented in the wrapper layer, unconditional on agent type. |

## Limitations

-   **Scientific Validity**: This pipeline validates the *mechanical correctness* of the benchmark engine. It does *not* validate the *scientific validity* (i.e., whether the rubric accurately reflects human expert judgment or discriminates between agent capabilities). That requires human evaluation and real agent runs, which are outside the scope of this reproduction feature.
-   **Statistical Variance**: The aggregation test uses synthetic data. While it verifies the arithmetic of mean/std calculations, it does not test the system's ability to handle real-world statistical variance in agent performance.
-   **Paper Abstract Range**: The plan does *not* validate against the "expected range" of scores mentioned in the paper's abstract. That range is an empirical result of the original study, not a ground truth for the pipeline. Validating against it would create a circular dependency.