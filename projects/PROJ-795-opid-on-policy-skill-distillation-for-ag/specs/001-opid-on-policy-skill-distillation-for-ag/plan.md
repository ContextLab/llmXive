# Implementation Plan: OPID: On-Policy Skill Distillation for Agentic Reinforcement Learning

**Branch**: `795-opid-reproduction` | **Date**: 2024-06-15 | **Spec**: [link]
**Input**: Feature specification from `/specs/795-opid-reproduction/spec.md`

## Summary

This plan implements the reproduction and validation of the OPID (On-Policy Skill Distillation) algorithm for Agentic Reinforcement Learning on CPU-only CI infrastructure. The primary requirement is to execute the vendored `external/OPID` codebase within the strict constraints of a GitHub Actions free-tier runner (limited CPU, ~7 GB RAM, no GPU) while validating the dual-advantage learning mechanism (outcome + skill distillation). 

**Critical Methodological Shift**: To strictly adhere to on-policy RL assumptions and address memory constraints, the previously proposed "RingBuffer" strategy has been replaced with a **Strict On-Policy Generator**. This generator discards trajectories immediately after the gradient update step, ensuring no stale data from previous policies biases the gradient estimates. Memory safety is maintained by limiting the batch size and episode count per step, not by buffering.

The technical approach involves stripping GPU dependencies, implementing a trajectory sampling strategy to prevent OOM via batch size limits, and configuring a small-scale evaluation subset to verify performance trends against an outcome-only baseline within the 6-hour time limit.

## Technical Context

**Language/Version**: Python 3.10+ (Required by `transformers` and `gym` ecosystem)  
**Primary Dependencies**: `torch` (CPU-only), `transformers`, `gym`, `alfworld`, `pandas`, `numpy`, `pyyaml`  
**Storage**: Local filesystem (temporary trajectory buffers, checkpoints in `output/`)  
**Testing**: `pytest` (Unit), `GitHub Actions` (Integration/Smoke)  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 vCPU, 7GB RAM)  
**Project Type**: Research Reproduction / CLI Tool  
**Performance Goals**: Complete 100 optimization steps in < 6 hours; Memory usage < 6GB (safety margin)  
**Constraints**: No CUDA/CUDA-related imports; No large model loading (>7GB); No network calls to unverified sources; **Strict on-policy data lifecycle (no buffering)**.  
**Scale/Scope**: 5 ALFWorld task instances; 100 training steps; ~1000 trajectory steps total.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on constitution file:*

1.  **Reproducibility & Transparency** [Const-Prin-I]: The plan explicitly mandates using the vendored code and verified dataset URLs, avoiding hallucinated sources. *Implementation*: Phase 1 (Setup) uses only `external/OPID` and verified HuggingFace URLs.
2.  **Compute Feasibility** [Const-Prin-II]: The plan strictly enforces CPU-only execution, memory capping, and time limits to ensure the CI job does not fail. *Implementation*: Phase 2 (Training) enforces `torch.cpu` and batch size limits.
3.  **Scientific Rigor** [Const-Prin-III]: The plan includes a specific validation step for the "critical-first routing" fallback and the dual-advantage variance, ensuring the algorithm is actually learning. *Implementation*: Phase 4 (Validation) includes ablation studies.
4.  **Safety & Robustness** [Const-Prin-IV]: Edge cases (OOM, timeouts, routing failures) are explicitly addressed with fallback mechanisms (sampling, default rewards, episode-level skills). *Implementation*: The research phase includes timeout handlers and fallback logic.
5.  **Traceability** [Const-Prin-V]: Every Functional Requirement (FR-NNN) and Success Criterion (SC-NNN) from the spec is mapped to a specific plan phase. *Implementation*: See "Phase Mapping" below.

## Project Structure

### Documentation (this feature)

```text
specs/795-opid-reproduction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
external/
└── OPID/                # Vendored source code (assumed present)

src/
├── opid/
│   ├── __init__.py
│   ├── config.py        # CPU-only configuration overrides
│   ├── training.py      # Main training loop with Strict On-Policy Generator
│   ├── evaluation.py    # Small-scale evaluation script
│   └── utils.py         # Trajectory sampling and logging helpers

tests/
├── contract/
│   └── test_schema_validation.py
├── integration/
│   └── test_cpu_smoke.py
└── unit/
    └── test_routing_logic.py

output/                  # Generated artifacts (logs, checkpoints)
```

