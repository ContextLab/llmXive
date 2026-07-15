# Quickstart: EvoMem-Conflict Filtering

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local equivalent with 2+ vCPU, 7GB+ RAM).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-850-llmxive-follow-up-extending-evoarena-tra/code/
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins `torch` to a CPU-only version to ensure compatibility with the CI runner.*

## Running the Experiment

### 1. Generate Synthetic Data (if needed)
If the `Terminal-Bench-Evo` dataset is not available locally, generate the synthetic subset:
```bash
python src/data/generate_synthetic.py --output data/raw/tasks.json --count 250
```

### 2. Run the Heuristic Validation
Test the conflict detector on the synthetic pairs:
```bash
python src/tests/unit/test_conflict_detector.py
```
*Expected: Precision/Recall ≥ 80% on the 500 synthetic pairs.*

### 3. Execute the Full Experiment
Run both agent variants on the task set:
```bash
python run_experiment.py --tasks data/raw/tasks.json --output data/logs/execution_logs.csv
```
*This will run `EvoMem-All` and `EvoMem-Conflict` on all tasks and log results.*

### 4. Analyze Results
Generate the statistical report:
```bash
python src/stats_analyzer.py --input data/logs/execution_logs.csv --output data/reports/final_report.md
```

## Verification

- **Check Logs**: Ensure `data/logs/execution_logs.csv` contains entries for all tasks and both variants.
- **Check Stats**: Verify the final report includes a p-value < 0.05 (if significant) and noise reduction percentage.
- **Reproducibility**: Re-run `run_experiment.py` and compare the checksum of `execution_logs.csv`.

## Troubleshooting

- **OOM Errors**: If memory exceeds 7GB, reduce the `--count` in step 1 or use a smaller model in `conflict_detector.py`.
- **CUDA Errors**: Ensure `torch` is installed via `pip install torch --index-url https://download.pytorch.org/whl/cpu`.
- **Missing Dataset**: If `tasks.json` is missing, run the generation script in step 1.
