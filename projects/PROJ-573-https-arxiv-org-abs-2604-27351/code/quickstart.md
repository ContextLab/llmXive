# Quickstart Guide

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- git (for cloning the repository)
- At least 5GB of free disk space for datasets and models
- 4 CPU cores recommended for parallel benchmark execution

## Setup Commands

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <project-directory>
```

### 2. Create and Activate Virtual Environment

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

The `requirements.txt` file contains pinned versions of all required packages:
- scikit-learn>=1.3.0
- pandas>=2.0.0
- numpy>=1.24.0
- pyyaml>=6.0
- datasets>=2.14.0
- scipy>=1.11.0
- matplotlib>=3.7.0
- reportlab>=4.0.0
- requests>=2.31.0

### 4. Verify Installation

```bash
python src/benchmark/run_benchmark.py --help
```

You should see the CLI help message with available arguments:
- `--config`: Path to configuration file (default: src/benchmark/config/default.yaml)
- `--mode`: Execution mode (heterogeneous|unified, default: heterogeneous)
- `--seeds`: Number of random seeds for reproducibility (default: 5)

### 5. Check Data Directory

Verify that the `data/` directory structure exists:

```bash
ls -la data/
ls -la data/processed/
```

The directory should contain:
- `data/`: For downloaded raw datasets
- `data/processed/`: For processed dataset files
- `data/statistical_summary.yaml`: For aggregated results

## Running the Benchmark

### Default Execution (Heterogeneous Mode)

```bash
python src/benchmark/run_benchmark.py
```

This will:
1. Load the default configuration from `src/benchmark/config/default.yaml`
2. Execute tasks for each modality using specialized models
3. Generate results in `results.csv` and `summary.pdf`

### Unified Mode (Text-Only Translation)

```bash
python src/benchmark/run_benchmark.py --mode unified
```

This will:
1. Translate all modalities to text representations
2. Process everything through a single LLM
3. Generate results with unified approach metrics

### Custom Configuration

```bash
python src/benchmark/run_benchmark.py --config path/to/custom.yaml
```

### Single Task Execution

```bash
python src/benchmark/run_task.py --task-id T001
```

## Troubleshooting Common Issues

### Issue: "No module named 'datasets'"

**Solution**: Ensure you're in the virtual environment and run:
```bash
pip install datasets>=2.14.0
```

### Issue: Dataset download fails with timeout

**Solution**: The download function has 3-retry logic with 300s timeout. If it still fails:
1. Check your internet connection
2. Verify the dataset URL is accessible
3. Try downloading manually using `wget` or browser
4. Check HuggingFace status page for service outages

### Issue: "Model weights exceed 1GB limit"

**Solution**: This project enforces CPU-tractable models (<1GB). If you encounter this:
1. Verify you're using the correct model IDs from `src/benchmark/config/modalities/`
2. Check `src/research/verify_models.py` for model size validation
3. Ensure you haven't accidentally downloaded larger model variants

### Issue: Statistical tests fail with "empty arrays"

**Solution**: This occurs when task execution returns no results. Check:
1. Task definitions in `src/tasks/task_definitions.yaml` are valid
2. All required datasets are downloaded and accessible
3. Model inference completes successfully (check logs)

### Issue: Permission errors when writing to data/

**Solution**: Ensure proper directory permissions:
```bash
chmod -R u+rwX data/
```

### Issue: "Config file not found"

**Solution**: Verify the config path is correct and the file exists:
```bash
ls -la src/benchmark/config/default.yaml
```

### Issue: Reproducibility issues across runs

**Solution**: The benchmark supports multiple seeds for reproducibility:
```bash
python src/benchmark/run_benchmark.py --seeds 5
```
Results will be aggregated in `data/statistical_summary.yaml` with confidence intervals.

### Issue: Memory errors during inference

**Solution**: All models are designed to be <1GB, but ensure:
1. You have at least 4GB available RAM
2. Close other memory-intensive applications
3. Consider running tasks sequentially instead of in parallel

## Next Steps

After successful setup:

1. Review the data model in `data-model.md` to understand entity relationships
2. Check `research.md` for dataset verification status and methodology
3. Examine `contracts/` for schema definitions
4. Run the full benchmark and review generated reports

For detailed implementation notes, see:
- `src/models/` for modality-specific model wrappers
- `src/evaluation/` for metrics and statistical analysis
- `src/benchmark/` for orchestration logic
- `src/tasks/` for task definitions and runner

## Support

For issues not covered here, check:
- `src/research/verify_models.py` for model verification
- `src/utils/logging.py` for detailed execution logs
- `state/projects/PROJ-573-https-arxiv-org-abs-2604-27351.yaml` for artifact tracking
- `data/statistical_summary.yaml` for aggregated results
