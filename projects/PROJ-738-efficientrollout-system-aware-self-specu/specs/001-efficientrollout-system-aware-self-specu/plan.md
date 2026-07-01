# Implementation Plan: EfficientRollout: System-Aware Self-Speculative Decoding for RL Rollouts

**Branch**: `001-efficientrollout-validation` | **Date**: 2024-05-21 | **Spec**: `specs/001-efficientrollout-validation/spec.md`
**Input**: Feature specification from `specs/001-efficientrollout-validation/spec.md`

## Summary

This feature implements a CPU-feasible validation of the "EfficientRollout" paper (arXiv:2606.18967). The primary requirement is to reproduce the system-aware self-speculative decoding (SD) mechanism on a GitHub Actions free-tier runner (limited CPU, constrained RAM) without GPU dependencies. The technical approach involves:
1.  **Quantization Adaptation**: Using CPU-native `torch.ao.quantization` (dynamic) as the primary method, with `optimum`/GGUF as a fallback, to generate a "Quantized Drafter" from the target model (e.g., Llama-3.1-8B-Instruct) as required by FR-001.
2.  **System-Aware Toggle**: Implementing the `sd_toggle` logic that monitors batch size and memory pressure to dynamically enable/disable speculation, adhering to FR-004.
3.  **Dual-Mode Validation**:
    *   **Mode A (Feasibility & Logic)**: Run SD vs. AR on the 8B quantized model to validate the *toggle logic* (does it disable speculation when memory-bound?) and *feasibility* (does it run without OOM?).
    *   **Mode B (Algorithmic Speedup)**: Run SD vs. AR on a *small, full-precision* model (e.g., TinyLlama-1.1B) to provide a scientifically valid baseline where SD is expected to be faster, validating the *algorithmic efficacy* of the method.
4.  **Constraint Enforcement**: Strictly limiting batch sizes and dataset subsets to ensure the process completes within 6 hours and 7GB RAM (FR-002, SC-002, SC-004).
5.  **Statistical Rigor**: Mandating N=30 data points (10 prompts x 3 trials) to calculate Coefficient of Variation (CV) and establish consistency, acknowledging the study is descriptive, not inferential.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU build), `transformers`, `accelerate`, `datasets` (for data loading), `pandas`, `matplotlib` (for plotting).  
**Storage**: Local filesystem (temporary artifacts for quantized models and JSON logs).  
**Testing**: `pytest` (unit tests for toggle logic, integration tests for end-to-end latency).  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Research/Validation CLI tool.  
**Performance Goals**: Complete 10-prompt subset validation (3 trials each) within 15 minutes; total CI job < 6 hours.  
**Constraints**: NO CUDA; NO `bitsandbytes`; NO GPU; Max RAM sufficient for the experimental workload.; Max Disk: Sufficient capacity to accommodate the planned dataset and computational artifacts..  
**Scale/Scope**: 
*   Primary: Llama-Instruct (Quantized) for Logic/Feasibility.
*   Secondary: TinyLlama-Chat-v1.0 (Full Precision) for Speedup Validation.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on constitution file*

1.  **Feasibility**: The plan explicitly avoids GPU-only libraries (`bitsandbytes`, `load_in_8bit`) and substitutes them with CPU-native quantization methods (`torch.ao.quantization` as primary, `optimum` as fallback) to satisfy the "Compute Feasibility" constraint.
2.  **Scope Adherence**: The plan strictly adheres to the "10-prompt subset" defined in US-2 to prevent CI timeout, deferring full-scale statistical power to the research phase.
3.  **Data Integrity**: The plan explicitly designates `prompts.jsonl` (local file) as the Single Source of Truth (SSoT) for this validation run. If this file is missing, the system MUST fail fast with a clear error, preventing silent fallback to an unverified source.
4.  **Metric Validity**: SC-003 explicitly allows for "negative speedup" or "insignificant" results on CPU, aligning with the assumption that the paper's [deferred] reduction is A100-specific. The metric is redefined to measure "directionality consistency" across trials.

## Project Structure

### Documentation (this feature)

```text
specs/001-efficientrollout-validation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── rollout.schema.yaml
    └── config.schema.yaml
```

### Source Code (repository root)

```text
src/
├── models/
│   └── drafter.py         # Wrapper for the quantized drafter
├── services/
│   ├── sd_toggle.py       # System-aware toggle logic
│   └── latency_tracker.py # Timing and acceptance rate logging
├── cli/
│   ├── quantize.py        # CPU-compatible quantization logic
│   ├── main.py            # Entry point for validation
│   ├── run_baseline.py    # Baseline AR execution
│   └── run_sd.py          # Speculative SD execution
├── data/
│   └── loaders.py         # Dataset loading and subset filtering
└── utils/
    └── memory_monitor.py  # RAM pressure detection

tests/
├── contract/
│   └── test_schemas.py    # Validate JSON outputs against contracts
├── integration/
│   └── test_end_to_end.py # Run 10-prompt subset and check latency
└── unit/
    ├── test_sd_toggle.py  # Test toggle logic
    └── test_quantizer.py  # Test CPU quantization

contracts/
└── (schema files generated by plan)
```

