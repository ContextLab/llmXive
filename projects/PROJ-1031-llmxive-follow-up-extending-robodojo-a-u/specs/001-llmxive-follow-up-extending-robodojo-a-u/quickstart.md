# Quickstart: Extending RoboDojo with Symbolic Abstractions

## Prerequisites
- Python 3.11 or newer
- Git
- Internet access (to download HuggingFace datasets)

## Installation
```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u

# Virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r code/requirements.txt
```

## Linting & Formatting (T002)
```bash
pip install ruff black
ruff check code/ --fix
black code/
```

## Running the Full Pipeline
All commands are orchestrated via `code/main.py`.

1. **Download & Stream Raw Data**
   ```bash
   python code/main.py --stage download
   ```
   *Data streamed from the verified HuggingFace URLs; checksums recorded.*

2. **Generate Embeddings & Symbolic States**
   ```bash
   python code/main.py --stage embed --tasks 18
   ```
   *Outputs `semantic_embeddings.parquet` and `symbolic_states.parquet`.*

3. **Plan Action Sequences**
   ```bash
   python code/main.py --stage plan --tasks 18
   ```
   *Produces `action_sequences.parquet` (≤ 60 s per task).*

4. **Execute (Oracle)**
   ```bash
   python code/main.py --stage execute --mode oracle
   ```
   *Validates logical feasibility; logs to `execution_logs.parquet`.*

5. **Execute (Real‑World)**
   ```bash
   python code/main.py --stage execute --mode real
   ```
   *Runs the adapted low‑level controller; logs failures with labels.*

6. **Collect GPU Baseline (Escape Hatch)**
   ```bash
   python code/main.py --stage baseline_gpu --subset 5
   ```
   *Runs a scaled‑down version on the Kaggle free GPU to gather GPU cycles, memory, and wall‑clock for compute‑overhead comparison.*

7. **Statistical Analysis & Report**
   ```bash
   python code/main.py --stage analyze
   ```
   *Creates `data/reports/final_report.md` and `statistical_analysis.json`.*

## Verification
```bash
# Verify data integrity
python code/utils/io.py --verify-checksums

# Ensure execution logs were created
python -c "import pandas as pd; print(pd.read_parquet('data/interim/execution_logs.parquet').head())"

# Run unit tests
pytest code/tests/ -v
```

## Troubleshooting
- **OOM**: Ensure streaming mode is active; reduce `--tasks` if needed.  
- **Planner Timeout**: Increase `--timeout` or switch to MCTS (`--planner mcts`).  
- **Missing Logs**: Re‑run the execute stage; verify `execution_logs.parquet` exists.  
- **Low Mapping Accuracy**: Review `semantic_encoder.py` config or increase training data for the mapping model.

---

