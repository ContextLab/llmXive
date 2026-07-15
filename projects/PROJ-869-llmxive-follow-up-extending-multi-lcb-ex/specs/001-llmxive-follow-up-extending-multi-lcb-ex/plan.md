# Implementation Plan: llmXive follow-up: extending "Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages"

**Branch**: `001-llmxive-multilingual-logic-transfer` | **Date**: 2026-07-13 | **Spec**: `specs/001-llmxive-multilingual-logic-transfer/spec.md`
**Input**: Feature specification from `specs/001-llmxive-multilingual-logic-transfer/spec.md`

## Summary

This feature implements a rigorous evaluation pipeline to test the "Logic Anchor" hypothesis: that providing a partial logic trace (derived from a successful Python solution) as a few-shot anchor improves code generation correctness in target languages (e.g., Rust, Kotlin) where models previously failed. The system extracts the first 3 algorithmic steps from ground-truth Python solutions, injects them into prompts for target-language generation, executes the output in a sandboxed CPU environment, and performs paired statistical analysis (McNemar's test) against a blind baseline. 

**Crucial Feasibility Adjustment**: To meet the strict 6-hour runtime constraint on a 2-core CPU (SC-004), the primary model is a **1.1B parameter CPU-optimized model (e.g., TinyLlama-1.1B-Chat or Phi-2)**. A medium-sized model is explicitly rejected for the main run as it would require a prohibitive amount of time. The study design is adjusted to test the hypothesis on a smaller, more capable model to ensure feasibility, acknowledging the trade-off in model capability for execution time. If the model fails to generate valid code, a fallback to a 50-task subset with a larger model is defined.

The pipeline is strictly constrained to run on GitHub Actions free-tier (limited CPU, limited RAM, 6h limit) using CPU-quantized models (GGUF via `llama-cpp-python`) and deterministic error categorization based on spec-defined **keyword/control-flow matching** (explicitly rejecting structural AST subgraph checks). The study frames conclusions as **associational improvements on a specific subset of difficult tasks**, not general causal mechanisms, due to the non-randomized, pre-screened dataset.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `llama-cpp-python` (CPU-only GGUF), `datasets` (HuggingFace), `pandas`, `scipy`, `networkx` (for AST/graph analysis if needed, but spec mandates keyword matching), `pytest`, `docker` (for sandbox isolation, or `subprocess` with strict timeouts).  
**Storage**: Local file system (`data/` for raw/processed datasets, `results/` for logs/metrics).  
**Testing**: `pytest` (unit/integration), `docker` (sandbox stability).  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Computational Research Pipeline / CLI.  
**Performance Goals**: Process 200 tasks (including 3 blind runs + 1 guided run per task) within ≤6 hours on 2 CPU cores using a **1.1B parameter model**.  
**Constraints**: No GPU; no `bitsandbytes` (4/8-bit quantization via CUDA); strict timeout per test case; dataset selection must include "Stochasticity Filter" (≥2/3 blind failures); error categorization must use **keyword/control-flow matching** (not structural AST subgraph); **Valid Alternative Check** to exclude library-based solutions from "Logic Transfer Failure".  
**Scale/Scope**: A set of algorithmic tasks (stratified by difficulty/topic); Multiple execution conditions (3 blind + 1 guided) per task.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **I. Reproducibility**: Plan ensures random seeds are pinned in `code/`. External datasets (LCB) are fetched from verified HuggingFace URLs. All transformations produce new files with checksums.
2.  **II. Verified Accuracy**: All dataset citations in `research.md` and `data-model.md` reference ONLY the verified URLs provided in the `# Verified datasets` block. No fabricated URLs.
3.  **III. Data Hygiene**: Raw data is preserved; derived data (filtered sets, baseline metrics) are written to new files with documented derivation steps. PII scan will be enforced.
4.  **IV. Single Source of Truth**: Statistical reports and error distributions trace back to `results/` logs. No hand-typed numbers in `paper/`.
5.  **V. Versioning Discipline**: All artifacts (datasets, code, results) will carry content hashes. The `state/` YAML will be updated on artifact changes.
6.  **VI. Cross-Language Logic Fidelity**: The plan explicitly implements "Logic Transfer Failure" detection via **keyword/control-flow matching** (per spec FR-004), rejecting the structural AST subgraph approach. It also includes a "Valid Alternative Check" to exclude library-based solutions, ensuring the metric distinguishes syntax translation from reasoning deficits.
7.  **VII. Paired Statistical Rigor**: The plan mandates a paired McNemar's test on the exact same 200-task subset for both "blind" and "guided" conditions. Unpaired comparisons are prohibited.

**Resolution of Unresolved Concerns**:
-   **Stochasticity Filter (FR-006.2)**: The plan includes a dedicated task **T017** to execute the filter logic (re-run blind 3 times, include if fail ≥2/3).
-   **Baseline Recording (SC-001)**: A specific task **T018** is defined to persist the `data/blind_baseline_metrics.yaml` artifact after the stochasticity filter runs.
-   **Error Categorization (FR-004)**: The plan explicitly mandates **keyword/control-flow matching** for Logic Transfer Failure, and **T022** details the specific string-matching algorithm, rejecting the AST approach.
-   **Compute Constraints**: Model loading uses `llama-cpp-python` with GGUF (standard CPU quantization), and the primary model is **1.1B** to ensure 6h runtime. A fallback to a small-scale model/baseline tasks is defined.
-   **Orchestration for Time Limit (SC-004)**: The plan includes a specific task **T034** to implement the orchestration logic (dynamic task skipping, resource monitoring) to guarantee the ≤6h constraint.
-   **Dependency Ordering**: The pipeline order is corrected: Data Download → Model Load → Blind Runs (to filter) → Guided Runs → Analysis.
-   **Selection Bias**: The plan explicitly reframes conclusions as "associational improvements on a specific subset" and includes a "Regression to the Mean" discussion and bootstrap resampling.
-   **Valid Alternative Check**: The plan updates "Logic Transfer Failure" definition to exclude valid alternative implementations (e.g., library calls).

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-multilingual-logic-transfer/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/
├── data/
│   ├── raw/             # Downloaded parquet files (checksummed)
│   ├── processed/       # Filtered task sets, baseline metrics
│   └── results/         # Execution logs, Pass/Fail matrices
├── code/
│   ├── __init__.py
│   ├── config.py        # Hyperparameters, seeds, paths
│   ├── data_loader.py   # Dataset fetching and parsing
│   ├── model_inference.py # GGUF loading, prompt construction, generation
│   ├── execution_harness.py # Sandbox execution, timeout enforcement
│   ├── logic_anchor.py  # Partial Logic Trace extraction (AST parsing)
│   ├── error_categorizer.py # Keyword/control-flow matching logic (string search)
│   ├── orchestrator.py  # Task scheduling, resource monitoring, time limits
│   └── statistical_analysis.py # McNemar's test, report generation
├── tests/
│   ├── unit/            # Unit tests for each module
│   ├── integration/     # End-to-end pipeline tests
│   └── contract/        # Schema validation tests
├── requirements.txt     # Pinned dependencies
└── run_pipeline.sh      # Entry point script
```

**Structure Decision**: A single cohesive Python package (`code/`) with modular separation of concerns (data, model, execution, analysis) is chosen. This aligns with the "Computational Research Pipeline" nature of the project and facilitates reproducibility on the GitHub Actions runner. The `orchestrator.py` module specifically addresses the time constraint (SC-004) by managing task queues and resource limits.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Constitution Check passed with all concerns resolved. | N/A |

## Implementation Phases & Tasks

### Phase 0: Data Ingestion & Feasibility Check
- **T001**: Download raw datasets from verified HuggingFace URLs.
- **T002**: Verify dataset checksums and record in `state/`.
- **T003**: **Model Feasibility Gate**: Measure token throughput of the 1.1B GGUF model on the target runner. If throughput < 2 tokens/sec, trigger fallback to 3B model with 50 tasks.

### Phase 1: Data Preparation & Filtering
- **T015**: Load CPU-quantized model (GGUF) using `llama-cpp-python` with standard CPU quantization (e.g., `q4_0`). **Explicitly avoid `bitsandbytes`**.
- **T016**: Implement dataset filtering logic: Select tasks where model failed in target language but succeeded in Python.
- **T017**: **Implement Stochasticity Filter**: Re-run blind condition 3 times for each candidate task. Include task only if it fails in ≥2 of 3 runs. **Output**: `data/filtered_tasks.json`.
- **T018**: **Persist Baseline Metrics**: Calculate and write the empirical baseline Pass@1 for the filtered tasks to `data/blind_baseline_metrics.yaml`. **This satisfies SC-001**.

### Phase 2: Logic Anchor Extraction
- **T020**: Implement AST parsing of Python solutions to extract the first few *critical* algorithmic operations (e.g., loops, recursive calls, not just initialization).
- **T021**: Serialize extracted steps into pseudo-code/Python for the anchor.

### Phase 3: Execution & Evaluation
- **T022**: **Logic Transfer Failure Detection**: Implement **keyword/control-flow matching** logic.
    - *Algorithm*: Search the generated code string for specific keywords, function names, and control flow structures defined in the anchor (e.g., `for`, `while`, `recursion`, specific variable names).
    - *Valid Alternative Check*: If the code passes tests but uses a standard library function that encapsulates the anchor steps, mark as "Pass" (or "Library Misuse" if incorrect), NOT "Logic Transfer Failure".
    - *Reject*: Do NOT use AST subgraph checks.
- **T023**: Run Guided condition on the 200 tasks.
- **T024**: Execute generated code in sandbox with 10s timeout.
- **T025**: Categorize errors using the logic in T022.

### Phase 4: Statistical Analysis & Reporting
- **T030**: Perform paired McNemar's test on the 200 tasks.
- **T031**: Perform bootstrap resampling to estimate confidence intervals (addressing regression to the mean).
- **T032**: Generate `statistical_report.yaml`.

### Phase 5: Orchestration & Validation
- **T033**: Validate execution time (verify total time ≤ 6h).
- **T034**: **Implement Orchestration Logic**: Build dynamic task skipping, resource monitoring, and parallelization tuning in `orchestrator.py` to **guarantee** the 6h constraint. This task is critical for meeting SC-004.
- **T035**: Final validation of all artifacts and checksums.