**Structure Decision**: Single project structure selected. The feature is a research validation tool, not a web service or mobile app. The `src/` directory isolates logic from the `tests/` and `contracts/`. The `cli/` directory provides the entry points for the Baseline and EfficientRollout runs.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Dual-Model Strategy | A single 8B quantized comparison is tautological for speedup claims; a small full-precision model is needed to validate the algorithm's efficacy. | Using only the 8B model would fail to scientifically validate the "speedup" claim against a degraded baseline. |
| Dynamic Batch Size Capping | GB RAM is insufficient for standard batch sizes with an 8B model. | Fixed batch size would cause OOM kills on the CI runner, blocking the entire pipeline. |
| 3 Trials per Prompt | N=1 is insufficient to distinguish signal from system jitter. | A single run cannot validate the mechanism's consistency; 3 trials provide a minimal variance estimate. |

## Statistical & Methodological Rigor

### 1. Sample Size & Power
-   **Constraint**: N=10 prompts, 3 trials each (Total N=30 data points).
-   **Limitation**: This sample size is **insufficient** for statistical inference (e.g., t-tests) to claim "speedup > 0" with high confidence.
-   **Validation Goal**: The study is **descriptive**, not inferential. It validates:
    1.  The *mechanism* of the toggle (does it log decisions?).
    2.  The *directionality* of the result (is SD faster or slower?).
    3.  The *consistency* of the result (does it hold across 30 data points?).
-   **Metric**: Coefficient of Variation (CV) of latency will be calculated to quantify system jitter. Success is defined as "Directionality Consistency" (e.g., SD is slower in 29/30 cases) rather than statistical significance.

### 2. Confounding Factors
-   **CPU Cache Thrashing**: Speculative decoding on CPU often suffers from cache misses during the verification step.
-   **Quantization Overhead**: The quantized model itself is slower than FP16.
-   **Control**: 
    *   **Primary (8B)**: Baseline uses the **same quantized model** running in Autoregressive (AR) mode. This isolates the *algorithmic* overhead of SD (draft + verify) from the *quantization* overhead.
    *   **Secondary (TinyLlama)**: Baseline uses a **full-precision** small model. This provides a scientifically valid baseline where SD is expected to be faster, validating the *algorithmic efficacy* of the method.

### 3. Memory Profile of Quantization
-   **Risk**: Static quantization of an 8B model may require >7GB RAM during the calibration step.
-   **Mitigation**: Use **dynamic quantization** (`torch.ao.quantization.quantize_dynamic`) which does not require a calibration dataset or full model load in FP32.
-   **Loading**: Use `device_map="auto"` or streaming loading to ensure the 8B model fits in 7GB RAM.
-   **Fail-Safe**: If the quantization process exceeds available system memory, the system must fail fast with a clear error message..

## Data Integrity & SSoT

-   **Single Source of Truth**: `prompts.jsonl` (local file in project root).
-   **Fallback Policy**: **NO** fallback to external URLs. If `prompts.jsonl` is missing, the system MUST exit with `ERROR: Source of Truth 'prompts.jsonl' not found`.
-   **Rationale**: The "Verified datasets" block did not contain a URL for `SimpleRL-Zoo`. Relying on a local file ensures reproducibility and prevents silent fallback to unverified data.

## Success Criteria (Revised)

-   **SC-001**: CPU-only quantization success rate is measured against the requirement that no CUDA errors occur during model loading (See FR-001, US-1).
-   **SC-002**: Total execution time for a prompt subset (3 trials) is measured against the 6-hour CI limit to ensure the workflow is feasible on free-tier hardware (See FR-002, US-2).
-   **SC-003**: **Directionality Consistency**: The ratio of EfficientRollout latency to Baseline latency is measured across 30 data points. The result is valid if the direction (faster/slower) is consistent across trials, even if the magnitude differs from the paper's [deferred] claim.
-   **SC-004**: Memory usage peak is measured against the available RAM limit. to verify the batch-size capping logic prevents OOM failures (See FR-002, US-2).
-   **SC-005**: **Toggle Logic Validation**: The system must successfully log a "Synthetic Enable" decision when the draft cost is artificially inflated, proving the toggle mechanism functions correctly.
-   **SC-006**: **Algorithmic Efficacy**: The Small-Model Proxy (TinyLlama) must demonstrate a positive speedup (SD < AR) to validate that the algorithm *can* work on CPU under favorable conditions.

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Quantization OOM | High (Pipeline fails) | Use dynamic quantization; stream model loading; fail-fast if >6GB. |
| Negative Speedup | Medium (Result is "failed" vs paper) | Expected on 8B; focus on mechanism validation. Use Small-Model Proxy for positive validation. |
| Toggle Always Disabled | Medium (Logic untested) | Implement "Synthetic Regime" test and "Small-Model Proxy" to prove toggle *can* enable. |
| Local Data Missing | High (Pipeline fails) | Fail-fast error; no silent fallback. |

## Computation Feasibility

-   **Model**: 
    *   Primary: Llama-3.1-8B (Quantized to INT8 via `torch.ao`).
    *   Secondary: TinyLlama-1.1B (Full Precision).
-   **RAM**: 
    *   8B Quantized: ~5-6GB peak (fits within 7GB).
    *   TinyLlama: ~GB peak (fits comfortably).
-   **Disk**: ~6GB model + <1GB logs (fits within 14GB).
-   **Time**: ~-15 mins per trial (10 prompts) -> [deferred] total (3 trials). Well within 6h limit.