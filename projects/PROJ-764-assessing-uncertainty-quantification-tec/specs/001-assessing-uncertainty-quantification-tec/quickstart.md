# Quickstart: Assessing Uncertainty Quantification Techniques for Machine‑Learning Predicted Material Properties

## Prerequisites

*   Python 3.11
*   pip
*   Access to a CPU-based environment (GitHub Actions runner, local machine)

## Installation

1.  Clone the repository:

    ```bash
    git clone [repository URL]
    cd [repository directory]
    ```

2.  Create a virtual environment:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

1.  Execute the main script:

    ```bash
    python src/main.py
    ```

    This will download the dataset, train the models, generate uncertainty estimates, evaluate calibration, and perform downstream screening.

## Output

The results will be stored in the `results/` directory:

*   `uq_predictions_base.csv`: Predictions and uncertainty estimates from all three UQ methods.
*   `calibration_report.csv`: Calibration metrics (ECE, interval score, sharpness) for each method.
*   `screening_results.csv`: Precision of the UQ-based screening compared to random selection.
*   Model weights (`.pt` files) will be saved in `results/models/`.
*   Reliability diagrams will be saved as PNG images in `results/`.

## Troubleshooting

*   **Runtime Errors:** Check the error messages in the console output. Ensure all dependencies are installed correctly.
*   **Data Download Issues:** Verify your internet connection and the availability of the OQMD dataset on Hugging Face.
*   **Resource Constraints:** If you encounter memory errors, reduce the batch size or simplify the model architecture.
