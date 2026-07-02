# Implementation Plan: MMSkills Reproduction & Validation

**Branch**: `001-mmskills-reproduction` | **Date**: 2024-05-21 | **Spec**: `specs/001-mmskills-towards-multimodal-skills-for-g/spec.md`
**Input**: Feature specification from `/specs/001-mmskills-towards-multimodal-skills-for-g/spec.md`

## Summary

This feature implements a **Pipeline Robustness & Structural Integrity** validation for the MMSkills framework ("Towards Multimodal Skills for General Visual Agents"). The technical approach involves installing dependencies with CPU-locked PyTorch, implementing a robust skill loader that validates JSON and image assets against verified data sources, and executing a small subset of the OSWorld benchmark with strict per-task timeouts and memory profiling.

**Important Scope Clarification**: This run validates **Pipeline Robustness** and **Structural Integrity** (can the code run, parse the data, and execute the first step without crashing?). It **does not** validate the "multimodal procedural knowledge" claim by comparing success rates against the paper's GPU-accelerated baseline, as such a comparison is scientifically invalid due to hardware differences (CPU vs GPU) and sample size (N=5). The primary metric is whether the system correctly handles data, logs errors (including missing assets), and respects resource limits.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `torch` (CPU-only), `transformers`, `datasets`, `pillow`, `pandas`, `pyyaml`, `psutil` (for RSS memory), `tracemalloc` (built-in), `pytest`  
**Storage**: Local filesystem (for skill assets, logs, and metrics CSV)  
**Testing**: `pytest` (unit tests for loader, integration tests for timeout logic)  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, Limited RAM, No GPU)  
**Project Type**: Research/Validation Tool  
**Performance Goals**: Run 5 tasks in < 6 hours; < 7GB RAM peak usage  
**Constraints**: No CUDA imports; Hard m timeout per task; Graceful degradation on missing assets (logged as `asset_error_count`); Constitution check required.  
**Scale/Scope**: Subset of tasks from OSWorld benchmark (fetched from verified source).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Action**: The plan explicitly checks for the existence of `constitution.md` at the project root (`projects/PROJ-599-mmskills-towards-multimodal-skills-for-g/constitution.md`).
- **If Found**: The plan proceeds to validate against the numbered principles within that file.
- **If Missing**: The plan **HALTS** immediately with error code `2` and the message: "Constitution Missing: FR-030 violation. Cannot proceed without project SSoT."
- **Note**: No assumptions are made about "standard" principles. If the file is absent, the project is blocked.

## Project Structure

### Documentation (this feature)

```text
specs/001-mmskills-towards-multimodal-skills-for-g/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Existing Schemas (Validation Targets)
│   ├── agent_action.schema.yaml
│   ├── metrics_schema.yaml
│   └── skill_package.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── mmskills/
│   ├── __init__.py
│   ├── loader.py          # Skill package loader (JSON/Image validation + Asset Counting)
│   ├── agent.py           # CPU-only agent execution logic
│   ├── evaluator.py       # Benchmark runner with timeout + Memory Profiling (psutil)
│   └── utils.py           # Timeout decorators, logging helpers
├── external/
│   └── MMSkills/          # Git submodule (Code only, NOT data)
├── skills_library/        # Local cache of fetched dataset
│   └── chrome/
├── tests/
│   ├── test_loader.py
│   ├── test_evaluator.py
│   └── test_timeout.py
├── requirements.txt
└── run.py                 # Entry point
```

**Structure Decision**: A monolithic `src/mmskills` package is selected to keep the validation logic tightly coupled with the external submodule. This avoids complex cross-repo imports and simplifies the CPU-only dependency resolution. The `external/MMSkills` is treated as a read-only submodule (code only); the actual benchmark data is fetched from the verified OSWorld HuggingFace repository during Phase 0.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Custom Timeout Logic | CI runners (GitHub Actions) do not guarantee per-task termination; A hard time limit is required to prevent the whole job from hanging if a task hangs.. | Relying on the original `MMSkills` code alone is risky as it may lack robust timeout handling for CI environments. |
| Asset Validation Layer | The original code may assume assets exist; we must explicitly verify `IMAGE_REFERENCE_LIST.md` to prevent "silent failures" or crashes during execution. | Skipping validation could lead to misleading "execution errors" that are actually just missing data, violating reproducibility. |
| Memory Profiling | Required by SC-004 to measure peak usage against CI limits. | Standard logging does not capture peak RSS; `psutil` is required for accurate measurement of native memory. |
| Constitution Check | Required by FR-030 and Constitution Principle I. | Assuming a "standard" constitution violates the Single Source of Truth principle. |
| Data Fetching (HuggingFace) | Required to ensure binary assets (images) are present. Submodule is code-only. | Relying on submodule for data risks missing files and construct validity failure. |
| Schema Compatibility | Required to ensure OSWorld data matches MMSkills skill structure. | Fetching data without verifying schema leads to runtime parsing errors. |