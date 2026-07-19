# llmXive: Extending DanceOPD On-Policy Generative Field Distillation

## Project Overview

This project implements a follow-up study to the "DanceOPD: On-Policy Generative Field Distillation" paper. The goal is to generate a synthetic dataset of teacher routing ground truth, train static decision trees to approximate expert routing, and quantify the fidelity degradation of using these trees compared to the full teacher model.

The pipeline is designed to run on CPU-only CI environments with strict resource constraints (≤7GB RAM, ≤6 hours runtime).

## Project Structure

```
.
├── code/ # Source code
│ ├── utils/ # Utility modules (config, metrics, statistics, etc.)
│ ├── models/ # Model definitions and inference logic
│ ├── 00_data_generation.py # Data streaming and teacher inference
│ ├── 01_train_trees.py # Decision tree training
│ ├── 02_evaluate_fidelity.py # Fidelity evaluation and statistical testing
│ ├── 03_versioning.py # Artifact versioning and checksumming
│ └── main.py # Entry point for the pipeline
├── data/ # Data storage
│ ├── raw/ # Raw downloaded data (ImageNet, LAION samples)
│ ├── processed/ # Processed datasets (teacher routing dataset)
│ └── results/ # Evaluation results, metrics, and reports
├── models/ # Trained decision tree models
├── tests/ # Unit and integration tests
├── specs/ # Design documents and JSON schemas
│ └── contracts/ # Data contracts (JSON schemas)
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Prerequisites

- Python 3.11+
- pip
- At least 7GB available RAM
- (Optional) GPU for teacher inference (CPU fallback requires pre-computed ground truth)

## Installation

1. Clone the repository and navigate to the project directory.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Quickstart

### 1. Setup and Configuration

Ensure the project directory structure is created:
```bash
python code/setup_data_dirs.py
```

Configure hyperparameters and paths in `code/utils/config.py` or via environment variables.

### 2. Data Generation (User Story 1)

Stream samples from ImageNet-1K and LAION-400M, run teacher inference, and extract features:
```bash
python code/00_data_generation.py
```
This produces:
- `data/raw/imageNet_samples.parquet`
- `data/raw/laion_samples.parquet`
- `data/processed/teacher_routing_dataset.parquet`

**Note**: If GPU is unavailable, ensure a verified `data/raw/teacher_ground_truth.parquet` exists (see T013a fallback logic).

### 3. Train Decision Trees (User Story 2)

Train decision trees with varying `max_depth` (2 to 20):
```bash
python code/01_train_trees.py
```
This produces:
- `models/trained_trees/` (individual tree models)
- `data/results/tree_accuracy.csv`

### 4. Evaluate Fidelity (User Story 3)

Generate images using tree-predicted routing vs. teacher routing, compute FID/CLIP, and perform statistical tests:
```bash
python code/02_evaluate_fidelity.py
```
This produces:
- `data/results/fidelity_metrics.csv`
- `data/results/statistical_tests.json`
- `data/results/fidelity_summary.md`
- `data/results/` (generated images)

### 5. Versioning

Calculate checksums and update state for all artifacts:
```bash
python code/03_versioning.py
```

## Data Integrity

- All input data is sourced from real datasets (ImageNet-1K, LAION-400M) via Hugging Face datasets.
- No synthetic or placeholder data is used.
- If real data fetching fails, the pipeline aborts with a clear error (no silent fallbacks).

## Statistical Testing

The pipeline includes:
- Bootstrap hypothesis tests for FID distribution
- Paired t-tests for per-sample CLIP scores
- Power analysis with runtime limits (max 6 hours)
- Partial result saving if statistical power is insufficient

## Testing

Run unit tests:
```bash
pytest tests/unit/
```

Run integration tests:
```bash
pytest tests/integration/
```

## Contributing

1. Ensure all tasks are completed according to `tasks.md`.
2. Run `quickstart.md` validation for end-to-end reproducibility.
3. Add unit tests for new functionality.
4. Update documentation as needed.

## License

[Insert License Information]

## Acknowledgments

- DanceOPD authors for the original work
- Hugging Face for datasets and transformers
- PyTorch and scikit-learn communities
