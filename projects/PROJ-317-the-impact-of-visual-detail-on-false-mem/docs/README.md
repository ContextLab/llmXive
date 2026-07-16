# PROJ-317: The Impact of Visual Detail on False Memory Susceptibility

## Overview
This project implements an automated pipeline to investigate how visual detail in stimuli influences false memory susceptibility. The system generates manipulated images (enhanced and reduced detail), simulates participant interactions, and performs statistical analysis on the resulting data.

## Project Structure
```
.
├── code/ # Source code
│ ├── analysis/ # Statistical analysis and visualization
│ ├── data/ # Data loading and generation utilities
│ ├── participants/ # Participant simulation logic
│ ├── stimuli/ # Image manipulation pipeline
│ ├── utils/ # Shared utilities
│ ├── cli.py # Command-line interface
│ ├── config.py # Configuration management
│ └── requirements.txt # Dependencies
├── data/ # Data storage
│ ├── stimuli/ # Generated and manipulated images
│ ├── stimuli_metadata/ # Metadata for stimuli
│ ├── responses/ # Participant response data
│ ├── processed/ # Processed data for analysis
│ ├── ethics/ # Ethics documentation
│ └── logs/ # Execution logs
├── docs/ # Documentation
│ └── README.md # This file
├── tests/ # Test suite
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
└── specs/ # Feature specifications
```

## Prerequisites
- Python 3.11+
- pip

## Installation
1. Clone the repository
2. Install dependencies:
 ```bash
 cd code
 pip install -r requirements.txt
 ```

## Usage
The project provides a command-line interface for all major operations.

### Stimuli Manipulation
Generate enhanced and reduced detail versions of baseline images:
```bash
python code/cli.py manipulate --input data/stimuli/baseline/ --output data/stimuli/manipulated/
```

### Participant Simulation
Run simulated participant sessions:
```bash
python code/cli.py simulate --config config.yaml --n-sessions 100
```

### Statistical Analysis
Run repeated-measures ANOVA and generate visualizations:
```bash
python code/cli.py analyze --input data/processed/responses.csv --output data/processed/results/
```

## Configuration
Configuration is managed via `code/config.py`. Key parameters include:
- Alpha level (default: 0.05)
- Power target (default: 0.80)
- Effect size (default: medium, Cohen's f=0.25)
- Dataset source (mock or real)

## Ethics
Ethics documentation is stored in `data/ethics/`. This includes:
- Informed consent templates
- IRB approval placeholders
- GDPR compliance notes

See `data/ethics/informed_consent.md` and `data/ethics/irb_placeholder.md` for details.

## Testing
Run the test suite:
```bash
pytest tests/
```

## License
This project is for research purposes only.
