# Quickstart: The Influence of Simulated Social Status on Risk-Taking Behavior

## I. Prerequisites

*   Python 3.11 installed.
*   `pip` package manager.
*   Access to a Linux environment (e.g., GitHub Actions runner).

## II. Installation

1.  Clone the repository: `git clone <repository_url>`
2.  Navigate to the project directory: `cd <project_directory>`
3.  Create and activate a virtual environment:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
4.  Install dependencies: `pip install -r requirements.txt`

## III. Data Preparation

1. Choose either simulation or meta-analysis (see `research.md`).
2. If simulating data, run the script to generate the dataset: `python src/data_simulation.py` (or modify if necessary).
3. If performing a meta-analysis, ensure you have access to the required datasets and adapt the analysis scripts accordingly.

## IV. Running the Analysis

1. Execute the main analysis script: `python src/analysis.py`
2. The results will be saved in the `data/processed/` directory.
3. Generate the report: `python src/report_generation.py`

## V. Troubleshooting

*   If you encounter errors during installation, ensure that all dependencies are correctly installed and compatible with your Python version.
*   If the analysis fails, check the error messages for clues about the problem.
*   Refer to the documentation (`research.md`, `data-model.md`) for more detailed information about the data processing and analysis steps.
