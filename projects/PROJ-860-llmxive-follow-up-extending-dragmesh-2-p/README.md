# llmXive Follow-up: Virtual Tactile Zero-Shot Adaptation

**Project ID**: PROJ-860-llmxive-follow-up-extending-dragmesh-2-p

## Overview
This project implements an adaptive reinforcement learning pipeline for robotic manipulation that utilizes virtual tactile sensing to estimate friction coefficients ($k_{est}$) in real-time. The system dynamically adjusts reward functions to improve success rates on novel, unseen objects with varying friction properties, specifically targeting high-friction scenarios where static baselines fail.

## Key Features
- **Virtual Tactile Estimator**: Real-time friction estimation using torque/velocity ratios with moving average filtering.
- **Adaptive Reward Scheduler**: Dynamic adjustment of detachment and contact rewards based on estimated stiffness.
- **Zero-Shot Adaptation**: Ability to generalize to novel geometries and friction coefficients without retraining.
- **CPU-Only Execution**: Optimized for CPU-only environments (no CUDA required) to ensure accessibility on standard hardware.

## Project Structure
```
.
├── code/ # Source code
│ ├── environment.py # PyBullet physics environment setup
│ ├── estimator.py # VirtualTactileEstimator implementation
│ ├── scheduler.py # AdaptiveRewardScheduler logic
│ ├── generator.py # Novel object geometry generation
│ ├── train.py # Training loop with adaptive rewards
│ ├── evaluate.py # Evaluation and comparison scripts
│ ├── aggregate.py # Data aggregation utilities
│ ├── analysis.py # Statistical analysis (t-tests)
│ └──... # Other utilities and scripts
├── data/
│ ├── raw/ # Raw dataset files (DragMesh-2)
│ ├── generated/ # Generated novel object geometries
│ └── results/ # Evaluation logs and benchmark metrics
├── state/
│ └── projects/ # Project state tracking and checksums
├── tests/ # Unit and integration tests
├── README.md # This file
└── requirements.txt # Python dependencies (in code/)
```

## Prerequisites
- Python 3.8+
- CPU-only environment (CUDA not supported)
- Git

## Installation
1. Clone the repository and navigate to the project directory.
2. Install dependencies:
 ```bash
 cd code
 pip install -r requirements.txt
 ```

## Usage
### Generate Novel Objects
```bash
python code/generator.py --count 30 --seed 42 --friction-min 0.1 --friction-max 2.0 --output data/generated/
```

### Train Adaptive Policy
```bash
python code/train.py --epochs 100 --log-interval 10
```

### Evaluate Policies
```bash
python code/evaluate.py --objects data/generated/ --policy adaptive
python code/evaluate.py --objects data/generated/ --policy static
```

### Run Full Benchmark
```bash
python code/benchmark_runner.py --output data/results/benchmark_metrics.json
```

### Statistical Analysis
```bash
python code/aggregate.py --input data/results/eval_logs.csv --output data/results/aggregated.csv
python code/analysis.py --input data/results/aggregated.csv
```

## Verification
- **Unit Tests**: Run `pytest tests/unit/`
- **Integration Tests**: Run `pytest tests/integration/`
- **Citation Validation**: Run `python code/validate_citations.py`

## License
This project is part of the llmXive research initiative. See LICENSE for details.
