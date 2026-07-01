# Implementation Plan: PlanBench-XL Reproduction & Validation

**Branch**: `001-planbench-xl-reproduction` | **Date**: 2024-05-22 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-planbench-xl-reproduction/spec.md`

## Summary

This project reproduces and validates the PlanBench-XL benchmark (arXiv:2606.22388) within a constrained CPU-only CI environment. The approach involves vendoring the external repository, configuring a minimal subset of tasks, and executing the provided `scripts/run_retail_batch.py` entry point against specific conditions (default, blocking, noise) using accessible LLM APIs (e.g., `gpt-5.4-mini`). The plan strictly adheres to the CI time limit and RAM constraint by limiting task counts, enforcing strict timeouts (a bounded duration per tool and per task), and skipping GPU-dependent models.

**Critical Note on Scope**: Due to CI constraints (n=5 tasks), this project performs **functional validation** of the benchmark's mechanism (i.e., verifying that blocking/noise logic causes a performance drop) rather than **statistical validation** of the paper's specific effect sizes. The "statistically significant" requirement in the source spec is acknowledged as scientifically unattainable with this sample size and is flagged as a spec-level contradiction in `research.md`.

## Technical Context

**Language/Version**: Python 3.11 (required by vendored PlanBench-XL scripts)  
**Primary Dependencies**: `openai`, `pyyaml`, `pandas`, `tqdm`, `pytest` (for validation), `datasets` (if needed for local data handling)  
**Storage**: Local filesystem (`results/` directory for JSON logs and metrics)  
**Testing**: `pytest` (unit tests for timeout logic, integration tests for batch execution), manual validation of `eval_results.json`  
**Target Platform**: GitHub Actions Free Tier (Linux, 2 CPU, ~7GB RAM, no GPU)  
**Project Type**: CLI / Reproduction Pipeline  
**Performance Goals**: Complete 5-task run in <30 mins; total CI job <6 hours.  
**Constraints**: No GPU/CUDA; strict 60s timeout per tool call; max 500MB disk usage for logs.  
**Scale/Scope**: 5 tasks per configuration (Default, Blocker, Noise); 1 model configuration (`gpt-5.4-mini`) for primary validation.

## Constitution Check

*Gates determined based on project constitution (assumed standard research integrity & feasibility due to missing `constitution.md`).*

**Note**: No specific `constitution.md` was provided for this project (per input). The plan defaults to **Standard Research Integrity Principles** (Principles I-V) as a fallback.

1.  **Principle I (Reproducibility)**: The plan mandates exact reproduction of the `run_retail_batch.py` logic with minimal, documented deviations (task count reduction) to ensure the core logic is validated.
2.  **Principle II (No Silent Fallbacks)**: The plan addresses FR-006 (missing API keys) by defining the behavior as a **logged HARD FAILURE** for the specific model configuration, not a silent pass. If *all* models fail, the job exits with a non-zero code. This ensures missing keys are visible and do not silently invalidate the run.
3.  **Principle III (Data Integrity)**: The plan requires a startup check for the vendored submodule (`external/PlanBench-XL`) to prevent partial execution on corrupted data.
4.  **Principle IV (Transparency)**: The `reproduction_report.md` will explicitly list discrepancies between reproduced metrics and paper claims, including `[DEFERRED]` flags where data is missing, and explicitly state the underpowered nature of the study.
5.  **Principle V (Real-call testing)**: The plan executes real API calls but limits them to a small, manageable number of tasks to ensure feasibility. It validates that the *mechanism* of failure (blocking) works, rather than claiming to reproduce the full statistical findings.

## Project Structure

### Documentation (this feature)

```text
specs/001-planbench-xl-reproduction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Target schemas for validation)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
external/
└── PlanBench-XL/        # Vendored submodule containing scripts, tasks, tools
    ├── scripts/
    │   └── run_retail_batch.py
    ├── configs/
    │   ├── retail_gpt5.4_blocker.yaml
    │   └── retail_gpt5.4_noise_ratio_0p4.yaml
    └── data/
        ├── tasks.json
        └── database.json

src/
├── validation/
│   ├── check_timeouts.py      # Validates FR-004
│   ├── check_disk_usage.py    # Validates SC-005
│   └── validate_schema.py     # Validates contracts
├── analysis/
│   └── generate_report.py     # Generates reproduction_report.md (FR-007)

tests/
├── unit/
│   └── test_timeout_enforcement.py
└── integration/
    └── test_baseline_run.py
```

**Structure Decision**: The plan utilizes the existing vendored structure (`external/PlanBench-XL`) as the execution engine, wrapping it with a `src/` directory for validation and analysis scripts to ensure separation of concerns and compliance with the spec's reporting requirements. The `contracts/` directory contains the target schemas that the Implementer must ensure the generated data adheres to.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | The project is a direct reproduction of an existing benchmark; no new architectural complexity is introduced. | N/A |

## Phase 2: Execution & State Management

To address the concern of **learning effects** and **state persistence**:

1.  **State Reset Protocol**: Before executing each condition (Default, Blocker, Noise), the system MUST:
    *   Terminate any running agent processes.
    *   Delete the specific run directory `results/{run_id}/` to clear any cached state or partial logs.
    *   Restart the `run_retail_batch.py` script as a fresh process.
2.  **Order Randomization**: While the same 5 tasks are used across conditions to control for difficulty, the order of execution for the conditions is randomized (e.g., Default -> Noise -> Blocker vs. Blocker -> Default -> Noise) to mitigate any potential order effects, although the process restart mitigates most of this risk.
3.  **Stochastic Mitigation**: All runs MUST use `temperature=0.0` (or the lowest available setting) to minimize non-determinism. If time permits (within the available time limit), a subset of tasks will be run multiple times with different random seeds to estimate variance, but the primary validation relies on the single run with fixed temperature.