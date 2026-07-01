# Implementation Plan: Reproduce & Validate Arbor (Hypothesis-Tree Refinement)

**Branch**: `001-reproduce-arbor` | **Date**: 2024-05-21 | **Spec**: `spec.md`

## Summary

This project aims to reproduce the core execution flow and validation logic of the "Arbor" autonomous research system within a constrained CPU-only CI environment (GitHub Actions free tier). The primary technical approach involves vendoring the Arbor codebase, configuring it for CPU-only inference (avoiding CUDA/quantization dependencies that fail on CPU), and executing a minimal benchmark task (`algotune_knn` or `dashboard_demo`). 

**Critical Scope Clarification**: This phase is defined as **Engineering Validation** (verifying the HTR mechanism runs, generates a valid tree, and links logs) and **Local Baseline Comparison** (HTR vs. Random Search on Iris/Wine). It explicitly **does not** claim to scientifically validate the paper's "2.5x gain" claim, as the necessary large-model capacity and statistical power are not available in this environment. Success is defined by the generation of non-empty, schema-valid artifacts and the completion of the benchmark loop within 6 hours and 7GB RAM.

## Technical Context

**Language/Version**: Python 3.10+ (Standard for AI/ML research codebases)  
**Primary Dependencies**: `arbor` (vendored), `transformers` (CPU-optimized), `torch` (CPU-only build), `scikit-learn` (for `algotune_knn`), `pyyaml`, `pytest`, `memory_profiler`  
**Storage**: File system (JSON for tree state, logs, results)  
**Testing**: `pytest` (for unit validation), CI integration tests (for end-to-end execution)  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner)  
**Project Type**: Research Reproduction / CLI Tool Validation  
**Performance Goals**: Execution < 6 hours; Memory < 7GB; No GPU dependency.  
**Constraints**: 
- No CUDA/GPU libraries.
- No 8-bit/4-bit quantization requiring `bitsandbytes` (unless strictly CPU-compatible, otherwise default to float32/16).
- Dataset must be small enough to fit in RAM (or streamed).
- Must handle timeouts gracefully.

**Scale/Scope**: Single benchmark task execution (`algotune_knn` or `dashboard_demo`) to validate the HTR loop.

## Constitution Check

**Status**: **PENDING / BLOCKING GAP**

*Note: The `constitution.md` content was not provided in the input.*

Per the panel review protocol, the plan cannot be fully approved without verifying it does not violate the project's specific constitutional principles. The following are potential conflicts that require the `constitution.md` to resolve:

1.  **Principle: No Silent Fallbacks** (Potential Conflict): The plan includes a strategy to "fallback to standard precision" if 8-bit quantization fails. If the constitution strictly forbids silent fallbacks, this plan violates it.
2.  **Principle: Real-Call Testing** (Potential Conflict): If the constitution requires testing against a live, external API, the plan's reliance on local CPU models may violate it.
3.  **Principle: Data Integrity** (Potential Conflict): If the constitution mandates specific data handling protocols not covered by `sklearn` built-ins, the current dataset strategy may need revision.

**Action Required**: The `constitution.md` file must be provided to validate these points. Until then, the plan assumes standard scientific integrity principles but flags these as potential blocking issues.

## Project Structure

### Documentation (this feature)

```text
specs/001-reproduce-arbor/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── tree-node.schema.yaml
    └── benchmark-result.schema.yaml
```

### Source Code (repository root)

```text
# Option 1: Single project (Reproduction)
projects/001-reproduce-arbor/
├── .specify/
│   ├── scripts/
│   │   └── setup-plan.sh
│   ├── templates/
│   └── memory/
├── src/                 # (If any wrapper scripts are needed)
│   ├── run_arbor.py     # Main execution wrapper
│   ├── monitor_resources.py # Resource tracking
│   └── generate_report.py # Report generation
├── tests/
│   └── test_artifacts.py
└── vendor/              # Vendored Arbor codebase
    ├── arbor/
    ├── examples/
    └── requirements.txt
```

**Structure Decision**: The project is a reproduction effort. The primary code is vendored. We will wrap the execution in simple scripts (`run_arbor.py`, `monitor_resources.py`) to enforce timeouts, capture artifacts, and measure resources, rather than modifying the core Arbor logic.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope is strictly limited to running existing code. | N/A |

## Phase Breakdown

