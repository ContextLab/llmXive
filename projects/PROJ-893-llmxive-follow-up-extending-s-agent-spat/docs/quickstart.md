# llmXive Follow-up: S-Agent Spatial Reasoning Pipeline - Quickstart

This guide provides instructions for setting up and executing the full symbolic spatial reasoning pipeline against the S-Agent-300K dataset.

## Prerequisites

- Python 3.11+
- pip
- ~14GB disk space (for S-Agent-300K dataset and derived artifacts)
- ~8GB RAM (for streaming dataset processing)

## 1. Environment Setup

Clone the repository and create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r code/requirements.txt
```

## 2. Project Structure Initialization

Ensure the directory structure exists:

```bash
python code/setup_structure.py
```

This creates:
- `code/` - Source code
- `data/raw/` - Raw downloaded datasets
- `data/derived/` - Processed constraints and predictions
- `data/results/` - Benchmark results and reports
- `specs/` - Design documents
- `tests/` - Test suites
- `state/` - Project state tracking

## 3. Full Pipeline Execution

Run the complete pipeline from data download to failure analysis:

```bash
python code/main.py
```

### Pipeline Stages

The pipeline executes the following stages in order:

1. **Download**: Fetches S-Agent-300K subset from HuggingFace
2. **Verify Checksum**: Validates dataset integrity against manifest
3. **Validate Distribution**: Performs KS-tests on object density and spatial variance
4. **Extract Geometry**: Parses constraints, excludes malformed scenes
5. **Solve**: Runs CSP solver on valid scenes
6. **Benchmark**: Compares symbolic solver vs VLM baseline
7. **Analyze Failures**: Classifies failure modes and quantifies semantic gap

### Configuration

Edit `code/config.py` to modify:
- `SAMPLE_SIZE`: Number of scenes to process (default: 1000)
- `RANDOM_SEED`: For reproducibility
- `PATHS`: Data directory locations

## 4. Output Artifacts

After successful execution, the following artifacts are generated:

### Data Artifacts
- `data/derived/constraints.jsonl` - Extracted geometric constraints
- `data/derived/predictions.jsonl` - CSP solver predictions
- `data/derived/latency_log.jsonl` - Per-scene solver latency
- `data/results/exclusion_log.json` - List of excluded/malformed scenes
- `data/results/benchmark_results.csv` - Full benchmark metrics
- `data/results/failure_analysis_report.md` - Failure mode analysis

### State Tracking
- `state/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat.yaml` - Updated with artifact hashes

## 5. Running Individual Components

### Download Data Only
```bash
python code/data/download.py
```

### Run CSP Solver Only
```bash
python code/solver/run_solver.py --config code/config.py
```

### Generate Benchmark Metrics
```bash
python code/benchmark/metrics.py
```

### Analyze Failure Cases
```bash
python code/benchmark/analyze_failures.py
```

## 6. Testing

Run the full test suite:

```bash
pytest tests/ -v
```

Run specific test categories:
```bash
pytest tests/unit/ -v # Unit tests
pytest tests/integration/ -v # Integration tests
```

## 7. Troubleshooting

### Dataset Download Fails
Ensure you have internet access and the HuggingFace token is configured:
```bash
huggingface-cli login
```

### Distribution Validation Gate Fails
The pipeline will abort if the dataset distribution significantly differs from expected. Check `data/derived/validation_report.json` for details.

### Solver Performance Issues
The CSP solver is CPU-only. Ensure you have sufficient RAM for the sample size. Reduce `SAMPLE_SIZE` in `config.py` if memory errors occur.

## 8. Verification

After completion, run hygiene checks to verify all artifacts:

```bash
python code/hygiene.py
```

This updates the state YAML with SHA-256 hashes of all generated files.