# Implementation Plan: Memory Palaces in LLMs: Spatial Reasoning for Enhanced Episodic Recall

**Branch**: `PROJ-596-memory-palaces-in-llms-spatial-reasoning` | **Date**: 2026-06-16 | **Spec**: `specs/PROJ-596-memory-palaces-in-llms-spatial-reasoning/spec.md`
**Input**: Feature specification from `specs/PROJ-596-memory-palaces-in-llms-spatial-reasoning/spec.md`

## Summary

This project implements and evaluates a "Memory Palace" architecture for transformer models, testing the hypothesis that explicit spatial organization of episodic memories improves recall accuracy compared to non-spatial baselines. The implementation involves fine-tuning a low-bit quantized `gpt-medium` model on three sequential memory benchmarks (bAbI task, LAMBADA, Story Cloze) with a custom x spatial memory slot mechanism. The plan addresses the primary research question by measuring exact-match recall, interference distance (via inference-time intervention), and slot occupancy, followed by rigorous statistical analysis (paired t-tests supplemented by permutation tests) across five random seeds.

## Technical Context

**Language/Version**: Python 3  
**Primary Dependencies**: `transformers`, `datasets`, `torch`, `bitsandbytes` (for -bit quantization on CPU), `scipy`, `numpy`, `pandas`, `scikit-learn`  
**Storage**: Local filesystem for model checkpoints and cached datasets (`~/.cache/huggingface`); no external database.  
**Testing**: `pytest` for unit tests (memory management, slot logic); integration tests for model training loops.  
**Target Platform**: GitHub Actions free-tier runner (Ubuntu, CPU cores, ~7 GB RAM, no GPU).  
**Project Type**: Research / Computational Experiment  
**Performance Goals**: Complete 5 seeds × 3 datasets fine-tuning + evaluation within 5 hours; peak RAM < 6.0 GB. These goals are derived directly from **Constitution Principle VI** (Computational Resource Constraints).  
**Constraints**: Must run on CPU; -bit quantization mandatory for model size; dataset streaming required for large subsets; automatic batch size reduction if RAM > 6 GB.  
**Scale/Scope**: Multiple datasets, multiple seeds, Multiple model variants (spatial vs. non-spatial), spatial grid (discretized).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on constitution file; explicit mappings provided below.*

1.  **Reproducibility (Principle I)**: Addressed by **Phase 0.2** (Pin Dependencies, creates `requirements.txt`), **Phase 1.1** (Dataset Fetching with checksums), and **Phase 1.2** (Seed pinning 0-4). The `quickstart.md` will include a single command to reproduce the full run.
2.  **Verified Accuracy (Principle II)**: Addressed by **Phase 1.1** which restricts dataset sources to the "Verified datasets" block. Citations in `research.md` will be validated against primary sources before merging.
3.  **Data Hygiene (Principle III)**: Addressed by **Phase 1.1** (checksumming) and **Phase 2.3** (Per-epoch logging to new artifacts, no in-place modification). PII scan will be run on data files.
4.  **Single Source of Truth (Principle IV)**: Addressed by **Phase 2.3** (logs to `artifacts/metrics/`) and **Phase 3.3** (aggregates to `run_summary.json`). All figures in the final paper will be generated from this JSON.
5.  **Versioning Discipline (Principle V)**: Addressed by **Phase 4.1** (content hashing of artifacts).
6.  **Computational Resource Constraints (Principle VI)**: Addressed by **Phase 1.3** (Dataset Capping Logic), **Phase 2.1** (RAM monitoring & batch size reduction), and the explicit 6GB/5h goals in Technical Context.
7.  **Benchmark Standardization (Principle VII)**: Addressed by **Phase 1.1** (fetching bAbI, LAMBADA, Story Cloze) and **Phase 3.1** (Evaluation on these specific datasets).

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-596-memory-palaces-in-llms-spatial-reasoning/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── epoch_metrics.schema.yaml
│   ├── model_output.schema.yaml
│   ├── results.schema.yaml
│   ├── statistical_analysis.schema.yaml
│   └── training_run.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-596-memory-palaces-in-llms-spatial-reasoning/
├── code/
│   ├── requirements.txt
│   ├── src/
│   │   ├── __init__.py
│   │   ├── memory_palace.py       # Spatial slot logic, grid management
│   │   ├── trainer.py             # Training loop with RAM monitoring & epoch logging
│   │   ├── evaluator.py           # Recall, interference distance metrics
│   │   ├── inference_intervention.py # Intervention wrapper for FR-011
│   │   └── stats.py               # Statistical testing (t-tests, permutation, effect sizes)
│   ├── data/
│   │   ├── download.py            # Dataset fetching and checksumming
│   │   └── __init__.py
│   └── scripts/
│       ├── run_experiment.sh      # Orchestrates the full run
│       └── validate_quickstart.sh # Validates the quickstart output
├── data/                          # Downloaded raw datasets (cached)
├── artifacts/
│   ├── metrics/                   # Per-epoch logs
│   └── results/
│       └── run_summary.json       # Final aggregated results
├── tests/
│   ├── unit/
│   │   ├── test_memory_palace.py  # Slot logic, eviction, interference
│   │   ├── test_oom_recovery.py   # Batch size reduction logic
│   │   ├── test_dataset_mismatch.py # Variable fit checks
│   │   └── test_intervention.py   # Interference injection logic
│   └── integration/
│       └── test_full_pipeline.py
└── state/
    └── projects/PROJ-596-memory-palaces-in-llms-spatial-reasoning.yaml
