# llmXive: Extending "Guava: An Effective and Universal Harness for Embodied Manipulation"

**Project ID**: PROJ-846
**Status**: Research Pipeline Implementation
**Goal**: Compare a Symbolic-Guava agent (perception via YOLO-tiny + LLM reasoning) against a Baseline-Guava (Visual) agent to evaluate the efficacy of symbolic state abstraction in embodied manipulation.

## 📋 Overview

This project implements a CPU-constrained research pipeline that:
1. **Ingests** raw Guava visual trajectories.
2. **Transforms** them into symbolic states using a lightweight YOLO-tiny ONNX model.
3. **Fine-tunes** a compact LLM (Phi-3-mini) on the symbolic dataset.
4. **Evaluates** the Symbolic-Guava agent against a Baseline-Guava (Visual) agent.
5. **Analyzes** results with statistical rigor (Permutation Tests) to verify research claims.

## 🏗️ Architecture

```
projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/
├── code/ # Source code
│ ├── analysis/ # Statistical analysis & failure categorization
│ ├── data/ # Data ingestion, transformation, validation
│ ├── models/ # LLM training & inference agents
│ ├── utils/ # Logging, config, state management
│ ├── check_python_version.py
│ ├── setup_directories.py
│ └── requirements.txt
├── data/
│ ├── raw/ # Raw Guava dataset (downloaded)
│ ├── processed/ # Symbolic trajectories, evaluation outcomes
│ └── artifacts/ # Logs, metrics, final reports
├── specs/ # Research design documents
├── state/ # Project state hashes (auto-generated)
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ (Strictly enforced)
- CPU-only environment (GPU escape hatch available for training only)
- ~14GB disk space for dataset and artifacts

### 1. Setup Environment

```bash
# Navigate to project root
cd projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff

# Verify Python version
python code/check_python_version.py

# Install dependencies
pip install -r code/requirements.txt
```

### 2. Initialize Project Structure

```bash
# Initialize Git repository
python code/init_git_repo.py

# Setup directory structure (data/raw, data/processed, etc.)
python code/setup_directories.py
```

### 3. Data Ingestion & Transformation (User Story 1)

```bash
# Download Guava dataset (raises error if unavailable)
python code/data/download_guava.py

# Verify Ground Truth annotations exist
python code/data/verify_ground_truth.py

# Transform raw frames to Symbolic Observations (YOLO-tiny + ONNX)
python code/data/transform_symbolic.py

# Validate perception metrics (Precision/Recall/Latency)
python code/data/validate_perception.py
```

### 4. Model Training (User Story 2)

```bash
# Fine-tune Phi-3-mini on symbolic data (LoRA)
# Note: Triggers GPU escape hatch if CPU time > 4h
python code/models/train_llm.py
```

### 5. Evaluation (User Story 3)

```bash
# Run Symbolic-Guava Agent on held-out tasks
python code/models/inference_symbolic.py

# Run Baseline-Guava (Visual) Agent (PRIMARY COMPARISON)
python code/models/inference_baseline.py

# Run Oracle-Symbolic Agent (Secondary Diagnostic)
python code/models/inference_oracle.py
```

### 6. Analysis & Reporting

```bash
# Flag latency-induced failures
python code/analysis/latency_failure_flagger.py

# Filter latency failures from success rate calculation
python code/analysis/latency_filter.py

# Verify exclusion logic
python code/analysis/latency_exclusion_verifier.py

# Categorize failures (Geometric, Semantic, Perception)
python code/analysis/failure_categorizer.py

# Run Permutation Test (Symbolic vs. Visual)
python code/analysis/stats_test.py

# Analyze Semantic Failure Ratio (SC-004)
python code/analysis/semantic_failure_analyzer.py

# Generate Final Evaluation Report
python code/analysis/evaluation_results_generator.py
```

## 📊 Key Outputs

All outputs are generated in `data/artifacts/` and `data/processed/`:

- `data/processed/symbolic_guava/`: Transformed symbolic trajectories.
- `data/artifacts/evaluation_results.json`: Final success rates, step efficiency, p-values.
- `data/artifacts/perception_log.json`: Continuous perception ground-truth log.
- `data/artifacts/sc004_verification.json`: Semantic failure ratio analysis.
- `state/PROJ-846-llmxive-follow-up-extending-guava-an-eff.yaml`: Project state integrity hashes.

## ⚠️ Constraints & Notes

- **CPU-Only**: The pipeline is designed for CPU execution. Training >4h triggers a GPU escape hatch, which will be flagged as a constraint violation in the final report.
- **Data Integrity**: No synthetic data is used. If the Guava dataset or Ground Truth is missing, the pipeline will fail loudly.
- **Baseline Requirement**: The primary research question compares Symbolic-Guava vs. **Baseline-Guava (Visual)**. The Oracle-Symbolic agent is secondary.
- **Latency Handling**: Failures caused by perception latency (>150ms) are flagged and excluded from the primary success rate calculation per FR-008.

## 🧪 Testing

Run the test suite:

```bash
pytest tests/ -v
```

Specific test suites:
- Contract Tests: `tests/contract/`
- Integration Tests: `tests/integration/`
- Unit Tests: `tests/unit/`

## 📚 Documentation

- `specs/`: Research design, user stories, and functional requirements.
- `code/`: Source code with inline documentation.
- `docs/`: (If applicable) Additional API documentation.

## 🤝 Contributing

1. Ensure all tests pass.
2. Verify no synthetic data is introduced.
3. Update `state/` hash after significant changes using `code/utils/state_manager.py`.
4. Adhere to CPU constraints unless explicitly using the GPU escape hatch for training.

## 📄 License

Research Project - Internal Use Only.