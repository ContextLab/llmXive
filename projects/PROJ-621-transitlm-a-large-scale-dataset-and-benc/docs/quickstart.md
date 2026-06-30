# Quickstart: Map-Free Transit Route Generation with LLMs

This guide provides step-by-step instructions to set up the environment, generate the dataset, train the model, run the benchmark, and interpret the results for the **Map-Free Transit Route Generation** project.

## Prerequisites

- Python 3.11+
- pip (Python package installer)
- ~8GB RAM (for model inference and training on CPU)
- ~10GB disk space

## 1. Setup Environment

### 1.1. Clone and Initialize
Ensure you are in the project root directory.

```bash
# Initialize the project structure if not already done
python code/src/setup_project.py
```

### 1.2. Install Dependencies
Install the required packages listed in `requirements.txt`.

```bash
pip install -r requirements.txt
```

**Note**: This project uses CPU-only inference. Ensure you do **not** install GPU-specific versions of PyTorch unless you have specific hardware requirements and modify the code accordingly.

## 2. Data Preparation (User Story 3)

Before training, you must generate the "map-free" dataset from GTFS feeds.

### 2.1. Fetch and Convert GTFS Data
This script downloads the NYC MTA GTFS feed, converts it to a NetworkX graph, and generates natural language route sequences.

```bash
python code/src/analysis/generate_dataset.py
```

**Outputs**:
- `data/processed/train_sequences.txt`: Training data (natural language routes).
- `data/processed/test_od_pairs.json`: Held-out Origin-Destination pairs for testing.
- `data/processed/graph.json`: The ground-truth transit graph (no coordinates).

### 2.2. Verify Map-Free Constraints
Run the verification script to ensure no geographic coordinates leaked into the text sequences.

```bash
python code/src/analysis/verify_map_free.py
```

**Expected Output**: A report confirming zero matches for latitude/longitude regex patterns.

## 3. Model Training (User Story 1)

Fine-tune a small LLM (≤1.5B parameters) on the generated dataset using LoRA.

```bash
python code/src/analysis/train.py
```

**Configuration**:
- **Model**: TinyLlama (or similar ≤1.5B model)
- **Device**: CPU
- **Memory Limit**: 7GB
- **Output**: `data/models/fine_tuned_adapter/`

**Monitoring**:
The script includes a memory monitor. If peak RSS exceeds 7GB, the process will abort.

## 4. Benchmark & Validation (User Story 1)

Run the end-to-end benchmark to generate routes for the held-out test set and validate them against the ground-truth graph.

```bash
python code/src/cli/run_benchmark.py
```

**Outputs**:
- `data/results/validation_scores.json`: Contains `exact_match_score` and `connectivity_validity_score` for each test sample.

### 4.1. Interpret Benchmark Results
Open `data/results/validation_scores.json`. Key metrics:
- **Exact Match Score (0.0 - 1.0)**: Percentage of generated routes that perfectly match the ground truth sequence of stations.
- **Connectivity Validity (0.0 - 1.0)**: Percentage of generated routes where every consecutive station pair exists as a valid edge in the GTFS graph.

## 5. Statistical Analysis (User Story 2)

Compare the fine-tuned model against a zero-shot baseline (TinyLlama without fine-tuning) to determine statistical significance.

### 5.1. Run Baseline
(If not already cached) Run the baseline inference script.
```bash
python code/src/analysis/baseline.py
```

### 5.2. Generate Statistical Report
Run the analysis script to perform McNemar's test.

```bash
python code/src/analysis/generate_statistical_report.py
```

**Outputs**:
- `data/results/statistical_report.md`: A markdown report containing:
 - **Confusion Matrix**: Comparing Fine-tuned vs. Baseline validity.
 - **McNemar's p-value**: A value < 0.05 indicates the improvement is statistically significant.
 - **Confidence Intervals**: For the difference in performance.

## 6. Running Tests

To ensure code integrity, run the test suite:

```bash
pytest code/tests/ -v
```

Key test files:
- `tests/unit/test_graph_validation.py`: Validates graph traversal logic.
- `tests/unit/test_stats.py`: Verifies McNemar's test implementation.
- `tests/contract/test_route_sequence_schema.py`: Ensures data schema compliance.

## Troubleshooting

- **Memory Error**: If you encounter `MemoryError` or RSS > 7GB, reduce the `batch_size` in `src/analysis/train.py` or ensure no other heavy applications are running.
- **Missing GTFS Feed**: If `generate_dataset.py` fails to download the feed, check your internet connection or manually download the GTFS zip to `data/raw/` and update the script's URL configuration.
- **Import Errors**: Ensure `code/` is in your `PYTHONPATH` or run from the project root.

## Next Steps

- **Optimization**: See `tasks.md` T029 for batch processing optimizations.
- **Security**: Review `tasks.md` T031 for input sanitization hardening.
- **Extensions**: Consider adding new transit agencies to the GTFS fetcher.