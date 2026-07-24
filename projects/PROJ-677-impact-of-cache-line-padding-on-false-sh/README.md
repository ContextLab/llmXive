# Impact of Cache Line Padding on False Sharing in Concurrent Counters

**Project ID**: PROJ-677
**Description**: This project investigates the performance impact of cache line padding on false sharing in multi-threaded atomic counters. It compares a "packed" memory layout (susceptible to false sharing) against a "padded" layout (isolated per thread) across varying thread counts.

## Prerequisites

- **Hardware**: Linux system with `cpupower` available (or root access to write to `/sys/devices/system/cpu/`).
- **Compiler**: `g++` (C++17 support) or `clang++`.
- **Python**: 3.11+ with `pandas`, `scipy`, `matplotlib`, `pydantic`, `pyyaml`.

## Directory Structure

```text
.
├── code/
│ ├── benchmark/ # C++ benchmark harness and counter implementations
│ ├── analysis/ # Python scripts for data processing and visualization
│ ├── contracts/ # Pydantic schemas for data validation
│ └── scripts/ # Build and environment setup scripts
├── data/
│ ├── raw/ # Raw CSV output from benchmark runs
│ └── processed/ # Aggregated results and statistical analysis
├── tests/ # Unit, integration, and contract tests
├── specs/ # Feature specifications and design docs
└── README.md
```

## Quick Start

### 1. Environment Setup

Install Python dependencies:

```bash
cd code/analysis
pip install -r requirements.txt
```

Ensure the CPU governor is set to performance mode (requires sudo):

```bash
# Option A: Using cpupower
sudo cpupower frequency-set -g performance

# Option B: Manual sysfs write (if cpupower unavailable)
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### 2. Build the Benchmark

Compile the C++ benchmark harness and counter implementations:

```bash
cd code/scripts
./build.sh
```

This generates:
- `code/benchmark/benchmark` (main executable)
- `code/benchmark/verify_layout` (memory layout verification utility)

### 3. Run the Benchmarks

Execute the full experiment suite (thread counts: 1, 2, 4, 8; configs: packed, padded):

```bash
cd code/scripts
./run_benchmarks.sh
```

Output:
- Raw timing data saved to `data/raw/benchmark_run_<timestamp>.csv`
- If timeouts occur, rows are marked with `status=TIMEOUT`.

### 4. Analyze Results

Run the statistical analysis pipeline:

```bash
cd code/analysis
python run_analysis.py
```

This script:
- Loads raw CSVs from `data/raw/`
- Computes throughput (operations/sec)
- Performs two-sample t-tests and Cohen's d calculations
- Applies Benjamini-Hochberg FDR correction
- Generates a line plot with 95% confidence intervals
- Writes final results to `data/processed/statistical_comparison.csv`

### 5. Verify Results

Confirm that padding improves performance at higher thread counts:

```bash
cd code/analysis
python verify_results.py
```

### 6. Update Checksums

After successful analysis, update the artifact checksums:

```bash
cd code/analysis
python update_checksums.py
```

## Usage Examples

### Single-Threaded Validation

Verify that the benchmark runs correctly without false sharing effects:

```bash
./code/benchmark/benchmark --threads 1 --config packed
./code/benchmark/benchmark --threads 1 --config padded
```

### Custom Thread Count

Run with a specific thread count (e.g., 4 threads, padded config):

```bash
./code/benchmark/benchmark --threads 4 --config padded
```

### Memory Layout Verification

Check the actual size and alignment of counter structs:

```bash
./code/benchmark/verify_layout
```

Expected output:
- Packed struct size: ~24 bytes
- Padded struct size: ≥192 bytes (3 cache lines of 64 bytes)

## Testing

Run the test suite:

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Contract tests
pytest tests/contract/
```

## Configuration

### Hardware Detection

The `hardware_detect.py` script automatically detects:
- Core count
- Cache line size
- Sets CPU governor to 'performance'

Run manually:

```bash
python code/analysis/hardware_detect.py
```

Output: `data/hardware_spec.yaml`

## Troubleshooting

### CPU Governor Permission Denied

If `run_benchmarks.sh` fails to set the CPU governor:
1. Ensure you have `sudo` privileges.
2. Verify `cpupower` is installed (`sudo apt install linux-tools-common`).
3. Manually write to `/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor`.

### Benchmark Timeout

If the benchmark times out:
1. Check system load (`top`, `htop`).
2. Ensure no other high-CPU processes are running.
3. Reduce the number of iterations in `main.cpp` if necessary.

### Missing Dependencies

Ensure all Python packages are installed:
```bash
pip install pandas scipy matplotlib pydantic pyyaml numpy
```

## License

[Insert License Here]

## References

- [Spec: Cache Line Padding and False Sharing](specs/001-cache-line-padding-false-sharing/)
- [Plan: Project Roadmap](plan.md)