# Quickstart: EvoMem-Conflict Filtering

## Prerequisites
- Python 3.11+
- Git
- Sufficient RAM (recommended for smooth operation, with a defined minimum threshold)

## Installation

1.  **Clone the repository** and navigate to the project directory.
    ```bash
    git clone <repo-url>
    cd projects/PROJ-850-llmxive-follow-up-extending-evoarena-tra
    ```

2.  **Create a virtual environment** and install dependencies.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r code/requirements.txt
    ```

3.  **Verify CPU-only mode** (optional but recommended).
    ```bash
    python -c "import torch; print('CUDA Available:', torch.cuda.is_available())"
    # Expected: CUDA Available: False
    ```

## Running the Experiment

### Step 1: Generate Synthetic Dataset
Generate the `Terminal-Bench-Evo` dataset (Synthetic Generator) and the conflict validation pairs.
```bash
python code/data/generators/terminal_bench_evo_generator.py --output data/terminal_bench_evo.json --seed 42 --target_tasks 200 --target_pairs 500
```
*This creates `data/terminal_bench_evo.json` and `data/conflict_pairs.json`. The `--target_tasks` and `--target_pairs` flags allow dynamic adjustment if the generator underperforms.*

### Step 2: Train/Load Conflict Detector
(If using a pre-trained model, skip training. If fine-tuning, run:)
```bash
python code/models/conflict_detector.py --mode train --data data/conflict_pairs.json --model distilbert-base-uncased
```
*This saves the model to `code/models/checkpoints/conflict_detector.pt`.*

### Step 3: Execute Agents
Run both agents on the generated dataset.
```bash
python code/main.py --dataset data/terminal_bench_evo.json --variants all,conflict --output data/execution_logs.csv
```
*This runs the experiment and outputs `data/execution_logs.csv`.*

### Step 4: Analyze Results
Run the statistical analysis and generate the report.
```bash
python code/analysis/stats.py --input data/execution_logs.csv --output data/analysis_report.json
```

## Expected Output
- `data/execution_logs.csv`: Raw logs for every task step.
- `data/analysis_report.json`: Aggregated metrics, p-values, and noise reduction stats.
- `data/conflict_pairs.json`: Validation dataset for the detector.

## Troubleshooting
- **OOM Error**: Reduce `--batch_size` in `main.py` or ensure no other heavy processes are running.
- **Detector Low Accuracy**: Check `data/conflict_pairs.json` for label balance; ensure `seed` is consistent.
- **No Conflicts Detected**: Lower the confidence threshold in `code/main.py` (default high) to 0.70 for testing.
- **Generator Underperformance**: If the generator produces fewer tasks than `--target_tasks`, check the logs for warnings. The pipeline will proceed with available data but flag the limitation.