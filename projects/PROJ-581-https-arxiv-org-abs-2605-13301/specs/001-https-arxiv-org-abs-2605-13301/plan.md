# Implementation Plan: Reproduce & Validate SU-01 Olympiad Reasoning

**Branch**: `581-reproduce-su01-olympiad` | **Date**: 2026-05-22 | **Spec**: `specs/581-reproduce-su01-olympiad/spec.md`

## Summary

This project validates the **feasibility of the SU-01 pipeline** and the **logic of the evaluation mechanism** on a CPU-only CI environment (GitHub Actions free tier). It explicitly **does not** claim to validate the "gold-medal-level" performance claims of the paper, as the 30B model weights are unlikely to be present in the submodule, and the sample size (n=2) is statistically insufficient for performance claims. 

The technical approach involves bootstrapping a CPU-compatible Python environment, initializing the `external/SU-01` git submodule, and executing the `su01-eval` pipeline on a minimal subset of available Olympiad datasets. The plan prioritizes **pipeline integrity** and **error handling**. If the 30B model weights are missing, the pipeline degrades to "Pipeline Logic Validation" only, and the final report will explicitly state "Claim Unverifiable" rather than a false "Reproduced" or "Failed" verdict on the reasoning capability. **No placeholder models (e.g., TinyLlama) or dummy generators are permitted for performance validation.**

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `torch` (CPU-only build), `transformers`, `accelerate` (CPU mode), `datasets`, `pytest`, `rich` (for logging)  
**Storage**: Local filesystem (temporary artifacts in `output/`), Git submodule for code  
**Testing**: `pytest` (unit tests for import integrity), shell script assertions for pipeline execution  
**Target Platform**: GitHub Actions free-tier runner (Linux, 2 vCPU, ~7GB RAM, no GPU)  
**Project Type**: Computational research / Reproduction pipeline  
**Performance Goals**: Complete validation pipeline (submodule init + small subset eval) within 6 hours.  
**Constraints**: 
- **Hard Constraint**: Strict CPU-only execution; no CUDA dependencies.
- **Hard Constraint**: Memory usage <7GB.
- **Hard Constraint**: -minute timeout for any single script execution (enforced by system, per FR-007).
- **Hard Constraint**: Graceful degradation if model weights are absent (must not silently fallback to dummy for performance claims; must skip inference and log warning).

**Scale/Scope**: Validation of a small number of problems from `imo25` or `usamo2026` subsets

The research question, the method, and the references remain unchanged as no specific values were asserted in those elements, and no citations were present in the original passage to preserve.; full pipeline logic verification. **Note**: This scope is for *pipeline sanity checking* only, not statistical validation of the paper's performance claims.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

- **Principle I (SSoT)**: The plan enforces deterministic execution via pinned dependency versions and explicit random seeds. The `spec.md` is the single source of truth; no new constraints are invented in the plan.
- **Principle II (No Silent Fallbacks)**: If the 30B model weights are missing or memory is exceeded, the pipeline **must not** silently switch to a dummy generator or smaller model for the purpose of "validating reasoning." Instead, it must log a `MISSING_WEIGHTS` warning, skip the inference step for that dataset, and flag the result as "Pipeline Validated, Performance Claim Unverifiable" in the report.
- **Principle V (Real-Call Testing)**: The plan distinguishes between "Pipeline Logic Validation" (code runs) and "Real-Call Testing" (model reasoning). The current scope is limited to Pipeline Logic Validation due to resource constraints. Any attempt to infer performance from a 1B model or dummy generator is explicitly disallowed.

## Project Structure

### Documentation (this feature)

```text
specs/581-reproduce-su01-olympiad/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── generated_solution.schema.yaml
    ├── output.schema.yaml
    └── aggregated_report.schema.yaml
```

### Source Code (repository root)

```text
external/
└── SU-01/               # Git submodule (contains su01-eval, su01-train-slime)

scripts/
├── setup_env.sh         # Installs CPU-only deps
├── run_subset_eval.sh   # Executes inference on 2-5 problems
└── generate_report.sh   # Aggregates logs and creates reproduction_report.md

tests/
├── test_imports.py      # Verifies no CUDA imports
└── test_pipeline.py     # Verifies end-to-end flow on dummy data (logic only)

output/
├── artifacts/           # Generated .txt, .jsonl
├── logs/                # Execution logs
└── results.json         # Aggregated metrics
```

**Structure Decision**: Single project structure with a dedicated `external/` directory for the vendored submodule. This isolates the third-party code while allowing the main project to manage the execution environment and validation logic.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Explicit "Unverifiable" Verdict Logic | The 30B weights are likely missing; a hard fail or dummy fallback would mislead the scientific conclusion. | A simple "run or die" approach would prevent pipeline validation. A "dummy fallback" for performance claims would be scientifically invalid. |
| CPU-Only Dependency Pinning | Default `torch` installs CUDA variants, causing import errors on CI. | Using generic `pip install torch` would result in CI failure; explicit CPU-only pins are required for feasibility. |
| Strict Dataset Matching | Substituting datasets (e.g., USAMO 2025 for 2026) invalidates the comparison to the paper's results. | Using a proxy dataset would create a construct validity threat, making the validation meaningless. |

## Success Criteria (Revised)

- **SC-001**: The success rate of the pipeline (number of successfully executed scripts / total scripts) is measured against the requirement that all core scripts (submodule init, install, logic check) complete without error. (See FR-001, FR-002)
- **SC-002**: The presence of at least one valid artifact (e.g., `results.json` or a figure) is measured against the requirement for "real artifacts" to verify pipeline logic. (See FR-005)
- **SC-003**: The `reproduction_report.md` must contain a "Verdict" field with a value of **"Pipeline Validated"**, **"Pipeline Validated, Performance Claim Unverifiable"**, or **"Failed"**. A verdict of "Reproduced" is **only** possible if the 30B model runs and the sample size is sufficient (which is not the case here). (See FR-005, US-3)
- **SC-004**: The execution time of the inference step (for the subset) is measured against the **30-minute hard constraint** (FR-007).
- **SC-005**: The absence of CUDA/GPU errors in the logs is measured against the requirement for CPU-only compatibility. (See FR-002)
- **SC-006**: If model weights are missing, the report must explicitly state "Performance Claim Unverifiable" rather than attempting to validate with a smaller model. (See Principle II)