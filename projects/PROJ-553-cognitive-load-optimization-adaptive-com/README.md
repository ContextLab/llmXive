# Cognitive Load Optimization: Adaptive Complexity Scaling for Personalized Learning

## Overview
This project implements an automated science pipeline to optimize cognitive load in personalized learning systems. It trains models to estimate cognitive load from interaction features and generates adaptive explanation tiers to maintain optimal learning difficulty.

## Key Features
- **Cognitive Load Estimation**: Predicts continuous load scores (0–100) using behavioral proxies (latency, errors, hints).
- **Adaptive Complexity**: Generates three tiers of explanation (Simple, Moderate, Complex) validated by Flesch-Kincaid readability scores.
- **Simulation Pipeline**: Compares adaptive vs. static delivery conditions using mixed-effects modeling.

## Requirements
- Python 3.11+
- CPU-only execution (no GPU required)

## Installation
1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Project Structure
```
.
├── code/ # Core implementation modules
├── data/
│ ├── raw/ # Raw downloaded datasets
│ ├── processed/ # Cleaned data and model artifacts
│ ├── explanation_tiers/ # Generated text tiers
│ └── simulation_results/ # Simulation outputs
├── tests/ # Test suite
├── docs/ # Documentation
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Usage
Run the full pipeline:
```bash
python code/run_pipeline.py
```

## Validation
This project relies on a "Golden Set" of expert-labeled interactions for model validation. Ensure `data/processed/golden_set.csv` is populated before running training tasks.

## License
[Insert License]