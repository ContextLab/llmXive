# Implementation Plan: Reproduce & Validate SpatialBench

**Branch**: `634-reproduce-spatialbench` | **Date**: 2024-05-21 | **Spec**: `specs/634-reproduce-spatialbench/spec.md`
**Input**: Feature specification from `/specs/634-reproduce-spatialbench/spec.md`

## Summary

This feature implements a reproducible, CPU‑only execution pipeline for the `SpatialBench` benchmark, vendored at `external/SpatialBench`. The primary requirement is to validate end‑to‑end execution on GitHub Actions free‑tier hardware (CPU‑only, <7 GB RAM) while validating the core quantitative metrics (Abs Rel, δ₁, δ₂) against the paper’s reported baselines within a 5 % relative tolerance **OR** verifying internal consistency if baselines are unavailable. The plan distinguishes between **logic‑validation** (subset execution) and **full‑scale statistical reproduction** (out‑of‑scope for CI).

## Technical Context

- **Language/Version**: Python 3.10+ (compatible with `torch` CPU wheels)  
- **Primary Dependencies**: `torch` (CPU‑only), `numpy`, `pandas`, `matplotlib`, `seaborn`, `scikit-learn`, `pyyaml`, `psutil`.  
- **Storage**: Local filesystem (temporary artifacts), `external/SpatialBench` submodule.  
- **Testing**: `pytest` (contract tests for output schema, integration tests for execution flow).  
- **Target Platform**: Linux (GitHub Actions free‑tier runner: 2 vCPU, ~7 GB RAM, ~14 GB disk, ≤6 h per job).  
- **Constraints**: No GPU/CUDA; no 8‑bit/4‑bit quantization; float32 precision only; strict memory monitoring (`MAX_RAM_MB = 6144`).  
- **Scale/Scope**: Subset execution (a limited set of scenes, 2 domains, 3 models) vs. full 546‑scene paper scope.

> **Dataset Variable Fit Note**: The spec references DTU and ScanNet. The provided "Verified datasets" block does **not** contain these 3‑D scene datasets. This plan **mandates** that `external/SpatialBench` ships its own data‑loader scripts for DTU and ScanNet. If those loaders are absent, the pipeline aborts with a clear error (see Phase 0).

## Constitution Check

The project currently has an empty `constitution.md`. We therefore assert compliance with the **default research‑integrity principles** (FR-030):

1.  **Principle I (SSoT)**: The plan explicitly verifies that data loaders exist in the submodule before proceeding, preventing silent fallback to generic links.
2.  **Principle II (No Silent Fallbacks)**: Missing data or mismatched checksums trigger an immediate `EXIT_CODE_DATA_MISSING` abort, ensuring no invalid data is processed.
3.  **Principle III (Reproducibility)**: The plan enforces a deterministic, CPU‑only run and records all artefacts (results, memory logs).
4.  **Principle IV (Resource Honesty)**: Explicitly forbids GPU/CUDA usage and enforces the `MAX_RAM_MB` limit via a watchdog.
5.  **Principle V (Transparency)**: All limitations (subset size, tolerance justification, fallback to internal consistency) are documented in `research.md`.

## Project Structure

### Documentation (this feature)

```text
specs/634-reproduce-spatialbench/
├── plan.md                # This file
├── research.md            # Phase 0 output
├── data-model.md          # Phase 1 output
├── quickstart.md          # Phase 1 output
├── contracts/             # Phase 1 output
│   ├── benchmark_results.schema.yaml
│   └── memory_log.schema.yaml
└── tasks.md               # Phase 2 output
```

### Source Code (repository root)

```text
external/
└── SpatialBench/          # Vendored benchmark code (submodule)

src/
└── spatialbench_runner/
    ├── __init__.py
    ├── config.py          # CPU‑only config, subset limits
    ├── runner.py          # Execution logic with memory monitoring
    ├── metrics.py         # Validation logic (Abs Rel, δ₁, δ₂)
    └── visualizer.py      # Artifact generation (PNG, HTML)

tests/
├── contract/
│   ├── test_results_schema.py
│   └── test_memory_log_schema.py
├── integration/
│   └── test_cpu_execution.py
└── unit/
    └── test_metrics.py
```

**Structure Decision**: A thin wrapper (`src/spatialbench_runner`) enforces CPU constraints and memory monitoring without modifying upstream code, satisfying FR‑001 and FR‑005.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Memory Monitoring Wrapper | Upstream code may exceed 7 GB RAM; OOM kills CI. | Direct execution risks silent CI failure; explicit monitoring is required for FR‑001 and SC‑001. |
| Subset Configuration | Full 546 scenes exceed CI limits. | Running full dataset is impossible on free‑tier; subset is the only viable validation path. |
| Stratified Sampling | Random 5 scenes could hide logic errors. | Cherry‑picked validation is scientifically unsound; stratified sampling ensures representativeness. |

## Implementation Phases

