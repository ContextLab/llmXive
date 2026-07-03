# Project Contracts: Memory Palaces in LLMs

This document defines the functional, non-functional, and interface contracts for the
`PROJ-596-memory-palaces-in-llms-spatial-reasoning` project. These contracts serve as
binding agreements between system components, ensuring modularity, testability, and
adherence to the scientific hypotheses regarding spatial reasoning in episodic recall.

## 1. Functional Contracts (FR)

### FR-001: Coordinate Assignment
**Requirement**: The system must assign unique 2D coordinates to episodic chunks based on
their semantic content and insertion order.
**Contract**:
- **Input**: `EpisodicChunk` (text representation, semantic embedding).
- **Output**: `MemorySlot` with assigned `(x, y)` coordinates within a defined grid.
- **Constraint**: Coordinates must be deterministic for identical input sequences across
 random seeds, modulo the random seed initialization of the coordinate assigner.
- **Implementation**: Enforced by `code/models/coordinate_assigner.py` using
 `CoordinateAssigner.calculate_interference_potential`.

### FR-002: Soft-Addressed Retrieval
**Requirement**: The model must retrieve information using soft attention over spatial
coordinates rather than hard indexing.
**Contract**:
- **Input**: Query embedding, set of occupied `MemorySlot` coordinates.
- **Output**: Weighted sum of slot contents based on cosine similarity between query
 and slot coordinates.
- **Metric**: Retrieval accuracy must be measurable via exact-match recall against
 ground truth answers in bAbI Task 3.
- **Implementation**: Enforced by `code/models/spatial.py` (cosine similarity calculation).

### FR-003: Memory Budget Enforcement
**Requirement**: The training loop must dynamically adapt to available RAM to prevent OOM.
**Contract**:
- **Threshold**: 6 GB RSS (Resident Set Size).
- **Action 1**: If RSS > 6 GB, reduce batch size from 8 to 4.
- **Action 2**: If RSS > 6 GB at batch size 4, cap the training dataset to 50% of its
 original size.
- **Logging**: All adaptations must be logged to `artifacts/results/hyperparams_log.json`.
- **Implementation**: Enforced by `code/training/memory_monitor.py` and
 `code/training/loop.py`.

### FR-004: Baseline Comparison
**Requirement**: A standard GPT-2 Medium (quantized) baseline must be trained alongside
the spatial variant.
**Contract**:
- **Fallback**: If GPT-2 Medium cannot be loaded within memory budget, `DistilGPT2`
 must be used as the fallback baseline.
- **Interface**: Both models must expose the same training and inference interface.
- **Implementation**: Enforced by `code/models/loading.py` and `code/models/base.py`.

### FR-005: Reproducibility
**Requirement**: Experiments must be reproducible across 5 random seeds.
**Contract**:
- **Seeds**: [-4, -3, -2, -1, 0] (or equivalent fixed set).
- **Output**: `artifacts/results/recall_accuracy.json` must contain per-seed results.
- **Implementation**: Enforced by `code/main.py` orchestration.

### FR-006: Statistical Rigor
**Requirement**: Comparisons between spatial and baseline models must include multiple-comparison
correction.
**Contract**:
- **Method**: Bonferroni or Holm-Bonferroni correction for three dataset comparisons
 (bAbI, LAMBADA, Story Cloze).
- **Output**: `artifacts/results/statistical_summary.json` with corrected p-values.
- **Implementation**: Enforced by `code/evaluation/stats.py`.

### FR-007: Effect Size Reporting
**Requirement**: Statistical tests must report effect sizes, not just p-values.
**Contract**:
- **Metric**: Cohen's d with 95% confidence intervals.
- **Output**: Included in `artifacts/results/statistical_summary.json`.
- **Implementation**: Enforced by `code/evaluation/stats.py`.

## 2. Non-Functional Contracts (NFR)

### NFR-001: Runtime Constraint
**Requirement**: The full pipeline (download, train, evaluate) must complete within 5 hours.
**Contract**:
- **Limit**: 18,000 seconds.
- **Output**: `artifacts/results/runtime_report.json` with `within_limit` boolean.
- **Implementation**: Enforced by `code/main.py` and `code/training/loop.py`.

