# Quickstart: Evaluating the Performance of Different Data Structures in Implementing Bloom Filters

## Prerequisites

- Python 3.11+
- pip
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-068-evaluating-the-performance-of-different-/code
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *requirements.txt includes*: `numpy`, `scipy`, `memory-profiler`, `pytest`, `bitarray`.

## Running the Benchmark

### 1. Generate Synthetic Dataset
```bash
python -m benchmarks.generator --size 10000 --seed 42 --output data/processed/synthetic_10k.json
```
*Options*:
- `--size`: Number of elements (10k–1M).
- `--seed`: Random seed for reproducibility.
- `--output`: Output file path.
- `--distribution`: (Optional) Log-normal parameters for string length.

### 2. Validate Distribution
```bash
python -m benchmarks.validator --input data/processed/synthetic_10k.json --target enron
```
*Checks*:
- Kolmogorov-Smirnov test p-value > 0.05.
- **Retry Logic**: If validation fails, the generator automatically retries up to 5 times with adjusted parameters.
- **Fallback**: If all 5 retries fail, the generator proceeds with the best-fit parameters and marks the dataset as `degraded` in the output metadata.

### 3. Run Benchmark Suite
```bash
python -m benchmarks.runner \
  --dataset data/processed/synthetic_10k.json \
  --fpr 0.01,0.05,0.10 \
  --sizes 10000,100000,500000,1000000 \
  --repetitions 50 \
  --output results/benchmarks.csv
```
*Options*:
- `--dataset`: Path to generated dataset.
- `--fpr`: Comma-separated false positive rates.
- `--sizes`: Comma-separated dataset sizes.
- `--repetitions`: Number of runs per configuration (default 50).
- `--output`: Output CSV file.
- `--timeout`: Max time per run (default 30 mins).

### 4. Analyze Results
```bash
python -m benchmarks.stats --input results/benchmarks.csv --output results/plots/
```
*Outputs*:
- `results/plots/memory_vs_size.png`
- `results/plots/latency_vs_size.png`
- `results/plots/stats_summary.json` (p-values, effect sizes, power analysis).

## Verifying Correctness

### Unit Tests
```bash
pytest tests/unit/
```
*Checks*:
- Cross-Implementation Consistency (all three implementations produce same results).
- Hash Uniformity (bad hash function degrades FPR as expected).

### Integration Tests
```bash
pytest tests/integration/
```
*Checks*:
- Benchmark pipeline completes without timeout.
- Memory usage stays within 7GB.
- Phased execution logic triggers correctly.
- Dataset validation retry logic (with a configurable maximum retry limit) functions correctly.

## Troubleshooting

- **Memory Error**: Reduce `--sizes` or `--repetitions`.
- **Timeout**: Increase GHA job timeout or reduce dataset size.
- **Import Error**: Ensure `bitarray` is installed (`pip install bitarray`).
- **Distribution Validation Failed**: The system automatically retries up to 5 times. If it still fails, check the `degraded` status in `DatasetMetadata` and verify the target distribution parameters.
- **Infinite Loop**: Not possible; max 5 retries enforced.

## Output Interpretation

- **Memory vs. Size Plot**: Shows linear scaling; bitset should have lowest overhead.
- **Latency vs. Size Plot**: Shows sub-linear scaling; bitset should be fastest.
- **Stats Summary**: `p < 0.05` indicates significant difference between implementations.
- **Power Analysis**: If power < 80% for small effects, results are labeled "Inconclusive".
- **Dataset Status**: If `validation_status` is "degraded", results are still valid but may have slight distributional deviations from the target.