# Quickstart: Improving Accessibility and Usability of Complex Computer Systems for People with Disabilities

## Prerequisites
- Python 3.11+
- Git
- A modern web browser (for the simulator)

## Installation

1.  **Clone and Setup**
    ```bash
    git clone <repo-url>
    cd projects/PROJ-015-improving-accessibility-and-usability-of
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**
    Ensure `scipy`, `matplotlib`, `pandas`, and `streamlit` are installed.
    ```bash
    python -c "import scipy, matplotlib, pandas, streamlit; print('All dependencies OK')"
    ```

## Running the Simulator

The simulator generates the required data for the study.

1.  **Start the Simulator**
    ```bash
    streamlit run code/simulator/app.py
    ```
2.  **Configure Session**
    - Select a `participant_id` (or generate a new one).
    - Choose `interface_type` (Traditional or Explainable).
    - Complete the assigned HCI tasks.
    - Fill out the SUS questionnaire.
3.  **Data Output**
    - The simulator automatically saves logs to `data/raw/sessions.jsonl`.
    - Check the console for "Session saved" confirmation.

## Running the Analysis Pipeline

To reproduce the statistical analysis and generate figures:

1.  **Execute the Notebook**
    ```bash
    jupyter nbconvert --to notebook --execute code/analysis.ipynb --output code/analysis_executed.ipynb
    ```
    *Or open in Jupyter Lab:*
    ```bash
    jupyter lab code/analysis.ipynb
    ```
2.  **Verify Outputs**
    - Check `data/processed/metrics_summary.csv` for statistical results.
    - Check `code/figures/` for generated box plots and bar charts.
    - Ensure the Holm-Bonferroni corrected p-values are present.

## Testing

Run the unit tests for the statistical logic:
```bash
pytest tests/unit/ -v
```
