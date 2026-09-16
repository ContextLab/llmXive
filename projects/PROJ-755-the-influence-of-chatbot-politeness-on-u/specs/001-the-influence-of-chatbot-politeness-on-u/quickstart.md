# Quickstart: Chatbot Politeness and User Trust

## Prerequisites

*   Python 3.11
*   GitHub Actions account
*   Access to the Persona-Chat and EmpatheticDialogues datasets on Hugging Face Datasets.

## Installation

1.  Clone the repository: `git clone <repository_url>`
2.  Navigate to the project directory: `cd <project_directory>`
3.  Create a virtual environment: `python3 -m venv venv`
4.  Activate the virtual environment: `source venv/bin/activate`
5.  Install dependencies: `pip install -r requirements.txt`

## Running the Analysis

1.  Execute the main script: `python src/main.py` (This will download the data, compute politeness scores, fit the CLMM, and generate results.)
2.  The results will be saved in the `results/` directory.

## Data Access

The datasets will be automatically downloaded from Hugging Face Datasets. Ensure you have sufficient disk space (approximately 7GB).

## Code Structure

*   `src/main.py`: Main script for running the analysis.
*   `src/data_processing.py`: Functions for downloading, validating, and filtering the datasets.
*   `src/politeness_scoring.py`: Functions for computing politeness scores.
*   `src/statistical_analysis.py`: Functions for fitting the CLMM and conducting subgroup analyses.

## Troubleshooting

*   If you encounter errors during installation, ensure that you have the correct version of Python and that your virtual environment is activated.
*   If the analysis takes too long, reduce the size of the dataset or simplify the model.
*   If you encounter issues with the datasets, check the Hugging Face Datasets documentation.
