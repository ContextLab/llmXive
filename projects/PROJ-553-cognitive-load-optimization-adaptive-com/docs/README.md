# Cognitive Load Optimization: Adaptive Complexity Scaling for Personalized Learning

## Overview

This project implements an adaptive learning system that adjusts the complexity of instructional content based on real-time estimates of a student's cognitive load. The system uses behavioral proxies (latency, errors, hints) to estimate load and generates three tiers of explanation complexity (simple, moderate, complex) to optimize learning efficiency.

## Key Features

- **Cognitive Load Estimation**: Predicts continuous load scores (0-100) from interaction features using Gradient Boosting.
- **Adaptive Complexity**: Generates three textual versions of each instructional unit with validated readability differences.
- **Simulation**: Compares adaptive vs static conditions to measure learning efficiency improvements.
- **Golden Set Validation**: Uses expert-labeled data for model validation to avoid the "illusion of competence".

## Project Structure

```
.
├── code/
│ ├── load_data.py # Data loading and validation
│ ├── train_load_model.py # Cognitive load model training
│ ├── generate_tiers.py # Explanation tier generation
│ ├── simulate_sessions.py # Adaptive vs static simulation
│ ├── analyze_results.py # Statistical analysis
│ └── utils.py # Utility functions
├── data/
│ ├── raw/ # Raw dataset files
│ ├── processed/ # Processed data and models
│ ├── explanation_tiers/ # Generated explanation tiers
│ └── simulation_results/ # Simulation output
├── tests/
│ ├── contract/ # Contract tests
│ └── integration/ # Integration tests
└── docs/
 ├── README.md # This file
 └── research.md # Research documentation
```

## Installation

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

### Running the Full Pipeline

```bash
python code/run_pipeline.py
```

### Generating Explanation Tiers

```bash
python code/generate_tiers.py
```

### Running Tests

```bash
pytest tests/
```

## Data Requirements

- **Golden Set**: Requires `data/processed/golden_set.csv` with expert-labeled interactions.
- **Instructional Units**: Loaded from `data/processed/interaction_data.csv` or similar.

## Validation

- **Model Performance**: Pearson correlation ≥ 0.6 against Golden Set.
- **Tier Progression**: Flesch-Kincaid difference ≥ 5 points between tiers.
- **Fidelity**: Jaccard similarity ≥ 0.85 and semantic similarity ≥ 0.90.

## Limitations

- Self-reported ease is not used as a primary metric due to the risk of the "illusion of competence".
- All findings are framed as associational only; no causal claims are made.
- Requires access to expert-labeled Golden Set data for validation.

## License

MIT License