# Implementation Plan: llmXive follow-up: extending "Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages"

**Branch**: `001-llmxive-multilingual-logic-transfer` | **Date**: 2026-07-13 | **Spec**: `specs/001-llmxive-multilingual-logic-transfer/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-multilingual-logic-transfer/spec.md`

## Summary

This feature implements a rigorous evaluation pipeline to test the **associational hypothesis** that providing a "Partial Logic Trace" (the initial algorithmic steps of a ground-truth Python solution) as a few-shot anchor is associated with improved **Logic-Compliant Pass@1 (LC-Pass@1)** in target languages (e.g., rust, kotlin) where models previously failed. The system extracts logic anchors via AST parsing, constructs guided prompts, executes generated code in a CPU-isolated sandbox with strict timeouts, categorizes failures (Syntax, Library, Runtime, Logic Transfer), and performs paired statistical analysis (McNemar's test) on a stratified dataset of tasks. The entire pipeline is designed to run within the constraints of a GitHub Actions free-tier runner (limited CPU, 7GB RAM, 6h limit) without GPU acceleration.

**Critical Data Block**: The study relies on a multilingual dataset (Multi-LCB) containing ground-truth solutions in target languages (Rust/Kotlin). If the verified datasets (LCB-R, LCB-R-F) do not contain these fields, the **Statistical Analysis** and **Cross-Language** components are blocked. A fallback strategy is defined: if no multilingual ground truth exists, the study reverts to **Python-to-Python Logic Fidelity** to maintain methodological validity.

**Note on Causality**: This study uses an observational design. Findings will be framed as **associational improvements** in LC-Pass@1, not causal proof of "reasoning transfer," as the design lacks randomization of tasks to conditions.

## Technical Context

**Language/Version**: Python 3 (for orchestration, AST parsing, stats) | Rust (for sandbox execution of target code) | Kotlin (via JVM, sandboxed)  
**Primary Dependencies**: `llama-cpp-python` (CPU-only GGUF support), `datasets` (HuggingFace), `ast` (stdlib), `subprocess` (stdlib), `scipy` (stats), `pandas`, `pyyaml`, `pytest`, `joblib` (parallelization)  
**Storage**: Local filesystem (`data/` for datasets/results, `data/` checksums managed by constitution)  
**Testing**: `pytest` (unit/integration), custom sandbox execution harness  
**Target Platform**: GitHub Actions free-tier runner (Linux, multi-core, 7GB RAM, no GPU)  
**Project Type**: Research pipeline / CLI tool  
**Performance Goals**: Process 200 tasks (blind + guided) in ≤ 6 hours total runtime; memory footprint < 6GB during inference.  
**Constraints**: No GPU/CUDA; no 8-bit/4-bit quantization requiring CUDA (`bitsandbytes` forbidden); strict timeout per test case; deterministic random seeds; CPU-only model loading via `llama-cpp-python`.  
**Scale/Scope**: A set of algorithmic tasks (stratified by difficulty/topic); two conditions (blind vs. guided); A selected subset of target languages (rust, kotlin, go). **Fallback**: If multilingual data is missing, scope reduces to Python-only logic fidelity.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification / Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, fixed random seeds, and re-fetching datasets from canonical HuggingFace URLs on every run. |
| **II. Verified Accuracy** | **PASS** | All dataset references (LCB-R) are from the `# Verified datasets` block. No fabricated URLs. **Note**: Study blocked if multilingual ground truths are not found. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of raw datasets and derivation of new files (filtered sets, results) without modifying raw data. |
| **IV. Single Source of Truth** | **PASS** | All metrics (LC-Pass@1, p-values) will be derived programmatically from `data/results.csv` and written to `data/statistical_report.yaml`. |
| **V. Versioning Discipline** | **PASS** | Plan includes content hashing for data artifacts and timestamp updates in `state/`. |
| **VI. Cross-Language Logic Fidelity** | **PASS** | Explicit "Logic Transfer Failure" categorization (FR-004) ensures logic drift is detected. **Crucially**, the plan defines **LC-Pass@1** such that these cases are *not* counted as passes, satisfying the Constitution's requirement to exclude logic drift from the success metric. |
| **VII. Paired Statistical Rigor** | **PASS** | Plan mandates McNemar's test on the *same* 200 tasks for both blind and guided conditions, avoiding unpaired comparisons. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-multilingual-logic-transfer/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (sibling to plan.md)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/
├── data/
│   ├── raw/                 # Downloaded parquet files (checksummed)
│   ├── processed/           # Filtered task sets, logic traces
│   └── results/             # Execution logs, pass/fail status, stats
├── code/
│   ├── __init__.py
│   ├── config.py            # Paths, seeds, model configs
│   ├── dataset.py           # Loading, filtering, stratification (FR-006)
│   ├── logic_anchor.py      # AST parsing, trace extraction (FR-001.1)
│   ├── prompt_builder.py    # Prompt construction (FR-001)
│   ├── inference.py         # CPU-only model loading & generation (llama-cpp)
│   ├── sandbox.py           # Execution harness, timeout, error parsing (FR-002, FR-003, FR-004)
│   ├── stats.py             # McNemar's test, error categorization (FR-005, FR-004)
│   └── main.py              # Orchestration pipeline (parallelized via joblib)
├── tests/
│   ├── unit/
│   │   ├── test_logic_anchor.py
│   │   └── test_sandbox.py
│   ├── integration/
│   │   └── test_pipeline.py
│   └── contract/
│       └── test_schemas.py
├── requirements.txt         # Pinned dependencies
└── README.md
```

**Structure Decision**: Single project structure selected to minimize overhead. Separation of concerns (dataset, anchor, inference, sandbox, stats) ensures modularity and testability. The `code/` directory mirrors the functional requirements directly.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Selection Bias (FR-006)** | The spec mandates a "Stochasticity Filter" (fail ≥ 2/3 runs) to ensure task difficulty. | Removing this filter violates the spec. The plan retains the filter but adds a **Methodological Risk** section to explicitly acknowledge the resulting bias (regression to the mean) and limits the interpretation of results to this specific subset. |

## Statistical Analysis & Metric Definition

**LC-Pass@1 Calculation**: The primary metric is **Logic-Compliant Pass@1 (LC-Pass@1)**.
`LC-Pass@1_guided = (Count of tasks where Guided Output Passes Tests AND Implements Anchor Steps) / Total Tasks`

**Logic Fidelity Definition**: A task is considered to "Implement Anchor Steps" if the generated code's Abstract Syntax Tree (AST) contains the subgraph corresponding to the 3 anchor steps extracted from the Python solution. This is a structural check, not keyword matching.

**Logic Transfer Exclusion**: Per Constitution Principle VI, any task where the generated code passes all tests but **fails** the AST structural comparison against the Partial Logic Trace is **not counted** in the numerator of the LC-Pass@1 metric. This ensures the metric reflects true logic transfer, not just functional correctness via a different algorithm.

**Statistical Test**: McNemar's test is applied to the paired binary outcomes (LC-Pass@k Pass/Fail) for the same set of tasks.

**Limitations**: The p-value derived from this test applies only to the specific subset of tasks selected (tasks where the model failed at least once in a pilot run, and specifically those failing ≥2/3 runs per FR-006). It cannot be generalized to all coding tasks without further randomization. The selection filter introduces a bias where the baseline is artificially depressed; improvements must be interpreted as valid only for this "hard" subset.

## Fallback Strategy

If the verified datasets (LCB-R, LCB-R-F) do not contain ground-truth solutions in target languages (Rust/Kotlin):
1.  **Scope Reduction**: The study will be re-scoped to **Python-to-Python Logic Fidelity**.
2.  **Methodology**: The "Target Language" will be Python. The "Partial Logic Trace" will be extracted from a *different* Python solution (or a subset of the same solution) to test if providing the anchor improves generation of a *new* Python solution.
3.  **Reporting**: The final report will explicitly state that the study was limited to Python-only due to data constraints, and the "Cross-Language" hypothesis was not tested.

## Methodological Risk: Selection Bias (FR-006 Compliance)

**Observation**: The source specification (FR-006) mandates a "Stochasticity Filter" where tasks are only included if the model fails in ≥ 2 of 3 blind runs.
**Risk**: This filter creates a "regression to the mean" bias. By selecting only the most difficult/stochastic tasks, the baseline performance is artificially low. Any intervention (even random noise) is statistically likely to show improvement on this specific subset.
**Mitigation**:
1.  The plan **strictly adheres** to FR-006 to maintain spec compliance.
2.  The **Statistical Report** will explicitly label the population as "Tasks with high stochastic failure (≥2/3 runs)" and will **not** claim generalizability to the full dataset.
3.  The **Discussion** section of the final report will dedicate a paragraph to this limitation, noting that the observed improvement is a lower-bound estimate for the "hard" subset but cannot be extrapolated to the general population of coding tasks.
4.  The **Research Questions** will be phrased to reflect this constraint: "Is there an improvement in LC-Pass@1 *for this specific subset of high-failure tasks*?"