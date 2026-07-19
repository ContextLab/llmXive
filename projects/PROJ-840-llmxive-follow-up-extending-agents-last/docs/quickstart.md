# llmXive Automated Science Pipeline: Quick Start Guide

This guide provides a step-by-step walkthrough to set up, run, and validate the
llmXive automated science pipeline for the "Agents' Last Exam" (ALE) extension.

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- At least 14GB of free disk space
- At least 7GB of available RAM

## 1. Project Setup

The project structure is defined in `specs/001-llmxive-ale-extension/plan.md`.
Run the setup script to create the necessary directories:

```bash
cd PROJ-840-llmxive-follow-up-extending-agents-last
python code/setup_project.py
```

This creates the following structure:
- `code/`: Source code modules
- `tests/`: Unit and integration tests
- `data/`: Raw and processed data files
- `docs/`: Documentation
- `specs/`: Feature specifications

## 2. Environment Configuration

Install the required dependencies:

```bash
pip install -r requirements.txt
```

**Required Dependencies**:
- `llama-cpp-python`: For local LLM inference
- `datasets`: For data loading and processing
- `scikit-learn`: For statistical analysis
- `pandas`: For data manipulation
- `pyyaml`: For configuration loading
- `pytest`: For testing
- `statsmodels`: For advanced statistical tests

Configure your environment variables (optional but recommended):

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/code"
```

## 3. Configuration

The pipeline uses a YAML configuration file located at `code/utils/config_schema.yaml`.
Key configuration sections include:

- **ModelConfig**: Path to the local LLM checkpoint (Q4_K_M quantized)
- **CheckpointConfig**: Interval N for context checkpointing
- **DataPathsConfig**: Paths to raw and processed data directories
- **NormalizationConfig**: Float tolerance (default: 1e-6)
- **StatsConfig**: Parameters for statistical significance testing

Example configuration snippet:

```yaml
model:
 path: "models/llama-7b-q4_k_m.gguf"
 quantization: "Q4_K_M"

checkpoint:
 interval_n: 3 # Regenerate state summary every N steps

data:
 raw_dir: "data/raw"
 processed_dir: "data/processed"

normalization:
 float_tolerance: 1.0e-6
```

## 4. Running the Pipeline

The pipeline consists of three main user stories that can be executed independently.

### Phase 1: Data Generation (US1 Prerequisite)

Generate synthetic ALE execution traces with known ground truth:

```bash
python code/data/generator.py
```

This produces `data/raw/golden_subset.json` containing traces with verified failure modes.
The generator uses deterministic seed pinning (T004) and verifies pairing (T004b) to
ensure reproducibility.

### Phase 2: Failure Mode Classification (US1)

Parse logs, reconstruct state, and classify failures:

```bash
# Step 1: Validate state reconstruction (Gate T013b)
python code/classification/state_validator.py

# Step 2: Run semantic classification
python code/classification/semantic_classifier.py

# Step 3: Generate classification report
python code/classification/report_generator.py
```

The classifier uses a local LLM (Q4_K_M) with deterministic seed pinning to label
failures as either "State Persistence Error" or "Reasoning Deficit".

### Phase 3: Context Checkpointing Intervention (US2)

Run baseline and intervention experiments:

```bash
# Run baseline tasks (no wrapper)
python code/intervention/runner.py --mode baseline

# Run intervention tasks (with checkpointing wrapper)
python code/intervention/runner.py --mode intervention --interval 3
```

Results are saved to:
- `data/processed/baseline_results.json`
- `data/processed/intervention_results.json`

### Phase 4: Statistical Analysis & Reporting (US3)

Perform statistical significance testing and generate the final report:

```bash
# Run McNemar's test and calculate pass rates
python code/analysis/stats.py

# Run sensitivity analysis for N=1, N=3, N=5
python code/analysis/sensitivity.py

# Generate final report
python code/analysis/report_generator.py
```

The final report is saved to `docs/report.md` and includes:
- Pass rates for baseline vs. intervention
- McNemar's test p-value
- Sensitivity analysis across different checkpoint intervals
- Bonferroni/FDR corrected significance values

## 5. Validation

Validate the entire quickstart process:

```bash
python code/validate_quickstart.py
```

This script checks:
- Directory structure integrity
- Requirements installation
- Pyproject.toml configuration
- Seed utility functionality
- Configuration loading
- Module imports
- Data generation and file creation

## 6. Testing

Run the test suite to verify all components:

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Full test suite
pytest tests/ -v
```

Key tests include:
- T008/T009: Parser normalization and classification accuracy on golden set
- T017/T018: Checkpoint injection and memory limit compliance
- T024/T025: Statistical significance and sensitivity analysis

## 7. Troubleshooting

### Common Issues

**Issue**: `ImportError: No module named 'llama_cpp'`
**Solution**: Ensure `llama-cpp-python` is installed with GPU support if needed:
```bash
pip install llama-cpp-python --force-reinstall --no-cache-dir
```

**Issue**: `FileNotFoundError: data/raw/golden_subset.json`
**Solution**: Run the data generator first:
```bash
python code/data/generator.py
```

**Issue**: `State Reconstruction Accuracy < 0.95`
**Solution**: The pipeline will halt at T013b. Check:
- Normalization tolerance (default: 1e-6)
- Seed pairing verification (T004b)
- Golden subset generation completeness

**Issue**: Memory usage exceeds 7GB
**Solution**: Ensure Q4_K_M quantization is used and context window limits are enforced
in `code/intervention/wrapper.py`.

## 8. Output Artifacts

After successful execution, the following artifacts will be available:

| Artifact | Path | Description |
|----------|------|-------------|
| Golden Subset | `data/raw/golden_subset.json` | Synthetic traces with ground truth |
| Baseline Results | `data/processed/baseline_results.json` | Pass/fail outcomes without intervention |
| Intervention Results | `data/processed/intervention_results.json` | Pass/fail outcomes with checkpointing |
| Classification Report | `data/processed/classification_report.json` | Failure mode breakdown |
| Statistical Report | `data/processed/stats_report.json` | McNemar's test results |
| Final Report | `docs/report.md` | Comprehensive analysis summary |

## 9. Next Steps

- Review the final report in `docs/report.md`
- Analyze sensitivity results to determine optimal checkpoint interval
- Extend the pipeline with additional user stories as defined in `specs/`
- Contribute to the project by implementing remaining tasks (T034, T035)

For more details, refer to the feature specifications in `specs/001-llmxive-ale-extension/`.
