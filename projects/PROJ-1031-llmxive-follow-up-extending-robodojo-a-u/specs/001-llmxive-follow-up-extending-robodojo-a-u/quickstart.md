# Quickstart: llmXive Follow-up: Extending RoboDojo with Symbolic Abstractions

## Prerequisites

- Python 3.11+
- Git
- Access to HuggingFace (for RoboDojo dataset)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins all versions and includes `torch`, `transformers`, `polars`, `scipy`.*

4.  **Configure linting/formatting** (T002):
    ```bash
    # Install ruff and black
    pip install ruff black
    # Run initial check
    ruff check code/
    black --check code/
    ```

## Running the Pipeline

### 1. Download Data
The script automatically streams data from the verified HuggingFace URLs. No manual download required.
```bash
python code/main.py --stage download
```
*Output: `data/raw/` with checksums.*

### 2. Generate Embeddings & States
```bash
python code/main.py --stage embed --tasks 18
```
*Output: `data/interim/semantic_embeddings.parquet`, `data/interim/symbolic_states.parquet`.*

### 3. Run Symbolic Planner
```bash
python code/main.py --stage plan --tasks 18
```
*Output: `data/interim/action_sequences.parquet`.*

### 4. Execute & Log (Oracle & Real)
```bash
python code/main.py --stage execute --mode oracle  # Test T010
python code/main.py --stage execute --mode real    # Test T024, T026
```
*Output: `data/interim/execution_logs.parquet` (with failure modes).*

### 5. Statistical Analysis
```bash
python code/main.py --stage analyze
```
*Output: `data/reports/statistical_analysis.json`, `data/reports/final_report.md`.*

## Verification

### Check Data Integrity
```bash
python code/utils/io.py --verify-checksums
```

### Run Tests
```bash
pytest code/tests/ -v
```

### Lint & Format
```bash
ruff check code/ --fix
black code/
```

## Troubleshooting

- **OOM Error**: Ensure `streaming=True` is used in `datasets.load_dataset`. Reduce `--tasks` count.
- **Planner Timeout**: Increase `--timeout` flag or switch to MCTS with lower depth.
- **Missing Logs**: Check `data/interim/execution_logs.parquet` exists. If not, re-run `--stage execute`.
- **Mapping Ambiguity**: If `mapping_accuracy` is low, check the `semantic_encoder.py` configuration or reduce task complexity.