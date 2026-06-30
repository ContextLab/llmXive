# Quickstart Guide

This guide provides the instructions to set up the **Heterogeneous Scientific Foundation Model Collaboration Benchmark** project and run the benchmark.

## 1. Prerequisites

- **Python**: Version 3.11 or higher is required.
- **System**: Linux, macOS, or Windows (WSL2 recommended).
- **Memory**: Minimum 4GB RAM (8GB recommended for full benchmark runs).
- **Disk**: At least 2GB of free space for dependencies and datasets.

## 2. Setup Commands

Follow these steps to clone the repository, create a virtual environment, and install dependencies.

### 2.1 Clone the Repository

```bash
git clone
cd PROJ-573-https-arxiv-org-abs-2604-27351
```

### 2.2 Create Virtual Environment

```bash
python3.11 -m venv.venv
source.venv/bin/activate # On Windows:.venv\Scripts\activate
```

### 2.3 Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Verification Steps

Ensure the installation was successful by running the following checks.

### 3.1 Verify CLI Help

Run the main benchmark script with the help flag to ensure the entry point is registered correctly.

```bash
python code/src/benchmark/run_benchmark.py --help
```

Expected output should list arguments like `--config`, `--mode`, and `--seeds`.

### 3.2 Verify Data Directory

Ensure the required data directories exist. The project structure expects the following:

```bash
ls -la code/data/
ls -la code/data/processed/
```

If directories are missing, the setup script `code/setup_project_structure.py` can be run to create them:

```bash
python code/setup_project_structure.py
```

### 3.3 Verify Configuration Loading

Run a dry-run of the benchmark to verify that the default configuration loads without errors.

```bash
python code/src/benchmark/run_benchmark.py --config code/src/benchmark/config/default.yaml
```

*Note: This command may fail if datasets are not yet downloaded (see Phase 0 tasks), but it should not fail due to missing configuration files or syntax errors.*

## 4. Troubleshooting Common Issues

### 4.1 `ModuleNotFoundError`

If you see errors like `ModuleNotFoundError: No module named 'src'`, ensure you are running commands from the project root (`code/`) and that the virtual environment is activated.

**Solution:**
```bash
cd code
source.venv/bin/activate
python -m src.benchmark.run_benchmark --help
```

### 4.2 `FileNotFoundError` for Config

If the benchmark fails to find `default.yaml`:

1. Verify the file exists at `code/src/benchmark/config/default.yaml`.
2. Ensure the path passed to `--config` is relative to the `code/` directory.

### 4.3 Dataset Download Failures

If the benchmark fails during the dataset download phase:

1. Check your internet connection.
2. Ensure you have sufficient disk space.
3. Verify the dataset availability by running the verification scripts in `code/src/research/`.

### 4.4 TaskRunner Initialization Errors

If you encounter `TypeError: TaskRunner.__init__() got an unexpected keyword argument`:

This indicates a mismatch between the caller and the `TaskRunner` definition. Ensure you are using the latest version of `code/src/tasks/task_runner.py` which includes a tolerant `__init__` signature accepting `**kwargs`.

### 4.5 YAML Parsing Errors

If you see `yaml.scanner.ScannerError`:

1. Open the failing YAML file (e.g., `task_definitions.yaml`).
2. Check for indentation inconsistencies or unquoted strings that look like special characters.
3. Run `python -c "import yaml; yaml.safe_load(open('path/to/file'))"` to validate syntax.

## 5. Next Steps

Once verification is complete, proceed to **Phase 0: Research & Dataset Verification** to ensure all required datasets and models are available before running the full benchmark.

For detailed task lists and user stories, refer to `tasks.md`.