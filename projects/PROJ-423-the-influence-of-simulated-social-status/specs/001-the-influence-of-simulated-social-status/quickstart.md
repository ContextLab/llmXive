# Quickstart: The Influence of Simulated Social Status on Risk-Taking Behavior

## Prerequisites

*   A recent version of Python was installed.
*   `pip` package manager.
*   GitHub Actions runner (free tier).

## Installation

```bash
git clone https://github.com/[your_repo]/the-influence-of-simulated-social-status.git
cd the-influence-of-simulated-social-status
python3 -m venv .venv
source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows
pip install -r code/requirements.txt
```

## Data Preparation

The data will be automatically generated or downloaded during the analysis process, depending on the chosen approach (simulation vs. meta-analysis). **While automated processes are in place for data acquisition and preprocessing, some manual verification of dataset integrity may be required, especially when using aggregated data from external sources.**

## Running the Analysis

1.  **Configure parameters:** Modify the `code/config.yaml` file to specify simulation parameters or select a list of studies for meta-analysis.
2.  **Run the analysis script:**

    ```bash
    python code/main.py
    ```

3.  **View results:** The results will be saved in the `data/processed` directory, including:
    *   `cleaned_data.csv`: Cleaned and preprocessed dataset.
    *   `model_config.json`: Model configuration parameters.
    *   `model_output.json`: Regression model output (coefficients, p-values).

## Report Generation

The report will be automatically generated after the analysis is complete:

```bash
python code/report_generator.py
```

This will produce a PDF summary of the results, including effect size plots and model diagnostics.

## Troubleshooting

*   **Missing dependencies:** Ensure all required packages are installed using `pip install -r code/requirements.txt`.
*   **Memory errors:** Reduce the dataset size or switch to asymptotic standard errors during bootstrapping if memory limitations occur.
*   **Incorrect data format**: Verify that the input data (if provided manually) matches the expected schema defined in `data-model.md`.
