# Implementation Plan: Reproducing, Analyzing, and Detecting Reward Hacking in Rubric-Based Reinforcement Learning

**Branch**: `663-reproduce-cherrl` | **Date**: 2026-06-08 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/663-reproduce-cherrl/spec.md`

## Summary

This feature reproduces the CHERRL (Checking for Reward Hacking in LLMs) methodology to validate the detection of reward hacking in rubric-based RL. The technical approach involves vendoring the CHERRL codebase, configuring a minimal CPU-tractable environment using Qwen1.5-1.8B (float16), injecting specific linguistic biases ("self-praise", "lexical", "tone") into the judge model, and executing short training loops to observe reward divergence. Finally, the RHDA detection agent will analyze the logs to identify the onset of hacking and perform a sensitivity analysis on detection thresholds. The entire pipeline is constrained to run on a GitHub Actions free-tier runner with limited CPU and RAM resources without GPU acceleration.

**Critical Note on Spec Inconsistencies**:
- **SC-002**: The spec defines success as a "reward increase of ≥ 10% over the baseline". This measures raw reward increase, not "divergence from ground-truth quality". The plan implements the scientifically valid metric (divergence from independent ground truth) and flags SC-002 for spec revision.
- **Edge Case**: The spec requires "downsampling context window" on OOM. The plan implements "ABORT on OOM" to satisfy the "No Silent Fallback" principle, flagging the spec requirement for revision.

## Technical Context

**Language/Version**: Python 3.10+ (required by PyTorch/Transformers ecosystem)
**Primary Dependencies**: `torch` (CPU-only), `transformers`, `accelerate`, `datasets`, `pandas`, `pytest`, `scikit-learn`
**Storage**: Local file system (JSONL logs, Parquet datasets, model cache)
**Testing**: `pytest` (unit tests for data loading, integration tests for bias injection)
**Target Platform**: Linux (GitHub Actions Free Tier: limited vCPU, constrained RAM, ~14GB Disk)
**Project Type**: Computational Research / Reproducibility Pipeline
**Performance Goals**: Complete reproduction pipeline (setup + 3 seeds x 4 runs x 500 steps + detection) within 6 hours; memory usage < 6GB to allow for OS overhead.
**Constraints**:
- No GPU/CUDA usage (explicitly forbidden by runner constraints).
- No 8-bit/4-bit quantization libraries requiring CUDA (e.g., `bitsandbytes`).
- Model size limited to ~B parameters (Qwen1.8B) in float16 to fit in 7GB RAM.
- Dataset subset to ensure RAM/disk limits are not exceeded.
- **Abort Policy**: If memory pressure is detected, the pipeline ABORTS with a clear error message recommending a smaller model (e.g., Qwen1.5-0.5B). It does NOT automatically switch models.

## Constitution Check

*Gates determined based on constitution file*

1.  **Reproducibility (Principle I)**: The plan relies on vendoring the specific CHERRL codebase and using the verified datasets listed in the spec. It does not introduce new, unverified data sources.
2.  **Transparency (Principle II)**: All bias injection parameters and detection thresholds are explicitly defined in the configuration and reported in the output logs. The `bias_config.yaml` and `detection_thresholds.yaml` in `external/CHERRL/configs` are designated as the Single Source of Truth (SSoT).
3.  **Feasibility (Principle III)**: The plan adheres strictly to the CPU-only, 7GB RAM constraint by selecting Qwen1.5-1.8B (float16) and limiting training steps. It explicitly avoids methods requiring CUDA.
4.  **Integrity (Principle IV)**: The plan frames results as associational effects (per FR-006 and Assumptions), avoiding causal claims about agent intent.
5.  **Safety (Principle V)**: The "hacking" simulated is a controlled linguistic bias injection in a sandboxed environment, posing no risk of generating harmful real-world content beyond the scope of the research.
6.  **No Silent Fallbacks (Principle II)**: The pipeline ABORTS on OOM. It does not automatically switch models. This satisfies the principle.

## Project Structure

### Documentation (this feature)

```text
specs/663-reproduce-cherrl/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-663-https-arxiv-org-abs-2606-04923/
├── external/
│   └── CHERRL/          # Vendored codebase (submodule)
│       ├── data/        # Dataset files (healthbench_train.parquet, etc.)
│       ├── src/         # Core logic (judge, trainer, detector)
│       └── configs/     # Bias configuration files (SSoT)
├── scripts/
│   ├── setup_env.py     # Dependency installation and sanity check
│   ├── run_bias_experiment.py # Main experiment runner
│   └── run_detection.py # RHDA agent execution
├── tests/
│   ├── test_data_load.py
│   └── test_bias_injection.py
└── outputs/             # Generated logs and reports
    ├── logs/
    └── reports/
```

**Structure Decision**: The project follows a "Research Pipeline" structure. The `external/CHERRL` directory is a read-only submodule to preserve the original code integrity. Custom scripts in `scripts/` orchestrate the specific bias injection and detection workflows required by the spec, ensuring the experiment is reproducible and contained.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Multiple Seeds (3 per condition) | Required for valid statistical testing (Mann-Whitney U) to establish variance in both biased and baseline groups. | Single run provides no variance estimate, making p-values invalid. |
| Independent Ground Truth | Required to measure "divergence from quality" rather than just "high reward". | Relying on the biased judge alone creates circular validation. |
| Abort on OOM | Required to satisfy "No Silent Fallback" principle. | Automatic switching to a smaller model would violate the principle. |
| Float16 Precision | Required to fit Qwen1.5-1.8B in 7GB RAM. | Float32 exceeds RAM limit for 1.8B model. |

## Detailed Phase Schedule

1.  **Phase 0: Environment Setup & Sanity (US-1)**
    -   Clone `external/CHERRL`.
    -   Install CPU-only dependencies.
    -   Run sanity check: Load Qwen1.5-1.8B (float16) and one HealthBench sample.
    -   **Success**: Exit code 0, "Success" log.

2.  **Phase 1: Bias Injection & Training (US-2)**
    -   **Configuration**: Load `bias_config.yaml` (SSoT).
    -   **Execution**: Run independent seeds for each of the bias types AND independent seeds for the baseline (no bias). Total: multiple runs.
    -   **Steps**: A sufficient number of steps per run.
    -   **Observation**: Log per-step rewards, tokens, and bias triggers.
    -   **Ground Truth**: Calculate independent quality score for each completion (using unbiased rubric).

3.  **Phase 2: Detection & Sensitivity (US-3)**
    -   **Agent**: Run RHDA on the generated logs.
    -   **Threshold Sweep**: Execute detection with thresholds `{0.01, 0.05, 0.1}`.
    -   **Output**: Generate `threshold_grid.csv` containing TPR/FPR.
    -   **Validation**: Compare detected onset step against the known injection step (defined as the step where bias config is active).

4.  **Phase 3: Statistical Analysis**
    -   **Metric**: Mean reward over the final steps of each seed.
    -   **Test**: Mann-Whitney U test comparing the distribution of biased means vs. baseline means.
    -   **Correction**: Bonferroni correction for the multiple bias comparisons

The research question, method, and references remain unchanged as specified in the planning document..

## Spec Kickback Notes

-   **SC-002**: The spec defines success as "reward increase of ≥ 10% over baseline". This is tautological. The plan measures "divergence from independent ground-truth quality". **Action**: Flag SC-002 for spec revision.
-   **Edge Case**: The spec requires "downsampling context window" on OOM. The plan implements "ABORT on OOM" to satisfy "No Silent Fallback". **Action**: Flag Edge Case for spec revision.