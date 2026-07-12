# Quickstart: llmXive follow-up: extending "AgenticSTS: A Bounded-Memory Testbed for Long-Horizon LLM Agents"

## Prerequisites

- Python 3.11+
- `pip` or `venv`
- Access to the 298 AgenticSTS trajectory logs (located in `data/raw/` upon checkout).

## Installation

1. **Clone the repository** and navigate to the project directory:
   ```bash
   git checkout 001-llmxive-agenticsts-followup
   cd projects/PROJ-990-llmxive-follow-up-extending-agenticsts-a
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins versions for reproducibility (Constitution Principle I).*

## Running the Pipeline

The pipeline is orchestrated by `code/main.py`. It performs the following steps:
1. Parse raw trajectories.
2. Validate proxy assumption (FR-006).
3. Train the classifier.
4. Run simulations (Dynamic, Static, Random).
5. Perform statistical analysis.
6. Output results to `data/processed/`.

### Execute Full Pipeline
```bash
cd code
python main.py
```

### Run Individual Steps
- **Parse Data**: `python parser.py`
- **Train Model**: `python classifier.py`
- **Simulate**: `python simulator.py`
- **Analyze Stats**: `python stats.py`

## Expected Outputs

After a successful run, the following files will be generated in `data/processed/`:

- `training_data.csv`: Extracted features and labels.
- `model.pkl`: Trained classifier (Decision Tree/Logistic Regression).
- `proxy_validation.json`: Correlation coefficient and validation status.
- `results.csv`: Per-trajectory outcomes for all three conditions.
- `statistical_results.json`: McNemar's test, t-test, and Bonferroni-corrected p-values.
- `summary.csv`: Aggregated win rates and token usage.

## Troubleshooting

- **NaN Entropy**: If you see warnings about NaN entropy, check `data/raw/` for malformed game states. The system defaults to "all layers" for those turns.
- **Proxy Validation Failed**: If correlation < 0.7, the script will log a warning and fall back to a heuristic. Check `data/processed/proxy_validation.json`.
- **Out of Memory**: The dataset is small. If OOM occurs, check for memory leaks in custom code or ensure no large files are loaded unnecessarily.

## Verification

To verify reproducibility (Constitution Principle I):
1. Delete `data/processed/`.
2. Re-run `python main.py`.
3. Compare the checksum of `statistical_results.json` with the previous run. They must match (random seeds are pinned).
