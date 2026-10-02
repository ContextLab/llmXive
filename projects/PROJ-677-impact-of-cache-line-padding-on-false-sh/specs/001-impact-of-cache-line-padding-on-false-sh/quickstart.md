# Quickstart: Impact of Cache Line Padding on False Sharing in Concurrent Counters

## 1. Prerequisites

- **System**: Linux (Ubuntu 20.04+), macOS, or Windows (WSL2)
- **Compiler**: GCC 11+ or Clang 13+ (C++17 support)
- **Python**: 3.11+
- **Dependencies**: `cmake`, `make`, `pip`, `venv`, `cpupower` (for CPU pinning)

## 2. Setup

### 2.1. Clone & Initialize
```bash
git clone <repo-url>
cd projects/PROJ-677-impact-of-cache-line-padding-on-false-sh
```

### 2.2. Build C++ Benchmark
```bash
cd code/benchmark
mkdir -p build && cd build
cmake ..
make -j$(nproc)
```

### 2.3. Install Python Dependencies
```bash
cd ../analysis
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## 3. Run Benchmark

### 3.1. Hardware Detection
```bash
python code/benchmark/hardware_detect.py
# Output: data/hardware_spec.yaml
# Verification: Check keys cpu_model, core_count, cache_line_size
```

### 3.2. Layout Verification
```bash
./build/verify_layout
# Verifies struct sizes and alignment
```

### 3.3. Execute Full Benchmark
```bash
cd code/scripts
./run_benchmarks.sh
# Note: This script sets CPU governor to 'performance' and pins threads.
# Output: data/raw/benchmark_results.csv
```

## 4. Analyze Results

```bash
cd code/analysis
python analysis.py
# Output:
#   - data/processed/aggregated_results.csv
#   - data/processed/statistical_comparisons.csv
#   - data/processed/throughput_plot.png
```

## 5. Validate Data

```bash
python validate_raw_data.py data/raw/benchmark_results.csv
# Checks: schema compliance, NaNs, missing values
```

## 6. CI/CD

Run on GitHub Actions:
```yaml
# .github/workflows/benchmark.yml
name: Benchmark
on: [push, pull_request]
jobs:
  benchmark:
    runs-on: ubuntu-latest
    timeout-minutes: 360
    steps:
      - uses: actions/checkout@v3
      - name: Build
        run: |
          cd code/benchmark && mkdir -p build && cd build
          cmake .. && make -j$(nproc)
      - name: Run
        run: |
          cd code/scripts && ./run_benchmarks.sh
      - name: Analyze
        run: |
          cd code/analysis && python analysis.py
```