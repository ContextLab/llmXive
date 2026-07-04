# Cognitive Load Optimization: Adaptive Complexity Scaling for Personalized Learning

## Overview
This project implements an adaptive learning system that optimizes instructional content complexity
based on real-time cognitive load estimation. The system uses behavioral proxies (latency, errors, hints)
to estimate cognitive load and adjusts explanation complexity accordingly.

## Features
- Cognitive Load Estimation Model using Gradient Boosting
- Adaptive Complexity Tier Generation (Simple, Moderate, Complex)
- Simulation of Adaptive vs Static Learning Conditions
- Mixed-Effects Modeling for Learning Efficiency Analysis

## Project Structure
```
PROJ-553-cognitive-load-optimization-adaptive-com/
├── data/
│ ├── raw/ # Raw datasets from HuggingFace
│ ├── processed/ # Processed data and models
│ ├── explanation_tiers/ # Generated explanation tiers
│ └── simulation_results/ # Simulation outputs
├── code/
│ ├── load_data.py # Data loading and verification
│ ├── train_load_model.py # Model training pipeline
│ ├── generate_tiers.py # Explanation tier generation
│ ├── simulate_sessions.py # Session simulation
│ ├── analyze_results.py # Statistical analysis
│ └── utils.py # Utility functions
├── tests/ # Test suite
├── docs/ # Documentation
└── requirements.txt # Python dependencies
```

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
# Load and verify datasets
python code/load_data.py

# Train cognitive load model
python code/train_load_model.py

# Generate explanation tiers
python code/generate_tiers.py

# Run simulation
python code/simulate_sessions.py

# Analyze results
python code/analyze_results.py
```

## Key Concepts
- **Cognitive Load**: Estimated from behavioral proxies (latency, errors, hints)
- **Adaptive Complexity**: Adjusts explanation difficulty based on load estimates
- **Golden Set**: Expert-labeled dataset for model validation
- **Hysteresis Controller**: Prevents premature simplification in adaptive mode

## License
MIT License
