# llmXive Follow-up: Extending GateMem Benchmark

This guide provides step-by-step instructions for setting up the environment, downloading the GateMem dataset, and running the initial evaluation pipeline.

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Git (for cloning the repository)
- At least 14GB of available disk space for dataset and intermediate files
- 7GB+ RAM recommended for CPU-only inference

## 1. Project Setup

### Clone and Initialize

```bash
# Clone the repository (replace with actual URL)
git clone
cd llmxive-follow-up-extending-gatemem-benc

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Verify Installation

```bash
# Check Python version
python --version # Should be 3.11+

# Verify key packages
python -c "import torch, datasets, pandas, statsmodels, scipy, pytest; print('All dependencies installed successfully')"
```

## 2. Dataset Download

The GateMem benchmark dataset is hosted on HuggingFace. The following script downloads and validates the dataset.

```bash
# Run the data loader to fetch the dataset
python code/utils/data_loader.py
```

**What this does:**
- Downloads the raw GateMem dataset from HuggingFace (`leak-target` benchmark)
- Saves raw JSONL files to `data/raw/`
- Calculates SHA256 checksums for data integrity
- Records checksums in `state/projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc.yaml`
- Validates the dataset against the schema defined in `contracts/dataset.schema.yaml`

**Expected Output:**
- `data/raw/gatemem_raw.jsonl` (or similar)
- `data/raw/checksums.txt`
- `data/processed/episodes.json` (extracted features)
- Log files in `logs/`

**Note:** If the download fails, the script will raise an error and **will not** fall back to synthetic data. Ensure you have internet connectivity and sufficient disk space.

## 3. Running the First Evaluation

### Quick Start: Access Control Evaluation (User Story 1)

Run the Gatekeeper vs. Baseline comparison on the "medical" and "office" domains:

```bash
python code/cli/run_evaluation.py \
 --domains medical,office \
 --metrics access_control \
 --output data/results/access_control_results.json
```

### Full Pipeline Execution

To run all user stories (Access Control, Utility, Forgetting, and Profiling):

```bash
python code/cli/run_evaluation.py \
 --domains medical,office,education,household \
 --all-metrics \
 --profile \
 --output-dir data/results/
```

**Arguments:**
- `--domains`: Comma-separated list of domains to evaluate (default: all)
- `--metrics`: Specific metric to compute (`access_control`, `utility`, `forgetting`, `latency`, `ram`)
- `--all-metrics`: Run all evaluations
- `--profile`: Enable computational profiling (wall-clock time, peak RAM)
- `--output-dir`: Directory for results (default: `data/results/`)

## 4. Expected Outputs

After running the evaluation, you should find the following artifacts:

### Data Artifacts
- `data/raw/gatemem_raw.jsonl` - Raw dataset
- `data/processed/episodes.json` - Extracted features
- `data/processed/access_control_results.json` - Access Control metrics
- `data/processed/utility_results.json` - Utility and Forgetting metrics
- `data/processed/performance_results.json` - Latency and RAM profiling
- `data/results/cost_comparison.json` - Cost reduction analysis
- `data/samples/failure_cases.json` - Stratified failure case samples

### Reports
- `data/results/final_benchmark_report.md` - Comprehensive benchmark report

### Logs
- `logs/memory_profile.log` - CPU/RAM usage over time
- `logs/deletion_errors.log` - Malformed deletion log entries
- `logs/pipeline.log` - General pipeline execution logs

## 5. Verification

### Contract Tests

Verify that outputs match the expected schemas:

```bash
# Run dataset schema validation
python -m pytest tests/contract/test_dataset_schema.py -v

# Run results schema validation
python -m pytest tests/contract/test_results_schema.py -v
```

### Integration Tests

Run a subset integration test:

```bash
python -m pytest tests/integration/test_us1_integration.py -v
```

## 6. Troubleshooting

### Common Issues

**Issue: "ModuleNotFoundError: No module named 'datasets'"**
- Solution: Ensure virtual environment is activated and run `pip install -r requirements.txt`

**Issue: "CUDA out of memory"**
- Solution: The pipeline is configured for CPU-only. Ensure `torch.cuda.is_available()` is not being forced. Check `code/gatekeeper/classifier.py` for device settings.

**Issue: "Download failed: 404 Not Found"**
- Solution: Verify internet connectivity. The dataset must be fetched from HuggingFace. If the dataset ID has changed, update `code/data/loader.py`.

**Issue: "Validation error: Missing required field"**
- Solution: The dataset schema validation failed. Check `contracts/dataset.schema.yaml` and ensure the downloaded data matches the expected structure.

### Memory Constraints

If you encounter memory issues:
- The pipeline processes data in batches. Ensure at least 7GB RAM is available.
- Reduce the number of domains processed simultaneously.
- Check `logs/memory_profile.log` for peak memory usage.

## 7. Next Steps

After completing the initial evaluation:

1. Review `data/results/final_benchmark_report.md` for comprehensive analysis.
2. Examine `data/samples/failure_cases.json` to understand error patterns.
3. Run the full test suite: `pytest tests/ -v`
4. Explore the statistical analysis in `data/results/cost_comparison.json`.

For detailed implementation notes, refer to the `specs/` directory and the main project documentation.

---

**Project**: PROJ-830-llmxive-follow-up-extending-gatemem-benc
**Task**: T037a - Quickstart Documentation
**Version**: 1.0