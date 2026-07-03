# Data Model: Memory Palaces in LLMs

## 1. Core Entities

### 1.1 MemorySlot
Represents a discrete location in the 2-D grid.
- **Coordinates**: `(x, y)` where `x, y ∈ [0, 7]`.
- **Embedding**: Vector `v ∈ ℝ^d` (d = hidden size of DistilGPT2, e.g., 768).
- **Metadata**: `last_accessed` (timestamp), `eviction_count` (integer).

### 1.2 EpisodicChunk
A text unit assigned to a memory slot.
- **Text**: The raw string.
- **Slot_ID**: The assigned `(x, y)` coordinate.
- **Temporal_Order**: Integer index in the sequence.
- **Content_Hash**: SHA-256 of the text (for reproducibility).

### 1.3 RecallAccuracy
The primary outcome metric.
- **Dataset**: Name (e.g., "babi_task3").
- **Seed**: Random seed used.
- **Model_Type**: "spatial", "baseline", or "ablation".
- **Accuracy**: Float (0.0 to 1.0).
- **Timestamp**: When the metric was computed.

### 1.4 InterferenceDistance
The structural metric.
- **Dataset**: Name.
- **Seed**: Random seed.
- **Model_Type**: "spatial" or "baseline".
- **Baseline_Accuracy**: Accuracy without interference.
- **Interference_Accuracy**: Accuracy with noise injection (adjacent for spatial, random for baseline).
- **Drop**: `Baseline_Accuracy - Interference_Accuracy`.

### 1.5 CoordinateVariance
The spatial distribution metric (FR-009).
- **Dataset**: Name.
- **Epoch**: Integer epoch index.
- **Model_Type**: "spatial".
- **Variance_X**: Variance of x-coordinates across all slots used in the epoch.
- **Variance_Y**: Variance of y-coordinates across all slots used in the epoch.
- **Total_Variance**: `Variance_X + Variance_Y`.

## 2. Data Flow

1. **Input**: Raw datasets (bAbI, LAMBADA, Story Cloze) downloaded to `data/raw/`.
2. **Processing**:
   - Chunking: Split text into `EpisodicChunk`s.
   - Assignment: Assign `MemorySlot` coordinates (e.g., round-robin or hash-based).
 - Subsampling: If dataset size > 20% of original (triggered by RAM > 6GB at batch size 4), keep top [deferred] by length.
3. **Training**:
   - Model loads chunks.
   - Updates `MemorySlot` embeddings.
   - Records `RecallAccuracy` per sample.
   - Logs `CoordinateVariance` per epoch.
4. **Evaluation**:
   - Compute `InterferenceDistance` by injecting noise (adjacent for spatial, random for baseline).
   - Aggregate metrics across seeds.
5. **Output**: JSON/CSV files in `artifacts/results/`.

## 3. Schema Definitions

See `contracts/` for detailed YAML schemas.
