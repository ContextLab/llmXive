# Cognitive Load Optimization: Adaptive Complexity Scaling

## Project Overview

This project implements an adaptive learning system that adjusts the complexity of instructional content based on real-time estimates of a learner's cognitive load. The system aims to optimize learning efficiency by presenting material at an appropriate difficulty level, avoiding both under-challenge and cognitive overload.

## Architecture

The pipeline consists of three main components:

1. **Cognitive Load Estimation Model** (User Story 1): Predicts continuous load scores (0–100) from behavioral interaction features (latency, errors, hints).
2. **Explanation Tier Generation** (User Story 2): Produces three textual complexity tiers (simple, moderate, complex) for each instructional unit.
3. **Adaptive Simulation & Analysis** (User Story 3): Simulates learning sessions under adaptive vs. static conditions and evaluates learning efficiency using mixed-effects modeling.

## Data Sources

- **Primary Data**: Public educational datasets (ASSISTments, OULAD) loaded via HuggingFace `datasets` library.
- **Validation Data**: A "Golden Set" of expert-labeled interactions (`data/processed/golden_set.csv`) used to validate the cognitive load model.

## Constitutional Conflict & Deviation Statement

**⚠️ CRITICAL NOTICE: Deviation from Constitution Principle VI**

This project explicitly deviates from **Constitution Principle VI**, which mandates the use of the NASA-TLX (National Aeronautics and Space Administration - Task Load Index) for cognitive load validation.

Instead, this implementation relies on a **"Golden Set" path** for validation:
- **Method**: Validation is performed against a dataset of expert-labeled interactions (`data/processed/golden_set.csv`), where experts have rated the cognitive load of specific student interactions.
- **Rationale**: Direct NASA-TLX administration in a high-frequency, real-time adaptive learning loop is often impractical due to survey fatigue and disruption of the learning flow. The Golden Set approach allows for offline validation of behavioral proxies (latency, errors, hints) against expert judgment.
- **Limitation**: This approach assumes that the expert-labeled Golden Set is representative of the broader population and that the behavioral proxies correlate sufficiently with the subjective load measures NASA-TLX would capture.
- **Action Required**: **Human Review Required**. Before accepting research findings or deploying this system, a human reviewer must explicitly acknowledge this deviation, assess the validity of the Golden Set, and determine if the reliance on behavioral proxies is sufficient for the intended research goals.

See `docs/research.md` for a detailed discussion of this deviation and the "illusion of competence" critique.

## Quick Start

1. **Setup**:
 ```bash
 pip install -r requirements.txt
 ```

2. **Data Preparation**:
 Run the data loading and Golden Set verification pipeline:
 ```bash
 python code/load_data.py
 ```
 *Note: If `data/processed/golden_set.csv` is missing, the pipeline will halt unless `code/create_golden_set.py` is run to generate a synthetic expert-labeled dataset based on the defined rubric (T006b).*

3. **Model Training**:
 ```bash
 python code/train_load_model.py
 ```

4. **Tier Generation**:
 ```bash
 python code/generate_tiers.py
 ```

5. **Simulation & Analysis**:
 ```bash
 python code/run_pipeline.py
 ```

## Directory Structure

```
.
├── code/
│ ├── load_data.py
│ ├── create_golden_set.py
│ ├── train_load_model.py
│ ├── generate_tiers.py
│ ├── simulate_sessions.py
│ ├── analyze_results.py
│ ├── run_pipeline.py
│ └── utils.py
├── data/
│ ├── raw/
│ ├── processed/
│ │ ├── golden_set.csv
│ │ └── load_model.pkl
│ ├── explanation_tiers/
│ └── simulation_results/
├── docs/
│ ├── README.md
│ └── research.md
└── tests/
```

## License

[Insert License]
