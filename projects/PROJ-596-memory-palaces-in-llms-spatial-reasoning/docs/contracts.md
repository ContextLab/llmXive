# Contracts Document: Memory Palaces in LLMs

**Project**: PROJ-596-memory-palaces-in-llms-spatial-reasoning
**Version**: 1.0.0
**Date**: 2026-07-03
**Status**: Draft

This document defines the formal contracts, interfaces, and behavioral guarantees for the Memory Palace architecture. It serves as the binding specification between the spatial memory modules, the transformer backbone, and the evaluation framework.

## 1. Scope and Purpose

The purpose of this contract is to ensure that:
1. Spatial coordinate assignment is deterministic and reproducible across seeds.
2. Memory slot operations (read/write) are consistent with the transformer's attention mechanism.
3. Evaluation metrics (recall, interference distance) are computed on real, verifiable data without synthetic fallbacks.
4. Resource constraints (RAM, runtime) are enforced and logged explicitly.

## 2. Functional Requirements

### FR-001: Coordinate Assignment
**Contract**: The `CoordinateAssigner` must assign a unique 2D grid coordinate `(x, y)` to every `EpisodicChunk` based on its content hash and current slot occupancy.
- **Input**: `EpisodicChunk` (text, metadata), `MemoryGrid` (current state).
- **Output**: `CoordinateAssignmentResult` containing `(x, y)` and `interference_potential`.
- **Guarantee**: No two chunks with identical content hashes map to the same coordinate unless the grid is full (in which case, the eviction policy defined in FR-004 applies).
- **Failure Mode**: If the grid is full and no eviction strategy can free a slot, the system must raise a `MemoryGridFullError` rather than silently overwriting data.

### FR-002: Soft-Addressed Retrieval
**Contract**: The `spatial_attention_loss` module must compute a weighted aggregation of memory slots using cosine similarity between the query embedding and slot coordinates.
- **Input**: Query embedding `q`, Memory Grid `M`.
- **Output**: Aggregated context vector `c` and scalar loss value `L_spatial`.
- **Guarantee**: The retrieval weights must sum to 1.0 (softmax normalized). The similarity metric must be cosine similarity.
- **Failure Mode**: If `M` is empty, return a zero vector and a loss of 0.0 (no penalty for missing memory).

### FR-003: Resource Constraints (Memory & Runtime)
**Contract**: The `MemoryMonitor` and `TrainingLoop` must enforce a hard limit of 6 GB RSS for the training process.
- **Behavior**:
 1. If RSS > 6 GB, reduce `batch_size` to 4.
 2. If RSS > 6 GB at `batch_size=4`, cap the training dataset to 10% of its original size.
 3. Log the decision and final hyperparameters to `artifacts/results/hyperparams_log.json`.
- **Guarantee**: The process must never exceed 6 GB RSS for more than 5 seconds.
- **Failure Mode**: If the dataset capping reduces the training set to < 100 samples, raise `InsufficientDataError`.

### FR-004: Eviction Policy
**Contract**: When the memory grid is full, the system must evict the slot with the lowest "recency-weighted activation" score.
- **Input**: `MemoryGrid`, new `EpisodicChunk`.
- **Output**: Evicted slot index and updated grid.
- **Guarantee**: Eviction must be deterministic given the same sequence of inputs.

## 3. Interface Contracts

### 3.1. Data Models

#### `EpisodicChunk`
| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Unique identifier for the chunk. |
| `content` | `str` | The raw text content. |
| `timestamp` | `datetime` | When the chunk was created. |
| `coordinates` | `Optional[Tuple[int, int]]` | Assigned (x, y) grid position. |

#### `MemorySlot`
| Field | Type | Description |
|-------|------|-------------|
| `coordinate` | `Tuple[int, int]` | Grid position. |
| `chunk` | `Optional[EpisodicChunk]` | The stored chunk. |
| `activation_score` | `float` | Last computed activation. |
| `access_count` | `int` | Number of times accessed. |

### 3.2. Module Interfaces

#### `code/models/coordinate_assigner.py`
```python
class CoordinateAssigner:
 def assign(self, chunk: EpisodicChunk, grid: MemoryGrid) -> CoordinateAssignmentResult:
 """Assigns coordinates and returns interference potential."""
...
```

#### `code/models/spatial.py`
```python
def soft_addressed_retrieve(query: torch.Tensor, grid: MemoryGrid) -> Tuple[torch.Tensor, float]:
 """Returns aggregated context and spatial attention loss."""
...
```

#### `code/training/memory_monitor.py`
```python
class MemoryMonitor:
 def check_and_adjust(self, batch_size: int) -> int:
 """Returns adjusted batch size if RSS > 6GB."""
...
```

## 4. Non-Functional Requirements

### NFR-001: Reproducibility
All random seeds must be fixed at the start of the experiment. The `CoordinateAssigner` must use a deterministic hash function (SHA-256) for content mapping.

### NFR-002: Data Integrity
No synthetic data or placeholder rows are permitted in the evaluation pipeline. All metrics must be derived from real datasets (bAbI, LAMBADA, Story Cloze) as verified by checksums in `data/raw/checksums.json`.

### NFR-003: Performance
The `soft_addressed_retrieve` operation must complete within 50ms for a grid size of 1024 slots on a standard CPU.

## 5. Verification & Validation

### 5.1. Contract Tests
- **T010**: Verify `compute_exact_match_recall` matches expected values on a known dataset subset.
- **T023**: Verify `compute_interference_distance` correctly identifies spatial vs. non-spatial variants.

### 5.2. Integration Tests
- **T011**: Verify `TrainingLoop` respects the 6 GB RAM limit and logs adjustments.
- **T019**: Verify statistical analysis module correctly handles normality checks and fallbacks.

## 6. Change Log

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-07-03 | LLM Implementer | Initial draft based on T008d requirements. |