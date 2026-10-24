# Quickstart: Structural Mismatch Cost in Heterogeneous Retrieval

## Prerequisites
- Python 3.11+
- Linux environment (GitHub Actions or local)
- Internet access for dataset download (optional – synthetic fallback is used)

## Verification Commands (required for T001)

The following commands **must** succeed for the project to be considered
valid. The integration test ``tests/integration/test_skeleton.py`` runs
them and stores the outputs under ``artifacts/``.

1. **Lint the codebase**

 ```bash
 ruff check code/
 ```

2. **Show the CLI help**

 ```bash
 python -m code.main --help
 ```

3. **Run the CLI with no arguments**

 ```bash
 python -m code.main
 ```

## Installation
```bash
cd projects/PROJ-883-llmxive-follow-up-extending-omniretrieva
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt
```

## Running the Full Benchmark
```bash
python -m code.main
```

The quickstart file documents the exact commands that the integration
test validates, fulfilling the requirements of task **T001**.