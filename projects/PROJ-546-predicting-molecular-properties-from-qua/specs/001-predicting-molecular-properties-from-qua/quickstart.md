# Quickstart: Predicting Molecular Properties from Quantum Chemical Calculations

## Prerequisites

*   Python 3.11 or higher
*   Git
*   GitHub Actions runner (or a compatible environment)

## Installation

1.  Clone the repository:

    ```bash
    git clone https://github.com/your-username/predicting-molecular-properties-from-qua.git
    cd predicting-molecular-properties-from-qua
    ```

2. Install dependencies using `pip`:

   ```bash
   pip install -r requirements.txt # or use conda environment, if set up
   ```

## Running the Pipeline

1.  Download the experimental barrier dataset:

    ```bash
    # The code automatically handles download from Hugging Face Datasets. No manual step needed
    ```

2. Execute the main script to run the entire pipeline:

    ```bash
    python src/main.py # or invoke a specific task with python src/<task>.py
    ```

## Output Files

The following output files will be generated in the `data/` and `reports/` directories:

*   `data/descriptors_semi.csv`: Semi-empirical descriptors.
*   `data/descriptors_dft.csv`: DFT descriptors (stratified subset).
*   `reports/evaluation.json`: Model evaluation metrics.
*   `reports/sensitivity.csv`: Feature importance and sensitivity analysis results.

## Troubleshooting

*   **Convergence Failures**: Check `logs/convergence_failures.log` for molecules that failed to converge during DFTB+ optimization.
*   **Out-of-Memory Errors**: Reduce the dataset size or use streaming techniques if memory usage is excessive.
*   **Invalid Geometry**: Ensure molecular structures are valid and geometries are properly optimized before performing calculations.
