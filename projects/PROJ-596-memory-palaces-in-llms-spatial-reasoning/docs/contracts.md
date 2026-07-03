# Contracts: Memory Palaces in LLMs – Spatial Reasoning for Enhanced Episodic Recall

**Project ID**: PROJ-596
**Version**: 1.0
**Status**: Draft
**Last Updated**: 2026-07-10

## 1. Introduction

This document defines the formal contracts, invariants, and acceptance criteria for the **Memory Palaces in LLMs** research pipeline. These contracts serve as the binding specification between the system's components, ensuring that the implementation of spatial memory mechanisms adheres to the scientific hypotheses and engineering constraints outlined in `specs/001-memory-palaces-in-llms-spatial-reasoning/spec.md`.

The contracts are categorized into:
1. **Data Integrity Contracts**: Ensuring reproducibility and correctness of input datasets.
2. **Memory Architecture Contracts**: Defining the spatial slot structure and coordinate assignment logic.
3. **Training & Resource Contracts**: Enforcing memory budgets and batch size adaptations.
4. **Evaluation & Statistical Contracts**: Mandating rigorous statistical testing and metric definitions.

---

## 2. Data Integrity Contracts

These contracts ensure that the input data used for training and evaluation is authentic, unmodified, and verifiable.

### C-001: Dataset Authenticity
**Scope**: `code/data/download.py`
**Requirement**: The system MUST download datasets exclusively from the canonical Hugging Face Hub repositories:
- `babi` (Task 3, `task3_10k`)
- `lambada`
- `story_cloze`
**Constraint**: No synthetic, hard-coded, or placeholder data is permitted.
**Verification**: Upon download, the system MUST compute the SHA-256 checksum of the raw dataset files and store them in `data/raw/checksums.json`. Any subsequent run must verify the local file against this checksum.

### C-002: Data Immutability
**Scope**: `data/raw/`
**Requirement**: Once a dataset is downloaded and verified, the raw files in `data/raw/` MUST NOT be modified by the training or evaluation scripts. All preprocessing must occur in memory or in a separate `data/processed/` directory.

---

## 3. Memory Architecture Contracts

These contracts define the structural invariants of the "Memory Palace" mechanism, addressing the "binding problem" and the distinction between address (location) and content (data).

### C-003: Spatial Slot Structure
**Scope**: `code/models/memory_slot.py`
**Requirement**: The `MemoryGrid` MUST implement a 2D coordinate system where each slot is addressable by `(x, y)` coordinates.
**Invariant**: The number of slots must be fixed per experiment run and defined in the configuration. No dynamic resizing of the grid is permitted during inference.

### C-004: Coordinate Assignment Logic
**Scope**: `code/models/coordinate_assignment.py`
**Requirement**: The `CoordinateAssigner` MUST assign a unique `(x, y)` coordinate to every `EpisodicChunk` based on a deterministic hash of the chunk's content or temporal sequence, ensuring reproducibility across seeds.
**Constraint**: Coordinates MUST fall strictly within the bounds of the `MemoryGrid` defined in C-003.

### C-005: Soft-Addressed Retrieval
**Scope**: `code/models/spatial.py`
**Requirement**: Retrieval MUST utilize cosine similarity between the query embedding and the spatial slot embeddings.
**Invariant**: The retrieval mechanism MUST be differentiable to allow gradient flow through the spatial addressing mechanism during fine-tuning.

---

## 4. Training & Resource Contracts

These contracts address the engineering constraints regarding hardware limitations and training stability, specifically responding to reviewer concerns about overhead and memory.

### C-006: Memory Budget Enforcement
**Scope**: `code/training/memory_monitor.py`
**Requirement**: The system MUST monitor Resident Set Size (RSS) in real-time.
**Threshold**: If RSS > 6 GB:
1. Reduce batch size to 4.
2. If RSS remains > 6 GB at batch size 4, the system MUST cap the training dataset to a defined fraction (e.g., 50%) of its original size.
**Logging**: All adjustments to batch size or dataset size MUST be logged to `artifacts/results/hyperparams_log.json` with a timestamp and the specific trigger (RSS value).

### C-007: Model Fallback Protocol
**Scope**: `code/models/loading.py`
**Requirement**: The system MUST attempt to load `gpt2-medium` with 4-bit quantization first.
**Fallback**: If the memory budget (C-006) is exceeded even with quantization, the system MUST automatically switch to `DistilGPT2`.
**Invariant**: The fallback mechanism MUST be transparent and recorded in the run metadata.

### C-008: Runtime Limit
**Scope**: `code/main.py`
**Requirement**: The total runtime for a full experiment (download + train + eval) across 5 seeds MUST not exceed 5 hours.
**Action**: If a run exceeds this limit, it MUST be terminated, and the partial results must be recorded with a `status: timeout` flag.

---

## 5. Evaluation & Statistical Contracts

These contracts ensure that the scientific claims regarding "enhanced recall" are supported by rigorous statistical evidence, addressing reviewer concerns about measurable structural correlates.

### C-009: Exact-Match Recall Metric
**Scope**: `code/evaluation/metrics.py`
**Requirement**: The primary metric MUST be Exact-Match Recall (EMR), calculated as the ratio of correctly recalled answers to total questions.
**Constraint**: EMR MUST be computed separately for the spatial variant and the non-spatial baseline.

### C-010: Statistical Significance
**Scope**: `code/evaluation/stats.py`
**Requirement**: Comparisons between spatial and baseline models MUST use paired two-tailed t-tests across the 5 random seeds.
**Normality Check**: A Shapiro-Wilk test MUST be performed. If normality is violated (p < 0.05), the system MUST fallback to the Wilcoxon signed-rank test.
**Correction**: For comparisons across multiple datasets (bAbI, LAMBADA, Story Cloze), the system MUST apply Bonferroni or Holm-Bonferroni correction to the p-values.

### C-011: Effect Size Reporting
**Scope**: `code/evaluation/stats.py`
**Requirement**: All significant comparisons MUST report Cohen's d with a 95% confidence interval.
**Output**: Results MUST be stored in `artifacts/results/statistical_summary.json`.

### C-012: Structural Correlate Metrics
**Scope**: `code/evaluation/metrics.py`
**Requirement**: The system MUST compute and report the following structural metrics to validate spatial organization:
1. **Interference Distance**: The average Euclidean distance between slots containing semantically conflicting information.
2. **Slot Occupancy**: The distribution of items across the grid (logarithmic binning).
3. **Coordinate Variance**: The variance of assigned coordinates over epochs.
**Output**: These metrics MUST be logged per epoch to `artifacts/results/` (CSV/JSON) and summarized in the final report.

---

## 6. Compliance & Verification

To verify compliance with these contracts, the following automated checks are enforced:

| Contract ID | Verification Method | Artifact |
|:--- |:--- |:--- |
| C-001 | Checksum validation script | `data/raw/checksums.json` |
| C-006 | Memory monitor logs | `artifacts/results/hyperparams_log.json` |
| C-009 | Unit test for metric calc | `tests/unit/test_metrics.py` |
| C-010 | Integration test for stats | `tests/unit/test_stats.py` |
| C-012 | Structural metric logger | `artifacts/results/interference_distance.json` |

## 7. Revision History

- **v1.0 (Draft)**: Initial draft covering data, architecture, training, and evaluation contracts.
- **Status**: Pending approval by the scientific review board.