### Phase 0: Research & Feasibility (Research.md)
- **Objective**: Verify dataset availability, confirm CPU-tractability of the model, and validate the `algotune_knn` task requirements.
- **FR Mapping**: FR-003 (CPU-only), FR-006 (Timeouts).
- **SC Mapping**: SC-003 (Resource Compliance).
- **Key Activities**:
  - Analyze `requirements.txt` for CUDA dependencies.
  - Identify the exact model used in `algotune_knn` and verify a CPU-compatible variant exists.
  - Confirm the dataset for `algotune_knn` is small enough for 7GB RAM.
  - **New**: Define the "Null Hypothesis" and "Random Search Baseline" strategy for scientific comparison.

### Phase 1: Data Model & Contracts (Data-Model.md, Contracts/)
- **Objective**: Define the schema for `tree.json` and `eval_results.json` to ensure the Implementer can validate outputs.
- **FR Mapping**: FR-002 (Tree generation), FR-005 (Report generation), FR-004 (Log linking).
- **SC Mapping**: SC-001 (Artifact Generation), SC-004 (Tree Integrity), SC-005 (Baseline Comparison).
- **Key Activities**:
  - Define `TreeNode` schema (Hypothesis, Evidence, Artifact types) with `log_file_path` for FR-004.
  - Define `BenchmarkResult` schema with `peak_memory_mb`, `total_runtime_seconds`, and dynamic baseline fields.
  - Define the `summary.md` report template.

### Phase 2: Quickstart & Execution (Quickstart.md)
- **Objective**: Provide the exact commands to clone, install, and run the system with CPU constraints.
- **FR Mapping**: FR-001 (Execution), FR-003 (CPU-only).
- **SC Mapping**: SC-002 (Execution Completeness).
- **Key Activities**:
  - Document `pip install` steps (pinning `torch` CPU version).
  - Define the CLI command with `--dry-run`, `--timeout`, and `--baseline-mode` flags.

### Phase 3: Implementation (Handled by Implementer Agent)
- **Objective**: Write the wrapper script and CI workflow.
- **FR Mapping**: All FRs.
- **SC Mapping**: All SCs.
- **Implementation Artifacts**:
  - `src/run_arbor.py`: Orchestrates the run, enforces timeouts.
  - `src/monitor_resources.py`: Wraps the process to log `peak_memory_mb` and `total_runtime_seconds`.
  - `src/generate_report.py`: Reads `eval_results.json` and writes `summary.md` with the required baseline comparison.
  - `tests/test_artifacts.py`: Validates `tree.json` structure and log linking.
- **FR/SC Mapping Table**:
  | Artifact | Addresses |
  |----------|-----------|
  | `run_arbor.py` | FR-001, FR-003, FR-006 |
  | `monitor_resources.py` | SC-003 |
  | `generate_report.py` | FR-005, SC-005 |
  | `tests/test_artifacts.py` | FR-004, SC-001, SC-004 |

### Phase 4: Validation
- **Objective**: Run the pipeline and verify against schemas.
- **FR Mapping**: FR-004 (Logging), FR-006 (Timeouts).
- **SC Mapping**: SC-005 (Baseline Comparison).
- **Key Activities**:
  - Execute the HTR run.
  - Execute the Random Search baseline run.
  - Run `memory_profiler` to capture peak RAM.
  - Validate `tree.json` against schema (including log paths).
  - Validate `eval_results.json` against schema.
  - Generate `summary.md` and verify it contains the comparison.

## Compute Feasibility Strategy

- **Model Selection**: The plan mandates using a CPU-optimized small model (e.g., `Phi-2` or `Llama-3-8B` in standard float32 if memory permits, otherwise a smaller distilled model) via `transformers` with `device="cpu"`.
- **Quantization**: Explicitly avoid `bitsandbytes` or `load_in_8bit` as these often require CUDA. If the codebase forces this, the plan includes a patch to fallback to standard precision or a smaller model.
- **Memory Management**: The `algotune_knn` task is chosen specifically because it operates on small tabular data (KNN on Iris or similar), fitting easily in RAM. The tree state will be kept in memory but flushed to JSON frequently.
- **Timeouts**: A wrapper script will enforce a 300s timeout per hypothesis step to prevent hanging, as per FR-006.
- **Baseline Strategy**: To ensure fair comparison, the baseline (Random Search) will be run with the *same* data split, preprocessing, and evaluation metric as the HTR run.