### Phase 0: Research & Feasibility
- **Goal**: Confirm dataset availability, baseline source, and CPU feasibility.
- **Steps**:
  1.  **Data Loader Verification**: Search `external/SpatialBench` for `load_dtu.py` and `load_scannet.py`. **Fail‑fast**: abort with `EXIT_CODE_DATA_MISSING` if absent. Provide official DTU/ScanNet download URLs as a manual fallback in the error message.
  2.  **Data Provenance Check**: Compute SHA‑256 hashes of the downloaded DTU and ScanNet archives and compare against the paper's documented hashes (found in `external/SpatialBench/metadata/` or the paper's supplement). **Abort** if mismatched to ensure construct validity.
  3.  **Baseline Source Check**: Look for per‑scene baseline metric files (`reference_results/*.json`).
      - **If present**: Proceed to **External Baseline Validation** (compare against paper values with ≤5% tolerance).
      - **If absent**: Proceed to **Internal Consistency Validation** (compare run-to-run stability with ≤0.1% variance). Flag this as a limitation for SC-004.
  4.  **Numerical Drift Estimation**: Cite literature that CPU‑FP32 vs. GPU‑FP16 drift is typically <0.5% for depth estimation. Adopt a conservative 5% relative tolerance for external baselines to cover drift plus implementation variance.
  5.  **Stratified Sampling Design**: Choose 5 scenes covering:
      - Two DTU scenes (low, medium depth range)
      - Two ScanNet scenes (indoor, outdoor)
      - One mixed‑density scene (high sparsity)
      This ensures representation of depth ranges and density settings.
  6.  **Dry‑Run on CPU**: Import `external/SpatialBench` with `torch.set_default_device('cpu')` and confirm no CUDA imports raise errors.
  7.  **Output**: `research.md` with dataset strategy, feasibility report, and baseline justification.

### Phase 1: Data Model & Contracts
- **Goal**: Define output schemas and data structures.
- **Steps**:
  1.  Define `BenchmarkResults` schema (JSON) and `MemoryLog` schema (JSON) – see `contracts/`. (FR‑002, SC‑002).
  2.  Add constant definition `MAX_RAM_MB = 6144` in `data-model.md`.
  3.  Document that `delta3` is optional (not listed under `required` in the schema).
  4.  Ensure schema constraints reflect SC‑002 (at least 3 models, 2 domains).

### Phase 2: Quickstart & Execution Logic
- **Goal**: Provide run instructions and core logic.
- **Steps**:
  1.  Draft `quickstart.md` (unchanged) with CPU‑only install commands.
  2.  Implement `runner.py` with:
      - `torch.set_default_device('cpu')`
      - **Memory monitoring loop** using `psutil`; abort if `ram_mb > MAX_RAM_MB`.
      - Sequential scene processing; `gc.collect()` after each scene.
  3.  Implement `metrics.py` to calculate Abs Rel, δ₁, δ₂.
      - If baselines exist: Compare against paper values (≤5% tolerance).
      - If baselines missing: Compare against previous run (≤0.1% stability).
  4.  Implement `visualizer.py` to generate `overview.png`, `memory_curve.png`, and an HTML report (FR‑004, SC‑003).
  5.  **Timing Guard**: Enforce a wall‑clock limit of 60 min for the subset run; abort with `EXIT_CODE_TIMEOUT` if exceeded.

### Phase 3: Validation & Reporting
- **Goal**: Verify correctness and generate final artefacts.
- **Steps**:
  1.  Run integration test: execute a set of scenes across multiple models.
  2.  Validate JSON outputs against the contracts.
  3.  Compare metrics to paper baselines (if available) OR verify internal stability.
  4.  Generate visualisations and a human‑readable HTML report.
  5.  Confirm SC‑001 (exit code 0), SC‑002 (metrics for ≥ 3 models across 2 domains), SC‑003 (≥ 2 visualisations), SC‑004 (≤ 5% error OR ≤0.1% stability), SC‑005 (≤ 60 min).

## Statistical & Methodological Rigor

- **Multiple Comparisons**: Not applicable – single benchmark suite.
- **Sample Size**: The stratified subset is **explicitly** a logic‑validation sample, not a statistical population. It is justified as representative of depth and density variations across the two domains.
- **Tolerance Justification**:
  - **External Baseline Validation**: Empirical studies show CPU‑FP32 vs. GPU‑FP16 results differ by <0.5% for depth estimation tasks. Adding a conservative buffer yields a 5% relative tolerance, covering both numerical drift and potential minor implementation discrepancies. This applies **only** if per-scene paper baselines exist.
  - **Internal Consistency Validation**: If paper baselines are missing, the success criterion shifts to **run-to-run stability** (variance <0.1% between two identical runs). This avoids the category error of comparing a single sample to a population mean.
- **Measurement Validity**: Abs Rel, δ₁, δ₂ are standard depth‑estimation metrics; the benchmark’s own code computes them.
- **Causal Inference**: Not applicable.
- **Collinearity**: Not applicable.

## Compute Feasibility Strategy

- **No GPU**: All `torch` operations forced to CPU.
- **Precision**: Float32 only; no 8‑bit/4‑bit quantization.
- **Memory**: `MAX_RAM_MB = 6144` enforced via `psutil`; process aborts before OOM.
- **Disk**: Subset data < 14 GB.
- **Runtime**: Estimated ≤ 45 min on 2 vCPU.