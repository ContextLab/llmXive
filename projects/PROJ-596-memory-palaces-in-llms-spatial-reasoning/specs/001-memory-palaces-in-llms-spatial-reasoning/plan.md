# Implementation Plan: Memory Palaces in LLMs: Spatial Reasoning for Enhanced Episodic Recall

**Branch**: `PROJ-596-memory-palaces-in-llms-spatial-reasoning` | **Date**: 2026-06-28 | **Spec**: `specs/PROJ-596-memory-palaces-in-llms-spatial-reasoning/spec.md`
**Input**: Feature specification from `/specs/PROJ-596-memory-palaces-in-llms-spatial-reasoning/spec.md`

## Summary

This project investigates whether explicit spatial organization of episodic memories in transformer architectures (a "Memory Palace" mechanism) improves recall accuracy on sequential memory benchmarks compared to standard non-spatial embedding strategies. The approach involves fine-tuning a **DistilGPT2** model (66M parameters, CPU-feasible) with an added 2-D grid memory module (soft-addressed retrieval with distance-decay penalty) against a baseline. Performance is measured via exact-match recall on **bAbI Task 3** (primary) and LAMBADA/Story Cloze (feasibility checks). Statistical significance is tested via paired t-tests (corrected for multiple comparisons) and structural validation via an "interference distance" metric (defined as recall drop under random noise injection for baseline, and adjacent slot injection for spatial).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers` (CPU-optimized), `datasets`, `scikit-learn`, `scipy`, `torch` (CPU wheel), `bitsandbytes` (CPU-compatible version if available, otherwise fallback to 8-bit via `accelerate` or standard quantization logic that does not require CUDA), `pandas`, `numpy`, `pyyaml`.  
**Storage**: Local filesystem (`data/`, `artifacts/`); no external database.  
**Testing**: `pytest` (unit tests for metric calculation, integration tests for training loop memory constraints).  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU cores, ~7 GB RAM, no GPU).  
**Project Type**: Computational research / machine learning experiment.  
**Performance Goals**: Total runtime ≤ 5 hours; Peak RAM ≤ 6 GB (triggering batch size reduction or [deferred] subsampling); Exact-match recall accuracy recorded per seed.
**Constraints**: No CUDA/GPU; no large-LLM training from scratch; strict adherence to 4-bit quantization or equivalent memory-saving techniques; all statistical tests must include multiple-comparison correction.  
**Scale/Scope**: **Primary**: bAbI Task 3 (5 seeds, 3 epochs). **Secondary**: LAMBADA/Story Cloze (1 seed, 1 epoch feasibility check). Multiple model variants (Spatial vs. Baseline) + 1 Ablation (Non-Spatial Attention).

> **Dataset-Variable Fit Note**: The spec assumes bAbI task 3 provides "temporal reasoning targets," LAMBADA provides "long-context prediction," and Story Cloze provides "narrative coherence." The implementation will verify that the specific samples used for these benchmarks actually contain the required episodic structures (e.g., distinct facts to recall) before training. If a dataset lacks the necessary episodic granularity for the "spatial slot" assignment to be meaningful, that dataset will be flagged as a mismatch in `research.md` and excluded from the primary analysis, per the "Dataset-variable fit" methodology.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: The plan mandates pinned random seeds in the code and deterministic data loading from verified URLs. Checksums for derived data will be recorded.
- **II. Verified Accuracy**: All citations in `research.md` will be limited to the "Verified datasets" block provided in the prompt. No external URLs will be fabricated.
- **III. Data Hygiene**: Raw data will be downloaded to `data/raw/` with checksums. Processed data (subsampled/evicted) will be written to `data/processed/` with derivation logs. No PII handling is expected as these are public synthetic/text datasets.
- **IV. Single Source of Truth**: All metrics (recall, interference distance, coordinate variance) will be computed by code and stored in `data/metrics/` JSON/CSV files. The paper will only reference these files.
- **V. Versioning**: Every artifact (code, data, results) will carry a content hash. The `state.yaml` will be updated upon artifact changes.
- **VI. Computational Resource Constraints**: The plan explicitly designs for CPU-only execution, 4-bit quantization, and automatic batch size reduction (to 4) or [deferred] data subsampling if RAM > 6 GB. Runtime is capped at a fixed duration. **Note**: The Constitution specifies "single CPU core" but the GitHub Actions runner provides cores; the plan interprets this as "no additional parallelization beyond the runner's default" to ensure the 5-hour limit.
- **VII. Benchmark Standardization**: Only bAbI task 3, LAMBADA, and Story Cloze are used. Metrics are restricted to exact-match recall, paired t-tests, Cohen's d, and interference distance.

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-596-memory-palaces-in-llms-spatial-reasoning/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-596-memory-palaces-in-llms-spatial-reasoning/
├── data/
│   ├── raw/             # Downloaded datasets (checksummed)
│   └── processed/       # Subsampled/evicted data for training
├── code/
│   ├── __init__.py
│   ├── models/
│   │   ├── base.py      # Non-spatial baseline wrapper
│   │   ├── spatial.py   # Spatial memory module (2-D grid, soft-addressed, distance-decay)
│   │   └── ablation.py  # Non-spatial attention ablation (same params, no grid)
│   ├── training/
│   │   ├── loop.py      # Training loop with memory monitoring and 20% subsampling trigger
│   │   └── config.py    # Hyperparameters (epochs=3, lr=5e-5, batch_size adaptive)
│   ├── evaluation/
│   │   ├── metrics.py   # Recall accuracy, interference distance, coordinate variance
│   │   └── stats.py     # T-tests, Cohen's d, multiple comparison correction, power analysis
│   └── main.py          # Entry point: download -> train -> evaluate -> report
├── tests/
│   ├── unit/            # Unit tests for metrics and memory monitoring
│   └── integration/     # End-to-end small-scale run
├── artifacts/
│   └── results/         # JSON/CSV outputs of metrics
└── requirements.txt     # Pinned dependencies
```

