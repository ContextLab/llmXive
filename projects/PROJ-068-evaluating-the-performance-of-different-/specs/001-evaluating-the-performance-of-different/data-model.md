# Data Model: Evaluating the Performance of Different Data Structures in Implementing Bloom Filters

## Key Entities

### BloomFilter (Abstract)
Represents the core data structure.
- **Attributes**:
  - `size`: int (number of bits)
  - `hash_count`: int (number of hash functions)
  - `false_positive_rate`: float (target FPR)
  - `element_count`: int (number of inserted elements)
- **Methods**:
  - `insert(element: str) -> None`
  - `query(element: str) -> bool`
  - `get_memory_usage() -> int` (bytes)

### Implementation Variants
1. **ArrayBloomFilter**: Uses Python `list` of integers/bytes.
2. **VectorBloomFilter**: Uses dynamic resizing (simulated via `list` append/pop or `array` module).
3. **BitsetBloomFilter**: Uses `bitarray` library for packed bits.

### BenchmarkRun
Represents a single execution instance.
- **Attributes**:
  - `run_id`: str (unique identifier)
  - `implementation`: str ("array", "vector", "bitset")
  - `dataset_size`: int
  - `false_positive_rate`: float
  - `insertion_time_ms`: float
  - `query_time_ms`: float
  - `peak_memory_bytes`: int
  - `repetition_index`: int (1–50)
  - `random_seed`: int
  - `timestamp`: str (ISO 8601)
  - `status`: str ("complete", "timeout", "truncated")

### DatasetMetadata
Describes the dataset used.
- **Attributes**:
  - `source`: str ("synthetic")
  - `element_count`: int
  - `seed`: int
  - `checksum`: str (SHA-256 of the generated sequence)
  - `distribution_params`: dict (mean_length, sigma_length)
  - `ks_test_p_value`: float (statistical equivalence to target distribution)
  - `validation_status`: str ("passed", "degraded")
  - `retry_count`: int (number of KS-test attempts)

## Data Flow

1. **Generation**: `DatasetGenerator` creates synthetic strings with controlled length distribution → `DatasetMetadata` saved.
2. **Validation**: `DatasetValidator` runs KS-test to ensure distribution matches target.
   - If p > 0.05: Status = "passed".
   - If p < 0.05: Retry up to 5 times. If still failing, Status = "degraded" (best-fit parameters used).
3. **Benchmarking**: `BenchmarkRunner` instantiates `BloomFilter` variants → runs insert/query → records `BenchmarkRun`.
4. **Aggregation**: `StatsAnalyzer` reads all `BenchmarkRun` records → computes statistics → generates plots.
5. **Storage**: Raw results saved as CSV; aggregated results as JSON.

## Schema Definitions

- **Input**: Synthetic string list (generated in memory).
- **Output**: CSV file with columns: `run_id, implementation, dataset_size, fpr, insertion_time_ms, query_time_ms, peak_memory_bytes, repetition_index, seed, status`.
- **Intermediate**: JSON logs for debugging.

## Constraints

- **Memory**: `peak_memory_bytes` must be < 7GB.
- **Time**: `insertion_time_ms` + `query_time_ms` < 30 minutes per run.
- **Reproducibility**: `random_seed` must be pinned; `DatasetMetadata` checksum must match.
- **Statistical Validity**: `ks_test_p_value` > 0.05 for "passed" status. If "degraded", `retry_count` must be 5.
- **Retry Limit**: `retry_count` must not exceed 5.