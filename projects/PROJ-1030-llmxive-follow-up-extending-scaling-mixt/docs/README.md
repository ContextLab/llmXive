# llmXive: Scaling Mixture-of-Experts Video Pretraining for Embodied Intelligence

## Project Overview

llmXive is a research pipeline for analyzing video data to study physical validity in embodied intelligence scenarios. This project implements a three-stage pipeline:
1. **Feature Extraction**: Extract latent activation vectors and expert masks from pre-trained LingBot-Video models.
2. **Ground-Truth Labeling**: Generate physical validity labels via 3D reconstruction and physics simulation.
3. **Classification**: Train lightweight classifiers to predict physical validity from extracted features.

## Prerequisites

- Python 3.11+
- CPU-only environment (GPU not required for this implementation)
- 7GB+ RAM available
- Internet connection for initial data download

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd llmXive
 ```

2. Create a virtual environment and install dependencies:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r code/requirements.txt
 ```

3. Initialize project structure:
 ```bash
 python code/setup_project_structure.py
 ```

4. Configure pre-commit hooks:
 ```bash
 python code/setup_precommit.py
 ```

## Quickstart

Run the complete pipeline with a single command:

```bash
python code/main_pipeline.py
```

This will:
1. Download the LingBot-Video model weights (if not already present)
2. Extract features from video clips
3. Generate physical validity labels via 3D reconstruction and simulation
4. Train and evaluate a classifier
5. Generate all reports and artifacts

Expected runtime: ~2 hours on a standard CPU machine with 7GB+ RAM.

## Project Structure

```
llmXive/
├── code/ # Source code
│ ├── extraction/ # Feature extraction modules
│ ├── labeling/ # Label generation modules
│ ├── classification/ # Classifier training and evaluation
│ ├── utils/ # Utility functions (memory management, logging, etc.)
│ ├── models/ # Data models
│ ├── extract_features.py
│ ├── generate_labels.py
│ ├── main_pipeline.py
│ └──...
├── data/
│ ├── raw/ # Raw input data (video manifests, sample lists)
│ ├── processed/ # Processed artifacts (features, labels, reports)
│ ├── external/ # External models (LingBot-Video weights)
│ └──.checksums.json # Artifact checksums
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── docs/ # Documentation
│ ├── README.md # This file
│ ├── usage_guide.md # Detailed usage instructions
│ └── results_report.md # Final results report
├── state/ # Pipeline state and manifests
│ └── manifest.yaml # Artifact manifest with SHA-256 hashes
└── requirements.txt # Python dependencies
```

## Output Artifacts

After successful pipeline execution, the following artifacts are generated:

### Data Artifacts (`data/processed/`)
- `features.npy`: Extracted latent vectors and expert masks
- `labels.csv`: Physical validity labels with confidence scores
- `null_labels.csv`: Samples excluded due to low confidence or simulation failure
- `classifier.pkl`: Trained classifier model
- `evaluation_metrics.json`: Performance metrics (F1, precision, recall)
- `feature_importance.json`: SHAP values and permutation importance
- `pipeline_run_summary.json`: Overall pipeline execution summary

### Documentation
- `docs/results_report.md`: Final results with associational framing
- `shap_interpretation.md`: Human-readable interpretation of feature importance

### State
- `state/manifest.yaml`: SHA-256 hashes of all artifacts for reproducibility

## Configuration

Environment configuration is managed through `data/.env` (create from template if needed):

```bash
# HuggingFace token for model downloads (optional)
HF_TOKEN=your_token_here

# Memory limits (in GB)
MAX_MEMORY_GB=7

# Sampling strategy
SAMPLE_SIZE=100
```

## Running Specific Pipeline Stages

### Feature Extraction Only
```bash
python code/extract_features.py
```

### Label Generation Only
```bash
python code/generate_labels.py
```

### Classifier Training Only
```bash
python code/classification/train_classifier.py
```

## Testing

Run unit tests:
```bash
pytest tests/unit/ -v
```

Run integration tests:
```bash
pytest tests/integration/ -v
```

## Contributing

1. Ensure code passes linting (`ruff check.`) and formatting (`black.`)
2. Write tests for new functionality
3. Update documentation as needed
4. Submit a pull request

## License

[Insert license information]

## Acknowledgments

This project builds on:
- LingBot-Video: Pre-trained video understanding model
- MonoDepth2: Monocular depth estimation
- PyBullet: Physics simulation engine
- HuggingFace Datasets: Dataset management
- SHAP: Feature importance analysis
