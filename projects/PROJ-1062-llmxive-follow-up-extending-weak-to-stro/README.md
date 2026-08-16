# llmXive: Weak-to-Strong Generalization via Direct On-Policy Distillation

## Project Overview
This project implements the research pipeline for extending weak-to-strong
generalization using Direct On-Policy Distillation (Direct-OPD) across
different model architectures (Transformer, MoE, SSM).

## Directory Structure
```
.
├── code/ # Source code
│ ├── core/ # Core logic (trainer, evaluator, rewards)
│ ├── data/ # Data loading and preprocessing
│ ├── models/ # Model loaders (Teacher, MoE, SSM)
│ ├── scripts/ # Executable scripts
│ └── tests/ # Unit and integration tests
├── data/ # Data storage
│ ├── raw/ # Raw downloaded datasets
│ └── processed/ # Preprocessed datasets
├── tests/ # Test suite
├── config/ # Configuration files
├── docs/ # Documentation
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Download data: `python code/scripts/download_aime.py`
3. Preprocess: `python code/scripts/preprocess.py`
4. Run experiments: `python code/scripts/run_experiment.py`

## License
MIT License
