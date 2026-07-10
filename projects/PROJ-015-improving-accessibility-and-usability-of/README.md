# PROJ-015: Improving Accessibility and Usability of Complex Computer Systems for People with Disabilities

## Overview
This project implements a research pipeline to evaluate the effectiveness of Explainable AI (XAI) interfaces versus traditional interfaces for users with disabilities. The system supports randomized controlled trials, data collection, statistical analysis, and reproducible reporting.

## Features
- **Simulator**: Streamlit-based interface for running usability tests with Traditional and Explainable AI variants.
- **Data Collection**: Automated logging of completion time, error counts, SUS scores, and engagement metrics.
- **Statistical Analysis**: Pipeline for normality testing, ANOVA, and Holm-Bonferroni correction using `scipy`.
- **Visualization**: Publication-quality plots generated via `matplotlib`.
- **Reproducibility**: Single Jupyter notebook (`code/analysis.ipynb`) to reproduce all results from raw data.

## Prerequisites
- Python 3.11+
- pip

## Installation
1. Clone the repository and navigate to the project directory.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Ensure the data directories exist:
 ```bash
 mkdir -p data/raw data/processed figures
 ```

## Usage

### Running the Simulator
Launch the Streamlit application to conduct usability sessions:
```bash
streamlit run code/simulator/app.py
```

### Running the Analysis Pipeline
Execute the full analysis pipeline from raw data to report generation:
```bash
python code/analysis/run_analysis.py
```

### Running the Report Notebook
Open and execute the Jupyter notebook for interactive analysis:
```bash
jupyter notebook code/analysis.ipynb
```

## Project Structure
```
.
├── code/
│ ├── analysis/ # Statistical analysis and visualization modules
│ ├── config/ # Configuration and settings management
│ ├── models/ # Data models (Participant, Session, Metric)
│ ├── simulator/ # Streamlit app and interface logic
│ ├── setup/ # Project initialization scripts
│ └── utils/ # Logging, checksum, and seed utilities
├── data/
│ ├── raw/ # Immutable raw session logs (JSON)
│ └── processed/ # Cleaned data and analysis outputs
├── tests/ # Unit and integration tests
├── docs/ # Documentation
├── requirements.txt # Python dependencies
└── README.md
```

## Configuration
Settings are managed via `code/config/settings.py`. Environment variables can override defaults.

## License
[Insert License Information]
