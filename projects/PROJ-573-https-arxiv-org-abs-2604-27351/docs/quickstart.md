# Quickstart Guide

This guide provides instructions to set up and verify the **Heterogeneous Scientific Foundation Model Collaboration Benchmark** project.

## 1. Prerequisites

Ensure the following software is installed on your system:

- **Python 3.11**: The project requires Python 3.11 or higher. Verify with `python --version`.
- **pip**: The Python package installer.
- **git**: Required for cloning the repository.

## 2. Setup Commands

Follow these steps to clone the repository, create a virtual environment, and install dependencies.

### Step 1: Clone the Repository

```bash
git clone
cd llmXive-proj-573
```

### Step 2: Create a Virtual Environment

It is recommended to use a virtual environment to isolate dependencies.

```bash
python -m venv venv
```

### Step 3: Activate the Virtual Environment

**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

### Step 4: Install Dependencies

Install the required packages listed in `requirements.txt`.

```bash
pip install -r requirements.txt
```

## 3. Verification Steps

After installation, verify that the setup was successful by running the following checks.

### Check 1: Verify CLI Help

Run the benchmark script with the `--help` flag to ensure the entry point is registered correctly.

```bash
python code/benchmark/run_benchmark.py --help
```

You should see usage instructions and available arguments (e.g., `--config`, `--mode`, `--seeds`).

### Check 2: Verify Data Directory

Ensure the project directory structure includes the `data/` folder.

```bash
ls -la data/
```

The directory should exist. It may be empty until you run the dataset download tasks (Phase 3, T022).

### Check 3: Run a Dry-Run (Optional)

If datasets are available, you can run a dry execution with a minimal configuration to verify imports:

```bash
python code/benchmark/run_benchmark.py --config code/benchmark/config/default.yaml --mode heterogeneous --seeds 1
```

*Note: This may take time depending on dataset availability and network speed.*

## 4. Troubleshooting Common Issues

### Issue: `ModuleNotFoundError`

**Symptom**: `ModuleNotFoundError: No module named '...'`

**Cause**: The virtual environment is not activated, or dependencies are missing.

**Solution**:
1. Ensure the virtual environment is active (check for `(venv)` in your shell prompt).
2. Re-run `pip install -r requirements.txt`.

### Issue: `Python 3.11` Not Found

**Symptom**: `python: command not found` or version is incorrect.

**Cause**: The system default Python is not 3.11.

**Solution**:
1. Install Python 3.11 from [python.org](https://www.python.org/downloads/) or via your package manager (e.g., `brew install python@3.11`).
2. Use the specific command to create the venv: `python3.11 -m venv venv`.

### Issue: Permission Denied on Windows

**Symptom**: `PermissionError` when activating the venv.

**Solution**:
1. Run PowerShell or Command Prompt as Administrator.
2. Alternatively, adjust execution policy: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`.

### Issue: Dataset Download Fails

**Symptom**: `HTTPError` or `ConnectionError` during dataset download.

**Cause**: Network connectivity issues or rate limiting from HuggingFace/UCI.

**Solution**:
1. Check your internet connection.
2. Ensure you are not behind a restrictive proxy.
3. Wait a few minutes and retry (the download script includes retry logic).