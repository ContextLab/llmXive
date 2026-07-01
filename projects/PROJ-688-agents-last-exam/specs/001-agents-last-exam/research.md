# Research: Agents' Last Exam Reproduction

## 1. Problem Definition & Scope

The goal is to reproduce the "Agents' Last Exam" benchmark **execution pipeline**. The scope is strictly limited to:
1.  **Environment Initialization**: Cloning the `agents-last-exam` repository and installing dependencies.
2.  **Pipeline Execution**: Running a single representative task (e.g., `ar_full_300` from the business finance tier) using a `dummy` agent to validate the infrastructure (sandbox, I/O, timeouts) without consuming API tokens.
3.  **Validation**: Generating a report that compares the **binary outcome** of this specific run against the paper's qualitative description of that task tier, while explicitly acknowledging that **aggregate statistical validation is impossible** with N=1.

**Key Constraints**:
-   **Compute**: Must run on GitHub Actions free-tier (2 CPU, ~7 GB RAM, no GPU).
-   **Time**: Total job ≤ 6 hours; per-task timeout ≤ 60 minutes.
-   **API**: Must handle missing API keys gracefully (fail with clear error, not crash).
-   **Scientific Scope**: This study validates **pipeline reproducibility**, not **agent cognitive performance** or **paper statistical claims**.

## 2. Dataset Strategy

**Source**: The "dataset" is the benchmark suite itself, contained within the `agents-last-exam` repository.
-   **Repository**: `agents-last-exam` (Submodule).
-   **Content**: Task definitions (prompts, expected outcomes, evaluation logic) located in `tasks/`.
-   **Selection Strategy**: Since the full suite (1000+ tasks) is computationally infeasible on free-tier CI, the plan selects a **single representative task** from the "hardest tier" (e.g., `tasks/business_finance/ar_full_300/main.py`) to validate the execution pipeline.
-   **Variable Fit**: The task definitions contain the necessary prompts and evaluation criteria. No external dataset is required for the execution phase.

**Note on URLs**: The plan relies on the **submodule mechanism** defined in the project configuration. If a specific URL is needed for documentation, it will be derived from the submodule source.

## 3. Methodological Approach

### 3.1 Execution Pipeline
1.  **Initialization**:
    -   Clone `agents-last-exam` into `external/`.
    -   Install dependencies via `pip`.
    -   Verify `ale_run` CLI is functional (`--help`).
2.  **Task Execution**:
    -   Invoke `ale_run` with the selected task ID and `--agent dummy` (or local config).
    -   Wrap execution in a timeout mechanism (e.g., `timeout 60m` or Python `signal` handler) to enforce the 60-minute limit.
    -   Capture stdout/stderr and exit codes.
3.  **Artifact Normalization & Validation**:
    -   **Parsing**: Parse the raw `ale_run` output (which may be unstructured or in a proprietary format) and transform it into the standardized `Task Execution Artifact` defined in `data-model.md`.
    -   **Schema Validation**: Validate the normalized JSON against `task_artifact.schema.yaml`. If validation fails, log an error and halt report generation.
    -   **Status Mapping**: Map execution outcomes to the canonical status set (`SUCCESS`, `FAILED`, `TIMEOUT`, `MISSING_API_KEY`, `SANDBOX_ERROR`).

### 3.2 Validation Logic & Scope
-   **Outcome Type**: With N=1, the result is a **binary event** (Pass or Fail), not a "rate".
-   **Comparison Strategy**:
    -   **Pipeline Check**: Did the code run to completion (or expected timeout) without crashing? (Yes/No)
    -   **Task-Level Check**: Does the observed outcome (Pass/Fail) align with the paper's qualitative description of the "hardest tier" (e.g., "far from saturated")?
    -   **Statistical Limitation**: The report will explicitly state: *"This study uses N=1. No statistical inference (p-values, confidence intervals) is claimed. The comparison to paper claims is anecdotal and serves only to verify the pipeline's ability to produce results consistent with the paper's setup."*
-   **Report Content**: The `validation_report.md` will contain:
    -   A table of executed tasks (N=1) with binary outcomes.
    -   A "Comparison to Paper Claims" section that contrasts the specific task outcome with the paper's tier description, explicitly noting the inability to validate aggregate statistics.

### 3.3 Statistical Rigor
-   **Sample Size**: N=1 (representative task).
-   **Limitation**: Explicitly acknowledged. No statistical inference is claimed.
-   **Causal Inference**: Not applicable; this is a reproducibility check of code behavior, not a causal study.
-   **Construct Validity**: The study distinguishes between "Pipeline Validation" (dummy agent) and "Agent Performance Validation" (real agent). This study only validates the former.

## 4. Compute Feasibility Analysis

-   **Hardware**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM).
-   **GPU**: None required. The `ale_run` sandbox and agent logic are CPU-bound.
-   **Memory**: The dummy agent and standard Python execution fit well within 7 GB.
-   **Disk**: The repository and artifacts are < 1 GB.
- **Time**: One task (time-limited) + setup (10 min) + report (5 min) = [deferred] total, well under the 6-hour limit.

## 5. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **Missing API Keys** | Detect `ANTHROPIC_API_KEY`/`OPENAI_API_KEY` at startup. If missing, run in `dummy` mode or exit with code 2 and clear message. |
| **Sandbox Timeout** | Enforce 60-minute hard timeout per task. Log `TIMEOUT` status. |
| **Submodule Corruption** | Verify `external/agents-last-exam` exists and has valid git history before proceeding. |
| **CI Resource Exhaustion** | Limit to 1 task. No parallelization. |
| **Schema Mismatch** | Insert explicit schema validation step before report generation to ensure data model compliance. |

## 6. Decision Log

| Decision | Rationale |
|----------|-----------|
| **Single Task Execution** | Running the full suite is infeasible on free-tier CI. A single representative task validates the pipeline. |
| **Dummy Agent** | Prevents token consumption and API key dependency for the baseline pipeline test. Explicitly scoped as "Pipeline Validation" only. |
| **Hard Timeout** | Prevents CI jobs from hanging indefinitely on stuck tasks. |
| **No GPU Usage** | The spec and compute constraints explicitly forbid GPU; the codebase does not require it for the baseline run. |
| **Reframed Validation** | Changed goal from "Validating Paper Claims" to "Validating Pipeline Reproducibility" to align with N=1 scientific limitations. |