### NFR-002: Data Integrity
**Requirement**: All downloaded datasets must be verified via checksums.
**Contract**:
- **Action**: Compute SHA-256 for every downloaded file.
- **Storage**: Store checksums in `data/raw/checksums.json`.
- **Implementation**: Enforced by `code/data/download.py`.

### NFR-003: Logging Standard
**Requirement**: All experimental metadata must be structured and machine-readable.
**Contract**:
- **Format**: JSON for structured logs, CSV for time-series metrics.
- **Location**: `artifacts/results/`.
- **Implementation**: Enforced by `code/utils/logger.py`.

## 3. Interface Contracts (IC)

### IC-001: Data Loading Interface
**Module**: `code/data/download.py`
**Public API**:
- `compute_file_checksum(file_path: Path) -> str`
- `get_dataset_cache_paths(dataset_name: str) -> dict`
- `download_and_verify(dataset_name: str) -> bool`
- `main() -> None`

### IC-002: Model Loading Interface
**Module**: `code/models/loading.py`
**Public API**:
- `check_memory_budget() -> Tuple[bool, int]` (returns (is_sufficient, estimated_rss_mb))
- `load_gpt2_medium_quantized() -> torch.nn.Module`
- `load_distilgpt2_fallback() -> torch.nn.Module`
- `load_model(use_spatial: bool) -> torch.nn.Module`
- `main() -> None`

### IC-003: Memory Monitoring Interface
**Module**: `code/training/memory_monitor.py`
**Public API**:
- `MemoryMonitor` class
 - `check_and_adapt(batch_size: int, dataset_size: int) -> Tuple[int, int]`
 - `log_state() -> None`
- `main() -> None`

### IC-004: Spatial Logic Interface
**Module**: `code/models/spatial.py`
**Public API**:
- `calculate_cosine_similarity(coord_a: np.ndarray, coord_b: np.ndarray) -> float`
- `soft_addressed_retrieval(query: np.ndarray, slots: List[MemorySlot]) -> torch.Tensor`

### IC-005: Evaluation Interface
**Module**: `code/evaluation/metrics.py`
**Public API**:
- `compute_exact_match_recall(predictions: List[str], ground_truth: List[str]) -> float`
- `compute_interference_distance(spatial_slots: List[MemorySlot], baseline_slots: List[MemorySlot]) -> float`
- `log_slot_occupancy(epoch: int, slots: List[MemorySlot]) -> None`
- `log_coordinate_variance(epoch: int, slots: List[MemorySlot]) -> None`

### IC-006: Statistical Analysis Interface
**Module**: `code/evaluation/stats.py`
**Public API**:
- `perform_ttest(group_a: List[float], group_b: List[float]) -> Dict[str, float]`
- `apply_correction(p_values: List[float], method: str) -> List[float]`
- `calculate_cohens_d(group_a: List[float], group_b: List[float]) -> Dict[str, float]`

## 4. Reviewer-Specific Contracts

### Contract: Rosalind Franklin (Structural Correlates)
**Requirement**: "What metric distinguishes spatial organization from arbitrary embeddings?"
**Response**: The `interference_distance` metric (IC-005) quantifies the spatial clustering
of semantically similar items. A lower interference distance for the spatial variant
compared to the baseline validates the structural hypothesis.

### Contract: John von Neumann (Address vs. Content)
**Requirement**: "Clear distinction between address and content."
**Response**: The `MemorySlot` data structure (IC-004) explicitly separates `coordinates`
(address) from `content` (tensor data). The retrieval mechanism uses coordinates for
addressing but returns content tensors.

### Contract: Eric Kandel (Biological Reality)
**Requirement**: "Does the system account for biological reality of synapse storage?"
**Response**: The `slot_occupancy` logging (IC-005) tracks how memory slots are filled
over epochs, simulating synaptic consolidation. The `coordinate_variance` metric
tracks the stability of spatial organization over time.