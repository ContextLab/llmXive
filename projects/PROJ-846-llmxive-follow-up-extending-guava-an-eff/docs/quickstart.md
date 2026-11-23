# Quickstart Guide: llmXive Guava Follow-up

This guide provides step-by-step instructions to execute the llmXive automated science pipeline for the "Guava" extension project.

## Prerequisites

- Python 3.11 or higher
- pip package manager
- At least 16GB RAM (recommended)
- CPU-only execution is supported; GPU acceleration is optional but triggers a constraint violation flag if used for training.

## 1. Environment Setup

### Initialize the Project

Navigate to the project root and initialize the environment:

```bash
cd projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff

# Verify Python version
python code/check_python_version.py

# Install dependencies
pip install -r code/requirements.txt
```

### Configure Directories

Ensure the data directory structure is created:

```bash
python code/setup_directories.py
```

This creates:
- `data/raw/` (for raw Guava dataset)
- `data/processed/` (for symbolic transformations)
- `data/artifacts/` (for evaluation results)

## 2. Data Ingestion (User Story 1)

### Download Guava Dataset

Fetch the raw Guava dataset. This step will fail loudly if the data source is unreachable.

```bash
python code/data/download_guava.py
```

*Output*: Raw data in `data/raw/guava/` and checksums in `data/raw/guava/checksums.json`.

### Verify Ground Truth

Scan the raw data for ground-truth annotations required for perception validation.

```bash
python code/data/verify_ground_truth.py
```

*Output*: `data/raw/guava/ground_truth_annotations.json`. If missing, the script halts with `GroundTruthSchemaMissingError`.

### Transform to Symbolic Representation

Convert visual frames to symbolic observations using YOLOv8-tiny (ONNX Runtime).

```bash
python code/data/transform_symbolic.py
```

*Output*: Symbolic JSON files in `data/processed/symbolic_guava/{trajectory_id}.json`.

### Validate Perception Pipeline

Check YOLO precision/recall against ground truth and verify latency constraints.

```bash
python code/data/validate_perception.py
```

*Output*: Metrics logged to `data/artifacts/perception_metrics.json`.

## 3. Model Training (User Story 2)

Fine-tune the Phi-3-mini model on the symbolic dataset.

```bash
python code/models/train_llm.py
```

**Note**: This script includes a CPU time constraint check (4 hours). If exceeded, it triggers a GPU escape hatch and logs `cpu_constraint_violated=true` in `data/artifacts/gpu_escape_log.json`.

*Output*: Fine-tuned model weights and training metrics in `data/artifacts/training_metrics.json`.

## 4. Evaluation (User Story 3)

Execute the agents on held-out tasks.

### Symbolic-Guava Agent

```bash
python code/models/inference_symbolic.py
```

*Output*: Outcomes in `data/processed/symbolic_outcomes.json`.

### Baseline-Guava (Visual) Agent

**Critical**: This baseline is required for the primary success criterion (SC-001). If the pre-trained visual model is missing, this script will halt the project.

```bash
python code/models/inference_baseline.py
```

*Output*: Outcomes in `data/processed/baseline_outcomes.json`.

### Oracle-Symbolic Agent (Diagnostic)

```bash
python code/models/inference_oracle.py
```

*Output*: Outcomes in `data/processed/oracle_outcomes.json`.

## 5. Analysis & Reporting

### Categorize Failures

```bash
python code/analysis/failure_categorizer.py
```

*Output*: Categorized outcomes in `data/processed/evaluation_outcomes.json`.

### Flag Latency-Induced Failures

```bash
python code/analysis/latency_failure_flagger.py
```

*Output*: Flagged outcomes and verification in `data/artifacts/latency_exclusion_verified.json`.

### Run Statistical Tests

Perform a permutation test comparing Symbolic-Guava vs. Baseline-Guava.

```bash
python code/analysis/stats_test.py
```

*Output*: P-value and significance declaration in `data/artifacts/stats_results.json`.

### Calculate Semantic Failure Ratio

```bash
python code/analysis/semantic_failure_analyzer.py
```

*Output*: Ratio and research conclusion in `data/artifacts/sc004_verification.json`.

### Generate Final Report

Aggregate all metrics and write the final evaluation results.

```bash
python code/analysis/evaluation_results_generator.py
```

*Output*: Comprehensive results in `data/artifacts/evaluation_results.json`.

## 6. Project State Finalization

Update the project state file with artifact hashes.

```bash
python code/utils/state_manager.py
```

*Output*: `state/PROJ-846-llmxive-follow-up-extending-guava-an-eff.yaml`.

## Troubleshooting

- **Dataset Unavailable**: If `download_guava.py` fails, check your internet connection and the HuggingFace repository status. No synthetic fallback is implemented.
- **Ground Truth Missing**: If `verify_ground_truth.py` fails, ensure the raw Guava dataset contains the required annotation schema.
- **GPU Constraint Violation**: If training exceeds 4 hours on CPU, the system will automatically switch to GPU and log the violation. Primary metrics will be flagged as invalid in the final report.
- **Baseline Missing**: If `inference_baseline.py` fails, the primary research question (SC-001) cannot be answered. The project is designed to halt in this case.