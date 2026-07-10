# Quickstart: Evaluating the Effectiveness of LLM-Driven Code Simplification on Performance

## Prerequisites

- Python 3.11+
- Git
- Sufficient RAM is available.
- Internet connection (for dataset/model download)

## Setup

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-265-evaluating-the-effectiveness-of-llm-driv
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

4. **Download dataset**:
   ```bash
   python code/data/download.py --output data/raw
   ```
   *Note: This script filters for executable functions and generates test suites where missing.*

5. **Validate and preprocess**:
   ```bash
   python code/data/preprocess.py --input data/raw --output data/processed
   ```

## Running the Pipeline

### Full Pipeline

```bash
python code/main.py
```

This will:
1. Download and validate functions (filtering for executability)
2. Generate test suites for equivalence checking
3. Simplify using CodeLlama-3B
4. Check functional equivalence (run test suites)
5. Benchmark performance (**exactly 100 iterations**)
6. Run statistical analysis on **function-level means** (N=100)

### Individual Steps

**Simplify functions**:
```bash
python code/models/simplify.py --input data/processed --output data/processed/simplified
```

**Benchmark performance**:
```bash
python code/models/benchmark.py --input data/processed/simplified --output data/results/benchmark
```

**Run statistical analysis**:
```bash
python code/analysis/stats.py --input data/results/benchmark --output data/results/stats
```

## Expected Outputs

- `data/processed/`: Validated and simplified function pairs (with test suites)
- `data/results/benchmark/`: Iteration-level performance metrics (100 iterations per function)
- `data/results/stats/`: Statistical summaries (JSON)
- `logs/`: Execution logs, failures, and warnings

## Troubleshooting

| Issue | Solution |
|-------|----------|
| OOM during LLM inference | Reduce batch size; ensure 4-bit quantization is enabled |
| Function fails to simplify | Check logs; function may be too complex or invalid |
| Statistical test fails | Verify data integrity; check for missing values |
| Timeout during benchmarking | Increase timeout limit (not recommended) or exclude problematic functions |

## Notes

- **Random seeds** are pinned for reproducibility.
- **Model download** occurs on first run; cached in HuggingFace cache directory.
- **Parallel processing** is enabled via `multiprocessing` for benchmarking.
- **Logs** are written to `logs/` directory for debugging.
- **Fixed Iterations**: The pipeline runs exactly 100 iterations per function.
- **Universal Equivalence Check**: All functions, regardless of size, must pass test suites to be included.
- **Unit of Analysis**: Statistical tests are performed on the 100 function-level means.