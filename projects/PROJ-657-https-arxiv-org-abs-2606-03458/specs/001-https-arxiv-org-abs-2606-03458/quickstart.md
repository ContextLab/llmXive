# Quickstart: KVarN Variance-Normalized KV-Cache Quantization

## Prerequisites

- Python 3.10+
- 7 GB+ RAM (GitHub Actions Free Tier compatible)
- No GPU required.

## Installation

1. **Clone the repository**
 ```bash
 git clone
 cd kvarn-project
 ```

2. **Create Virtual Environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install Dependencies**
 ```bash
 pip install -r code/requirements.txt
 ```
 *Note: `requirements.txt` pins CPU-compatible versions of `torch` and `transformers`.*

## Running the Experiment

### 1. Download Datasets
The script automatically downloads and checksums datasets to `data/raw/`.
```bash
python code/run_experiment.py --mode download
```

### 2. Run Inference (Sample Mode)
Run a small subset to verify the pipeline (recommended for quick testing).
```bash
python code/run_experiment.py --mode run --benchmark MATH500 --sample-size 10 --method kvarn
```
*Flags:*
- `--benchmark`: `MATH500`, `AIME24`, `HumanEval`, `IFEVAL`.
- `--sample-size`: Number of items to process (default: 50).
- `--method`: `uniform` (baseline) or `kvarn`.

### 3. Run Full Analysis
Run both methods on the full sample and generate statistics.
```bash
python code/run_experiment.py --mode full --benchmarks MATH500,AIME24 --sample-size 50
```

### 4. View Results
Results are saved to `data/processed/`.
- `results_*.jsonl`: Detailed per-instance logs.
- `summary_stats.csv`: Aggregated accuracy and MSE.
- `plots/`: Generated visualizations.

```bash
cat data/processed/summary_stats.csv
```

## Troubleshooting

- **Memory Error**: Reduce `--sample-size` or use `--batch-size 1`. Ensure no other processes are using RAM.
- **Timeout**: The 6-hour CI limit may be exceeded. The script logs progress; partial results are saved.
- **Import Error**: Ensure `torch` is installed with CPU support.