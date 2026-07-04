# Quickstart: Robustness of Confidence Intervals to Differential Privacy Noise

## Prerequisites

*   Python 3.10+ installed.
*   Git installed.
*   Access to a GitHub Actions runner (or local environment with sufficient RAM).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-710-robustness-of-confidence-intervals-to-di
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Dependencies include: `numpy`, `pandas`, `scipy`, `statsmodels`, `scikit-learn`.*

## Running the Simulation

The simulation is orchestrated by `code/main.py`.

1.  **Run the full pipeline**:
    ```bash
    python code/main.py
    ```
    *This will:*
    *   Generate synthetic populations.
    *   Run the Outer Loop and Inner Loop.
    *   Apply adjustments.
    *   Run the GLM analysis.
    *   Perform the Threshold Sensitivity Sweep.
    *   Run the Convergence Check.
    *   Save results to `artifacts/`.

2.  **Run specific components (for debugging)**:
    ```bash
    # Generate data only
    python code/data/synthetic_pop.py

    # Run convergence check (requires pre-generated results)
    python code/analysis/convergence_check.py
    ```

## Verifying Results

1.  **Check Coverage Results**:
    Open `artifacts/coverage_results.csv` and verify the `covered` column contains 0s and 1s. Ensure `seed` is present.

2.  **Check Sensitivity Analysis**:
    Open `artifacts/sensitivity_analysis.csv` and verify thresholds and passing cases.

3.  **Check GLM Output**:
    Open `artifacts/glm_summary.json` and verify p-values are present for the `epsilon` factor.

4.  **Run Tests**:
    ```bash
    pytest code/tests/
    ```

## Troubleshooting

* **Memory Error**: Ensure you are not loading the full synthetic population into memory for every bootstrap step. The code should sample *from* the population, not load the whole population [deferred] times.
*   **Runtime > 6h**: Reduce the number of Monte Carlo replications ($N_{sim}$) in `code/config.py` (e.g., from a standard baseline to a reduced count) for a quick test.
*   **NaNs in Results**: Check if $\epsilon$ is too small for the data range, causing excessive noise. The code should log warnings for this.
*   **Convergence Failed**: If `convergence_check.py` reports high variance, increase $N_{sim}$ in `config.py`.