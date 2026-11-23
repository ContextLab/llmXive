# llmXive: ArcANE Project

An automated research pipeline for evaluating character consistency in literature using LLMs.

## Setup

1. **Initialize Structure**:
 ```bash
 python code/setup_project_structure.py
 ```

2. **Setup Data Directories**:
 ```bash
 python code/scripts/setup_data_dirs.py
 ```

3. **Install Dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

## Execution

Run the full experiment pipeline:
```bash
python code/src/cli/run_experiment.py
```

## Project Structure

- `src/`: Source code
- `tests/`: Test suite
- `data/`: Data storage (raw, derived, gold_standard)
- `specs/`: Design documents and contracts
- `config/`: Configuration files
- `scripts/`: Utility scripts
