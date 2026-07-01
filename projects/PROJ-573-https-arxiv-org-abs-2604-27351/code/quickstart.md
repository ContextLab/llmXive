# Quickstart Guide: Heterogeneous Scientific Foundation Model Collaboration Benchmark

This guide provides instructions for setting up the project environment and running the benchmark.
Follow these steps to verify the installation and execute the analysis pipeline.

## 1. Prerequisites

Ensure your environment meets the following requirements:

- **Python**: Version 3.11 or higher
- **Package Manager**: `pip` (bundled with Python)
- **Operating System**: Linux, macOS, or Windows (WSL recommended for Linux tools)
- **Disk Space**: At least 5GB free space for datasets and dependencies

## 2. Setup Commands

Follow these steps to clone the repository, create a virtual environment, and install dependencies.

### 2.1 Clone the Repository

```bash
git clone
cd llmXive/projects/PROJ-573-https-arxiv-org-abs-2604-27351
```

### 2.2 Create a Virtual Environment

It is recommended to use a virtual environment to isolate dependencies.

```bash
# Create a virtual environment named '.venv'
python -m venv.venv

# Activate the virtual environment
# On macOS/Linux:
source.venv/bin/activate
# On Windows:
#.venv\Scripts\activate
```

### 2.3 Install Dependencies

Install the required packages from the project's requirements file.

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

*Note: If `requirements.txt` is not present in the root, ensure you have completed Task T008 (Initialize Python project).*

## 3. Verification Steps

Before running the full benchmark, verify that the installation is successful and the environment is configured correctly.

### 3.1 Check CLI Help

Verify that the main entry point is executable and can parse arguments.

```bash
python code/src/benchmark/run_benchmark.py --help
```

You should see a list of available arguments including `--config`, `--mode`, and `--seeds`.

### 3.2 Verify Data Directory

Ensure the data directories exist. If they are empty, you may need to run the download scripts (Task T022).

```bash
ls -la code/data/
ls -la code/data/processed/
```

Expected structure:
- `code/data/`
- `code/data/processed/`
- `code/state/`

### 3.3 Run a Quick Test (Single Task)

Run a single task to verify the pipeline connectivity without executing the full benchmark.

```bash
# Example: Run task T001 with a short timeout
python code/src/benchmark/run_task.py --task-id T001
```

If successful, you should see log output indicating the task status and potentially a result file in `code/data/`.

## 4. Troubleshooting Common Issues

### 4.1 Module Import Errors

**Symptom**: `ModuleNotFoundError: No module named 'src'` or similar.
**Solution**: Ensure you are running the script from the project root (`code/` directory in this repo structure) and that the virtual environment is activated.
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/code"
```

### 4.2 Dataset Download Failures

**Symptom**: `ConnectionError` or `Timeout` when running download scripts.
**Solution**:
- Check your internet connection.
- Verify that the HuggingFace datasets library is installed: `pip install datasets`.
- If running behind a proxy, configure `HTTP_PROXY` and `HTTPS_PROXY` environment variables.

### 4.3 TaskRunner Configuration Errors

**Symptom**: `TypeError: TaskRunner.__init__() got an unexpected keyword argument 'config'`.
**Solution**: This indicates a version mismatch between the caller and the `TaskRunner` implementation. Ensure you have updated `code/src/tasks/task_runner.py` to accept the `config` argument or use the updated version from the latest commit. The current implementation should support flexible initialization.

### 4.4 Memory Issues

**Symptom**: `MemoryError` during model loading or inference.
**Solution**: The benchmark is designed for CPU-tractable models (< 1GB). If you encounter memory issues:
- Ensure no other heavy applications are running.
- Check that the correct model weights (distilled/quantized versions) are being loaded.
- Verify the `max_memory_gb` settings in `code/src/benchmark/config/modalities/*.yaml`.

### 4.5 Timeout Errors

**Symptom**: `TimeoutError` during task execution.
**Solution**: The default timeout per task is 300 seconds. If a task legitimately requires more time, update the `timeout_per_task` parameter in `code/src/benchmark/config/default.yaml`.

## 5. Running the Full Benchmark

Once verification is complete, you can run the full benchmark.

```bash
# Run with default configuration (Heterogeneous mode)
python code/src/benchmark/run_benchmark.py --config code/src/benchmark/config/default.yaml

# Run in Unified mode (Text-only translation)
python code/src/benchmark/run_benchmark.py --config code/src/benchmark/config/default.yaml --mode unified
```

Results will be saved to:
- `code/data/results.csv`
- `code/data/summary.pdf`
- `code/state/artifact_hashes.yaml` (for integrity tracking)

## 6. Next Steps

- Review `code/research/research.md` for dataset verification details.
- Check `code/specs/001-https-arxiv-org-abs-2604-27351/` for the full specification.
- Run the test suite: `pytest code/tests/`