**Structure Decision**: A single project structure is selected to minimize overhead and ensure reproducibility on the CI runner. The separation into `models`, `training`, and `evaluation` ensures modularity while keeping the codebase compact enough for the 6-hour runtime limit.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **DistilGPT2 (66M)** | Required to fit in constrained CPU memory with training overhead. | GPT Medium exceeds RAM even with low-bit quantization during training on CPU. |
| **4-bit Quantization + CPU** | Required to fit model weights in RAM. | Full precision or 8-bit (bitsandbytes on CUDA) is impossible without GPU. |
| **Interference Distance Metric** | Required to address reviewer concerns (Rosalind Franklin) about "measurable structural correlates." | Simple recall accuracy alone is insufficient to prove *spatial* organization is the cause of improvement. |
| **Adaptive Batch Size & [deferred] Subsampling** | Required to respect a hard RAM constraint (Constitution VI). | Fixed batch size 8 or full dataset risks OOM crashes on the free-tier runner. |
| **Multiple Comparison Correction** | Required by FR-006 and SC-004 to prevent false positives across 3 datasets. | Reporting raw p-values would inflate Type I error rates. |
| **Distance-Decay Penalty** | Required to enforce locality and distinguish from standard attention. | Soft attention without decay is mathematically equivalent to global memory, not spatial. |

## Phase Breakdown

### Phase 0: Research & Feasibility (Drafting `research.md`)
- **Goal**: Verify dataset availability, confirm variable fit, and select CPU-tractable libraries.
- **Tasks**:
  - Verify URLs for bAbI, LAMBADA, Story Cloze (using provided verified list or standard HuggingFace loaders).
  - Confirm `distilgpt2` 4-bit quantization works on CPU.
  - Define the "Interference Distance" calculation method (random injection for baseline, adjacent for spatial).
  - Document dataset-variable fit (ensure datasets contain episodic chunks).
  - Perform power analysis for N=5.

### Phase 1: Data Model & Design (Drafting `data-model.md`, `quickstart.md`, `contracts/`)
- **Goal**: Define schemas for inputs, outputs, and intermediate metrics.
- **Tasks**:
  - Define `MemorySlot`, `EpisodicChunk`, `RecallAccuracy`, `InterferenceDistance`, and `CoordinateVariance` data structures.
  - Create YAML schemas for `dataset_manifest`, `training_run`, and `results`.
  - Draft `quickstart.md` for reproducing the environment.

### Phase 2: Implementation (Code Generation - handled by Implementer Agent)
- **Goal**: Write the code to train and evaluate.
- **Tasks**:
  - Implement `spatial.py` with 2-D grid, soft-addressed retrieval, and distance-decay penalty.
  - Implement `ablation.py` with non-spatial attention (same params, no grid).
 - Implement `training/loop.py` with memory monitoring (RSS check), batch size reduction, and **[deferred] subsampling trigger** (if RAM > 6GB at batch size 4).
  - Implement `evaluation/metrics.py` (Recall, Interference, Coordinate Variance) and `stats.py`.

### Phase 3: Execution & Validation
- **Goal**: Run the experiment on CI and validate results.
- **Tasks**:
  - Execute `main.py` on GitHub Actions.
  - Verify runtime ≤ 5h and RAM ≤ 6 GB.
  - Validate statistical outputs (p-values, CIs, effect sizes).
