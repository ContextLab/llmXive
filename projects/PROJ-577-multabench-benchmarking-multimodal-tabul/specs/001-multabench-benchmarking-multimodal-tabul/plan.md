# Implementation Plan: MulTaBench: Benchmarking Multimodal Tabular Learning with Text and Image

**Branch**: `577-multabench-reproduction` | **Date**: 2024-05-21 | **Spec**: `specs/577-multabench-reproduction/spec.md`
**Input**: Feature specification from `specs/577-multabench-reproduction/spec.md`

## Summary

This plan outlines the reproduction and validation of the MulTaBench benchmarking pipeline. The primary requirement is to execute the vendored `external/MulTaBench` codebase on a reduced subset of datasets and models to validate the end-to-end logic, ensure CPU-only compatibility, and verify that "tuned" embeddings outperform "frozen" ones as claimed in the paper. The technical approach involves initializing the environment, configuring CPU-only device maps, running a subset benchmark, and validating output metrics against paper claims.

## Technical Context

**Language/Version**: Python + (as required by MulTaBench)  
**Primary Dependencies**: `torch` (CPU-only), `transformers`, `scikit-learn`, `pandas`, `numpy`, `lightgbm`, `tabpfn` (if available), `datasets`  
**Storage**: Local file system for dataset caching and results artifacts (`multabench/leaderboard/data/`)  
**Testing**: `pytest` for unit tests; manual validation of CSV artifacts for integration.  
**Target Platform**: Linux (GitHub Actions free-tier runner: vCPU, limited RAM, no GPU).  
**Project Type**: Research benchmarking pipeline / CLI tool.  
**Performance Goals**: Reduced-scale run must complete within 2 hours; full pipeline (if feasible) within 6 hours.  
**Constraints**: No GPU/CUDA; memory usage < 7GB; no large model training from scratch; only CPU-tractable methods.  
**Scale/Scope**: Reduced subset: Multiple datasets (text, image), Multiple models (frozen vs. tuned).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Constitution Principle I: Single Source of Truth (SSoT)**
- *Requirement*: The `spec.md` is the authoritative source for entity definitions and requirements.
- *Plan Action*: This plan explicitly designates `spec.md` as the Single Source of Truth (SSoT) for all entity definitions (Dataset, Model, Benchmark Run). The `data-model.md` is designated as the SSoT for schema definitions. All plan phases reference `spec.md` for FR/SC definitions.
- *Status*: Pass.

**Constitution Principle II: No Silent Fallbacks**
- *Requirement*: The system must not silently switch behaviors without logging.
- *Plan Action*: Phase 2 implements explicit logging for dataset skips and model fallbacks (FR-004). Any fallback (e.g., TabPFN -> LightGBM) is logged with a warning. **This satisfies Constitution Principle II: No Silent Fallbacks.**
- *Status*: Pass.

**Constitution Principle III: Real-Call Testing**
- *Requirement*: The plan must involve executing actual code against real data.
- *Plan Action*: Phase 3 executes the `benchmark.py` script on real (subset) datasets, not mocks. **This satisfies Constitution Principle III: Real-Call Testing.**
- *Status*: Pass.

**Constitution Principle IV: Explicit Data Contracts**
- *Requirement*: Data schemas must be explicitly defined and validated.
- *Plan Action*: Phase 1 defines `results.schema.yaml` and validates output against it before writing final artifacts. **This satisfies Constitution Principle IV: Explicit Data Contracts.**
- *Status*: Pass.

## Project Structure

### Documentation (this feature)

```text
specs/577-multabench-reproduction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (created later)
```

### Source Code (repository root)

```text
external/MulTaBench/
├── src/
│   ├── multabench/
│   │   ├── datasets/       # Dataset loading and registry
│   │   ├── models/         # Baseline implementations
│   │   ├── benchmark.py    # Main entry point
│   │   └── utils/          # CPU detection, error handling
├── tests/
│   ├── unit/
│   └── integration/
└── results/                # Output artifacts (CSV, logs)
```

**Structure Decision**: The plan relies on the existing structure of the vendored `external/MulTaBench` repository. No new source code structure is created; the implementation will configure and execute the existing pipeline.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Reduced-scale run | Full multi-dataset run exceeds 6h CI limit and RAM. | A full run would fail the resource constraint (SC-003). |
| CPU-only enforcement | MulTaBench may default to CUDA. | GPU is unavailable on free-tier; code must be forced to CPU. |
| Error handling wrapper | Dataset downloads may fail. | A crash would invalidate the entire run; graceful skip is required (FR-004). |
| TabPFN Fallback | TabPFNv may exceed 7GB RAM on CPU. | Without fallback, the run would OOM and produce no data. LightGBM ensures completion. |
| Registry Verification | Dataset IDs may not match registry. | Running with invalid IDs causes silent failures; explicit check prevents this. |

## Execution Phases

### Phase 0: Environment Initialization & Registry Verification
1. Clone `external/MulTaBench`.
2. Install dependencies in a virtual environment.
3. Run `init.sh` or equivalent to verify the dataset registry.
4. **Critical Step**: Explicitly list available datasets via `multabench.datasets.all_datasets`.
5. **Abort Condition**: If the required dataset IDs (`BIN_TEXT_FAKE_JOB_POSTING`, `MUL_IMAGE_CBIS_DDSM`) are not found in the registry, log a fatal error and abort the run. Do not proceed.

### Phase 1: Configuration & Memory Profiling
1. Create a configuration file (`config_subset.yaml`) specifying:
   - Datasets: `BIN_TEXT_FAKE_JOB_POSTING`, `MUL_IMAGE_CIFAR10`.
   - Models: `lgbm`, `tabpfnv2`.
   - Device: `cpu`.
    - Batch size: 1 (initial).
   - Fallback: `lightgbm` (if `tabpfnv2` fails).
2. **Memory Profiling**: Run a dry-run with `batch_size=1` for TabPFNv2.
   - Measure peak RSS memory.
   - If peak RSS > 6GB, skip TabPFNv2 for this dataset immediately.
   - If peak RSS <= 6GB, calculate max batch size using safety factor (a conservative scaling coefficient * (available_memory - current_usage) / peak_per_batch).

### Phase 2: Execution
1. Run `benchmark.py --config config_subset.yaml`.
2. **Flag Verification**: Verify that the `benchmark.py` entry point supports a `--freeze-embeddings` (or equivalent) flag.
   - If the flag exists: Ensure it is passed appropriately for the "frozen" configuration runs.
   - If the flag does **not** exist in the vendored code: Implement a minimal wrapper or configuration override to force the "frozen" state (e.g., setting `requires_grad=False` on backbone weights) before the training loop begins.
3. Monitor for CUDA errors; if detected, force `device='cpu'`.
4. Monitor for memory errors; if detected, trigger fallback to LightGBM.
5. **Verification Step**: Before training, assert `requires_grad` status on backbone weights for the "tuned" configuration to ensure the mechanism is active.

### Phase 3: Validation
1. Check for output files: `results_subset.csv`.
2. Validate metrics: Accuracy/AUC/MSE in [, 1] or plausible range.
3. Perform Directional Consistency Check on the results.
4. Compare tuned vs. frozen metrics.
