# Quickstart Guide

This guide provides instructions for setting up the **Heterogeneous Scientific Foundation Model Collaboration Benchmark** project and running the initial benchmark.

## Prerequisites

Ensure the following software is installed on your system before proceeding:

- **Python**: Version 3.11 or higher.
 - Verify: `python --version`
- **pip**: Package installer for Python.
 - Verify: `pip --version`
- **git**: Version control system.
 - Verify: `git --version`
- **System Dependencies**:
 - Ensure `build-essential` (Linux) or Xcode Command Line Tools (macOS) are installed for compiling native extensions if required by dependencies.

## Setup Commands

Follow these steps to clone the repository, create a virtual environment, and install dependencies.

### 1. Clone the Repository

```bash
git clone
cd PROJ-573-https-arxiv-org-abs-2604-27351
```

### 2. Create a Virtual Environment

It is recommended to use a virtual environment to isolate dependencies.

```bash
python -m venv.venv
source.venv/bin/activate # On Windows:.venv\Scripts\activate
```

### 3. Install Dependencies

Install the required Python packages listed in `requirements.txt`.

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Verify Installation

Ensure that the main entry points are accessible and the configuration loads correctly.

```bash
# Check that the benchmark script responds to help
python src/benchmark/run_benchmark.py --help

# Check that the task runner script responds to help
python src/benchmark/run_task.py --help
```

## Verification Steps

After setup, perform the following checks to ensure the environment is ready for research execution.

### 1. Check Directory Structure

Verify that the required data and state directories exist.

```bash
ls -la data/
ls -la state/
ls -la src/
```

Expected output should include:
- `data/` (for datasets)
- `data/processed/`
- `state/` (for artifact hashes)
- `src/benchmark/`
- `src/models/`
- `src/evaluation/`

### 2. Run a Dry-Run Configuration Load

Attempt to load the default configuration without executing the full benchmark to verify YAML parsing and path resolution.

```bash
python -c "from src.benchmark.run_benchmark import load_config; cfg = load_config('src/benchmark/config/default.yaml'); print('Config loaded successfully:', len(cfg.get('datasets', [])), 'datasets found')"
```

### 3. Verify Dataset Availability (Optional)

If you have network access, run the dataset verification script to ensure external datasets are reachable.

```bash
python src/research/verify_timeseries.py
python src/research/verify_tabular.py
python src/research/verify_text.py
```

## Troubleshooting Common Issues

### Issue: `ModuleNotFoundError: No module named 'src'`

**Cause**: The script is being run from outside the project root, or the `src` directory is not in the Python path.
**Solution**: Ensure you are in the project root directory and run:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
# Or run scripts using the module syntax:
python -m src.benchmark.run_benchmark --help
```

### Issue: `PermissionError` when writing to `data/` or `state/`

**Cause**: The user does not have write permissions for the project directories.
**Solution**: Ensure the directory ownership matches the current user or adjust permissions:
```bash
chmod -R u+w data/ state/
```

### Issue: `TypeError: TaskRunner.__init__() got an unexpected keyword argument 'config'`

**Cause**: The `TaskRunner` class definition does not accept the `config` argument passed by the caller.
**Solution**: This is a known API contract issue. Ensure the `TaskRunner` class in `src/tasks/task_runner.py` is updated to accept `**kwargs` or explicitly define `config` in `__init__`. If you are running an older version of the code, update the `TaskRunner` implementation to be tolerant of different initialization signatures.

### Issue: `AttributeError: 'list' object has no attribute 'get'`

**Cause**: The task definition YAML file is expected to be a dictionary with a "tasks" key, but the loaded object is a list.
**Solution**: Check `src/tasks/task_definitions.yaml`. The root element should be a dictionary containing a `tasks` list, e.g.:
```yaml
tasks:
 - task_id: T001
...
```
If the file is currently just a list, wrap it in a `tasks` key.

### Issue: Dataset Download Fails

**Cause**: Network connectivity issues or changes in HuggingFace dataset availability.
**Solution**:
1. Check your internet connection.
2. Verify the dataset name in `src/research/verify_*.py` matches the HuggingFace Hub ID exactly.
3. Ensure `datasets` package is up to date: `pip install --upgrade datasets`.

### Issue: `CUDA` or GPU-related Errors

**Cause**: The project is designed for CPU-only inference (<1GB models). Some installed dependencies might default to GPU.
**Solution**: Ensure you are using the CPU-compatible versions of libraries (e.g., `torch` CPU version) and that no environment variables (like `CUDA_VISIBLE_DEVICES`) are forcing GPU usage if not intended. The benchmark scripts should explicitly handle CPU inference.

## Next Steps

Once verification is complete:

1. Review `research.md` for dataset verification results.
2. Run the full benchmark:
 ```bash
 python src/benchmark/run_benchmark.py --config src/benchmark/config/default.yaml
 ```
3. Check the generated `results.csv` and `summary.pdf` in the output directory.