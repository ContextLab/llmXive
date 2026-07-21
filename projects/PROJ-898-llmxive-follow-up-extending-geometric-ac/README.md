# PROJ-898: llmXive Follow-up: Extending Geometric Action Model for Robot Policy Learning

## Overview
This project extends the Geometric Action Model (GAM) for robot policy learning, focusing on symbolic planning, latent drift detection, and comparative statistical analysis.

## Project Structure
```
projects/PROJ-898-llmxive-follow-up-extending-geometric-ac/
├── code/ # Core implementation modules
│ ├── utils.py
│ ├── config.py
│ ├── gfm_wrapper.py
│ ├── symbolic_solver.py
│ ├── differentiable_solver.py
│ ├── data_generation.py
│ ├── inference_pipeline.py
│ └──...
├── data/ # Data storage (tracked via.gitkeep)
│ ├── raw/ # Raw input data and baseline metadata
│ ├── generated/ # Generated physics states and test sets
│ └── results/ # Experiment results and logs
├── tests/ # Test suites
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── scripts/ # Utility and execution scripts
│ ├── init_project.py # Project initialization script
│ └── generate_test_set.py
├── specs/ # Design documents and specifications
└── README.md
```

## Getting Started

### Initialization
To create the project directory structure and necessary placeholder files:
```bash
python scripts/init_project.py
```

### Prerequisites
- Python 3.11+
- Required dependencies listed in `requirements.txt`

### Running Experiments
See individual script documentation in the `scripts/` directory for execution instructions.

## License
[Internal Use Only]