**Structure Decision**: A modular `src/opid` structure is selected to wrap the vendored `external/OPID` logic. This allows us to inject CPU-specific configuration overrides and OOM protection logic without modifying the vendored source directly, preserving the integrity of the original reproduction code while adapting it to the CI constraints.

## Implementation Phases

### Phase 1: Environment Setup & CPU Hardening
- **Goal**: Ensure the environment runs on CPU without errors.
- **Steps**:
  1. Install `torch` from CPU-only wheel index.
  2. Patch `external/OPID` imports to force `device="cpu"`.
  3. Verify ALFWorld environment initialization.
- **Validation**: Run `src/opid/quickstart.py` with `--cpu-only`.
- **Mapped Requirements**: FR-001, SC-004.

### Phase 2: Strict On-Policy Training Loop
- **Goal**: Execute a sufficient number of optimization steps without OOM or on-policy violations.
- **Steps**:
  1. Implement `StrictOnPolicyGenerator`: Collects trajectories, computes gradients, updates policy, and **immediately discards** trajectories.
  2. Implement `CriticalFirstRouting`: Assigns skill types with episode-level fallback.
  3. Implement `DualAdvantageCalculator`: Computes outcome and distillation advantages.
  4. Monitor memory usage; abort if >6GB.
- **Validation**: Logs show valid loss and `skill_type` distribution.
- **Mapped Requirements**: FR-002, FR-003, FR-004, SC-001, SC-005.

### Phase 3: Evaluation & Baseline Comparison
- **Goal**: Run evaluation on 5 tasks and compare against baseline.
- **Steps**:
  1. Run OPID agent on multiple ALFWorld tasks.
  2. Run "Outcome-Only" baseline (distillation weight=0) on same 5 tasks.
  3. Record success rates and skill distributions.
- **Validation**: Success rates logged; no crashes.
- **Mapped Requirements**: FR-005, SC-003.

### Phase 4: Contract Validation & Artifact Integrity
- **Goal**: Validate generated artifacts against schemas.
- **Steps**:
  1. Run `tests/contract/test_schema_validation.py` against `output/trajectory_logs.json` and `output/opid_metrics.csv`.
  2. Verify `log_prob_shift` variance > 0.
  3. Correlate `distillation_advantage` with success rate.
- **Validation**: All schema checks pass; correlations computed.
- **Mapped Requirements**: SC-002, SC-003 (methodology refinement).

## Validation Procedure (Operational Steps)

To explicitly measure Success Criteria SC-003 and SC-005:

1.  **SC-003 (Baseline Comparison)**:
    - Execute `python src/opid/evaluation.py --mode baseline --tasks 5`.
    - Execute `python src/opid/evaluation.py --mode opid --tasks 5`.
    - Calculate `diff = abs(opid_success_rate - baseline_success_rate)`.
    - **Pass Condition**: `diff <= 0.10` (Sanity check for non-degenerate behavior).
    - **Note**: This is a feasibility check, not a statistical power test.

2.  **SC-005 (Routing Fallback)**:
    - Parse `output/trajectory_logs.json`.
    - Count `skill_type == "episode"` vs `skill_type == "step"`.
    - Calculate `fallback_ratio = count(episode) / total_steps`.
    - **Pass Condition**: `fallback_ratio >= 0.10`.

3.  **SC-002 (Distillation Signal)**:
    - Calculate variance of `log_prob_shift` in `trajectory_logs.json`.
    - **Pass Condition**: `variance > 0`.
    - **Ablation**: Run with `--distillation-weight 0` and verify variance drops significantly or changes pattern.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Strict On-Policy Generator | RingBuffer violates on-policy assumptions (data must be from current policy). | Buffering old data biases gradients; immediate discarding is the only valid on-policy approach. |
| CPU-Only Torch | GitHub Actions free tier has no GPU. | GPU wheels fail on CPU runners; CPU wheels are mandatory. |
| Small-Scale Eval (5 tasks) | Full ALFWorld eval is too slow for h CI. | A subset is sufficient for a "smoke test" of non-degenerate behavior, though insufficient for publication-grade claims. |
| Ablation Study | Non-zero variance alone doesn't prove efficacy. | Must compare against a zero-distillation baseline to isolate the signal's contribution. |