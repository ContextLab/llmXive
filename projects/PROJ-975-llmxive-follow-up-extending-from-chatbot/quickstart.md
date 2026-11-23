# Quickstart Guide

## Project: llmXive Follow-up
**Title**: Extending "From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent"

## Prerequisites

Ensure you have Python 3.9+ and `pip` installed.

## Installation

1. Clone the repository and navigate to the project root.
2. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Project Structure

- `data/raw/`: Generated synthetic datasets (tasks, skills)
- `data/results/`: Experiment logs, analysis outputs, and figures
- `code/`: Implementation modules (data generation, agent, analysis)
- `tests/`: Unit and contract tests
- `contracts/`: JSON schemas for data validation
- `state/`: Project state tracking and artifact hashes

## Running the Pipeline

### 1. Setup Project Directories
Ensure the required directory structure exists:
```bash
python code/setup_directories.py
```

### 2. Generate Synthetic Data (User Story 1)
```bash
python code/generate_data.py
```
**Outputs**:
- `data/raw/tasks.json`
- `data/raw/skills.json`
- `data/raw/checksums.json`

### 3. Fix Task Schema (add missing `ground_truth_skills`)
```bash
python code/fix_tasks_schema.py
```

### 4. Validate Raw Data
```bash
pytest tests/contract/
```
Ensures `tasks.json` and `skills.json` conform to their schemas.

### 5. Align Logging Configuration
The `code/logging_config.py` file defines `LOG_COLUMNS`. **Make sure it exactly matches** the required header:
```
run_id,task_id,library_size,pruning_enabled,success,latency_ms,tokens_used,retrieval_precision,retrieval_diversity,edge_case
```
If you modify the header, update `LOG_COLUMNS` accordingly.

### 6. Execute the Agent (full factorial sweep)
```bash
python -m code.agent \
 --library-sizes 10 20 30 40 50 60 70 80 90 100 \
 --overlap low medium high \
 --pruning off fr04 \
 --seed 42 \
 --randomize-tasks
```
**Outputs**:
- `data/results/experiment_log.csv` (detailed execution logs)
- `data/results/execution_logs/run_<size>_<pruning>_<overlap>.jsonl` (JSON‑L logs for each run)

### 7. Verify CSV Output
```bash
python -c "from code.logging_config import verify_log_file_exists; assert verify_log_file_exists(), 'CSV log missing'"
```

### 8. Analyze Results (User Story 3)
```bash
python code/analyze.py --input data/results/experiment_log.csv
```
**Outputs**:
- `data/results/analysis_report.json`
- `data/results/sensitivity_report.json`
- `data/results/final_analysis.json`

### 9. Validate All Outputs
```bash
pytest tests/contract/
```

### 10. Verify End‑to‑End Reproducibility
Run the entire Quickstart on a fresh runner (e.g., a new GitHub Actions job) and confirm that the final `analysis_report.json` matches the one produced in Step 8.

## Configuration

Environment variables can override defaults in `code/config.py`:
- `SEED_A`: Random seed for skill generation (default: 42)
- `SEED_B`: Random seed for task ground‑truth assignment (default: 123)
- `OVERLAP_LEVEL`: 'low', 'medium', or 'high' (default: 'medium')

## Troubleshooting

- **Memory Errors**: The system checks RAM usage. Reduce the dataset size or run on a machine with more RAM if you encounter "Memory Limit Exceeded".
- **Schema Validation Errors**: Ensure `contracts/*.yaml` files are present and match the data structure.
- **Missing Data**: Re‑run `generate_data.py` if `data/raw/` is empty.
- **Logging Issues**: If the CSV header does not match, verify `LOG_COLUMNS` in `code/logging_config.py` and re‑run the dummy‑log command.
- **CLI argument error**: Use the exact flags shown above; do not include braces or other shell‑specific syntax.
- **Pruning removes wrong skills**: Ensure `pruning.py` implements `prune_fr04` as described in the methodology.
- **Agent exits with code 2**: Run `pytest tests/integration/test_full_sweep.py` to see the failure traceback; the updated `agent.py` now accepts multiple pruning flags.