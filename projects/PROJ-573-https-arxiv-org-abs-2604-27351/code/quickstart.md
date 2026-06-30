# Quickstart Guide

This guide provides the necessary instructions to set up the development environment, install dependencies, and verify the installation for the Heterogeneous Scientific Foundation Model Collaboration Benchmark project.

## Prerequisites

Ensure the following software is installed on your system before proceeding:

- **Python 3.11** (or higher): Required for compatibility with project dependencies.
- **pip**: Python package installer (usually included with Python).
- **git**: Version control system for cloning the repository.
- **make** (Optional): For running convenience commands if the Makefile is used.

Verify your Python version:
```bash
python --version
# Expected output: Python 3.11.x
```

## Setup Instructions

Follow these steps to clone the repository, create a virtual environment, and install dependencies.

### 1. Clone the Repository

```bash
git clone <repository_url>
cd PROJ-573-https-arxiv-org-abs-2604-27351
```

### 2. Create a Virtual Environment

It is recommended to use a virtual environment to isolate dependencies.

```bash
python -m venv.venv
```

### 3. Activate the Virtual Environment

**On macOS/Linux:**
```bash
source.venv/bin/activate
```

**On Windows:**
```bash
.venv\Scripts\activate
```

### 4. Install Dependencies

Install all required packages listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 5. Project Structure Verification

Ensure the directory structure matches the expected layout:

```bash
ls -R
# Should show:
# src/
# benchmark/
# data/
# evaluation/
# models/
# tasks/
# utils/
# validators/
# tests/
# data/
# processed/
# state/
# contracts/
# docs/
# requirements.txt
# quickstart.md
```

## Verification Steps

Perform the following checks to ensure the environment is correctly configured.

### 1. Run CLI Help

Verify that the main benchmark script is executable and responds to help flags:

```bash
python src/benchmark/run_benchmark.py --help
```

**Expected Output:**
- Usage information
- List of available arguments: `--config`, `--mode`, `--seeds`

### 2. Check Data Directory

Ensure the data directories exist and are writable:

```bash
ls -ld data/ data/processed/
```

### 3. Run Unit Tests

Execute the test suite to verify core functionality:

```bash
python -m pytest tests/ -v
```

## Troubleshooting Common Issues

### Issue: `ModuleNotFoundError: No module named 'src'`

**Cause:** The script is being run from the wrong directory or the Python path is not set correctly.

**Solution:**
Ensure you are in the project root directory and run:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
# Or run scripts explicitly with the full path relative to root
python src/benchmark/run_benchmark.py --help
```

### Issue: `TypeError: __init__() got an unexpected keyword argument`

**Cause:** Mismatch between the `TaskRunner` class definition and how it is being instantiated in the benchmark runner.

**Solution:**
This is a known API contract issue. Ensure `src/tasks/task_runner.py` is updated to accept flexible arguments or the caller is adjusted. See `src/tasks/task_runner.py` for the `__init__` signature.

### Issue: `AttributeError: 'list' object has no attribute 'get'`

**Cause:** The task definition YAML file structure does not match the expected dictionary format in `src/benchmark/run_task.py`.

**Solution:**
Check `src/tasks/task_definitions.yaml`. The root element should be a dictionary containing a `tasks` key, not a raw list.
Correct format:
```yaml
tasks:
 - task_id: T001
...
```

### Issue: `FileNotFoundError: [Errno 2] No such file or directory: 'data/...'`

**Cause:** The dataset has not been downloaded yet.

**Solution:**
Run the dataset download script:
```bash
python src/data/download.py
```

### Issue: `ImportError: cannot import name '...'`

**Cause:** Circular imports or missing dependencies in `requirements.txt`.

**Solution:**
1. Verify `requirements.txt` contains all necessary packages (e.g., `numpy`, `pandas`, `scipy`, `pyyaml`, `datasets`).
2. Re-run `pip install -r requirements.txt`.
3. Ensure no circular imports exist between modules in `src/`.

## Next Steps

Once verification is complete, you can proceed to:

1. **Run the Benchmark:**
 ```bash
 python src/benchmark/run_benchmark.py --config default.yaml
 ```
2. **Run a Specific Task:**
 ```bash
 python src/benchmark/run_task.py --task-id T001
 ```
3. **Read the Research Documentation:**
 Review `research.md` for dataset details and methodology.

For more advanced usage, refer to the `specs/` directory and the `src/benchmark/` documentation.
