# llmXive Follow-up: Extending PerceptionDLM Parallel Region Perception

**Project ID**: PROJ-833
**Status**: Active Research

## Overview
This project investigates the limits of parallel perception in large multimodal models by generating synthetic datasets with varying region counts (20-50) and comparing parallel inference against sequential context-reset baselines using PerceptionDLM.

## Research Question
Does semantic coherence degrade non-linearly as the number of simultaneous regions exceeds the model's effective context window, and where is the tipping point?

## Directory Structure
```
projects/PROJ-833-llmxive-follow-up-extending-perceptiondl/
├── code/ # Implementation modules
│ ├── config.py # Configuration and paths
│ ├── main.py # Orchestration script
│ ├── synthetic/ # Data generation logic
│ ├── models/ # Model runners
│ ├── metrics/ # Evaluation metrics
│ └── analysis/ # Regression and plotting
├── data/ # Data storage
│ ├── raw/ # Original dataset samples
│ ├── synthetic/ # Generated images and annotations
│ └── processed/ # Inference results and metrics
├── tests/ # Test suite
│ ├── unit/
│ ├── integration/
│ └── contract/
├── specs/ # Feature specifications
├── docs/ # Design decisions and reports
└── requirements.txt # Python dependencies
```

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Run full pipeline: `python code/main.py`
3. View results: `data/processed/degradation_curve.csv` and `data/processed/pareto_frontier.png`

## Key Constraints
- **Model**: PerceptionDLM (same model for parallel and sequential baselines)
- **Precision**: FP32/FP16 on CPU (no quantization)
- **Data**: Real COCO-Stuff/ParaDLC-Bench samples via HuggingFace
- **Memory**: Adaptive reduction if Peak RSS > 7GB
- **Statistics**: Bonferroni correction applied to regression tests

## References
- Plan Summary: PROJ-833 Plan
- Feature Spec: specs/001-llmxive-follow-up-extending-perceptiondl