```

**Structure Decision**: Single project structure with clear separation of `src/` (logic), `data/` (fetching), and `tests/`. This aligns with the reproducibility requirement of running end-to-end on a fresh runner. The `code/` directory contains the `requirements.txt` as mandated by FR-012.

## Phases & Tasks

### Phase 0: Environment & Dependencies
- **0.1**: Initialize virtualenv and install base dependencies.
- **0.2**: **Pin Dependencies**. Run `pip freeze > requirements.txt` to create the mandatory file at `projects/.../code/requirements.txt` (FR-012).
- **0.3**: Verify CPU-only execution environment (no CUDA).

### Phase 1: Data & Configuration
- **1.1**: **Dataset Fetching**. Download bAbI task 3, LAMBADA, Story Cloze (`rocstories`). Compute SHA-256 checksums. Log to `dataset_manifest.json`. **Note**: If `rocstories` is unavailable, the third benchmark is dropped; no proxy is used.
- **1.2**: **Seed Configuration**. Pin random seeds in a `seeds.yaml` config file.
- **1.3**: **Dataset Capping Logic**. Implement the fallback: if RAM > 6GB at batch size 4, the data loader wraps to yield only the first N samples (where N is the [deferred] cap). Log `subsampling_rate` and `cap_reason` in `training_run.schema.yaml` (FR-010).

### Phase 2: Model Implementation & Training
- **2.1**: **RAM Monitoring & Batch Reduction**. Implement logic in `trainer.py` to measure RSS after each batch. If RSS > 6.0 GB, Reduce batch size to a smaller, computationally efficient value.. If still > 6.0 GB, trigger the capping logic from Phase 1.3 (FR-003, FR-010).
- **2.2**: **Per-Epoch Logging Hook**. Implement a callback in `trainer.py` to log `slot_occupancy` and `coordinate_variance` to `artifacts/metrics/epoch_{epoch}.json` at the end of every epoch (FR-008, FR-009).
- **2.3**: **Training Loop**. Fine-tune spatial and non-spatial (external memory buffer only) variants for a limited number of epochs.

### Phase 3: Evaluation & Metrics
- **3.1**: **Recall Accuracy**. Compute exact-match recall for each seed/dataset/variant (FR-004).
- **3.2**: **Interference Injection**. Implement `src/inference_intervention.py`. This module forces a collision: for spatial models, it perturbs the retrieval key to target an adjacent slot; for non-spatial models, it targets a random index. Compute the drop in recall (FR-011).
- **3.3**: **Statistical Analysis**. Compute paired t-tests (FR-005) AND permutation test p-values + bootstrap CIs to address low power (N=5). Apply Bonferroni correction (FR-006). Compute Cohen's d (FR-007).

### Phase 4: Reporting
- **4.1**: **Artifact Hashing**. Generate checksums for all results.
- **4.2**: **Summary Generation**. Aggregate results into `artifacts/results/run_summary.json`.

## Test Plan

The following unit tests are required to address edge cases and ensure robustness:
- `tests/unit/test_oom_recovery.py`: Verifies that batch size reduction and dataset capping occur correctly when memory limits are exceeded.
- `tests/unit/test_dataset_mismatch.py`: Verifies that the system correctly identifies and handles datasets that do not match the expected variable schema.
- `tests/unit/test_intervention.py`: Verifies the logic for interference injection and metric calculation.
- `tests/unit/test_memory_palace.py`: Verifies slot logic, eviction policies, and coordinate assignment.

## Complexity Tracking

| Violation / Risk | Why It Is a Risk (Complexity) | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Spatial Memory Module (grid-based)

The research question is to determine how grid-based spatial memory architectures influence navigation efficiency in complex environments. The method involves constructing a modular spatial memory system with a configurable grid resolution to evaluate its impact on pathfinding performance. References: Smith et al. (2023), DOI:10.1109/TPAMI.2023.1234567. | **Risk**: Adds significant architectural complexity and potential for implementation bugs in coordinate assignment. | A non-spatial baseline exists, but the spatial module is the independent variable. We cannot remove it without invalidating the hypothesis test. |
| Automatic Batch Size Reduction | **Risk**: Dynamic memory management can introduce non-determinism or silent failures if RSS measurement is inaccurate. | Fixed batch size risks OOM failure on CI, violating Principle VI and causing the job to abort. |
| Interference Distance Metric (Intervention) | **Risk**: Requires a custom inference-time intervention wrapper. If the intervention logic is flawed, the metric is invalid. | Simple recall accuracy is insufficient to distinguish spatial reasoning from general memory capacity. The intervention is necessary to isolate the structural property. |
| Statistical Power Analysis (N=5) | **Risk**: Low power increases Type II error. Requires dual reporting (t-test + permutation) to be scientifically sound. | Reporting only p-values without effect sizes or robustness checks is scientifically incomplete and misleading for N=5. |