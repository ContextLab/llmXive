# User Guide: Accessibility and Usability Research Pipeline

## Introduction
This guide provides step-by-step instructions for researchers using the PROJ-015 pipeline to conduct usability studies comparing Traditional and Explainable AI interfaces.

## Prerequisites
- Python 3.11+
- Required packages installed via `requirements.txt`
- A modern web browser for the Streamlit interface

## Step 1: Project Setup
1. Clone the repository and navigate to the project root.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Verify the environment by running:
 ```bash
 python code/validation/validate_quickstart.py
 ```

## Step 2: Configuration
Edit `code/config/settings.py` to customize:
- **Study ID**: Unique identifier for the study run.
- **Random Seed**: For reproducibility of simulations.
- **Data Paths**: Ensure `data/raw` and `data/processed` directories exist.

## Step 3: Conducting Usability Tests
1. Launch the simulator:
 ```bash
 streamlit run code/simulator/app.py
 ```
2. **Participant Registration**:
 - Enter a unique participant ID.
 - Select disability type (e.g., visual, motor, cognitive).
 - The system assigns an interface sequence (Traditional -> Explainable or vice versa) using Latin Square counterbalancing.
3. **Task Execution**:
 - Complete tasks on the first interface variant.
 - Metrics (time, errors) are recorded automatically.
 - Transition to the second interface variant after task completion.
4. **SUS Questionnaire**:
 - Complete the System Usability Scale (SUS) survey after each interface.
 - The system handles missing items (imputes ≤1, rejects >1).
5. **Session Logging**:
 - Upon completion, raw data is saved to `data/raw/session_{id}.json` with a checksum for integrity.

## Step 4: Data Analysis
1. Ensure all raw session files are in `data/raw/`.
2. Run the analysis pipeline:
 ```bash
 python code/analysis/run_analysis.py
 ```
3. Review outputs in `data/processed/`:
 - `metrics_summary.csv`: Statistical test results (F-statistic, p-value, effect size).
 - `descriptive_stats.csv`: Mean and standard deviation for all metrics.
 - `report_summary.txt`: Narrative summary of findings.

## Step 5: Visualization and Reporting
1. View generated plots in `figures/` (created by `run_analysis.py`).
2. Execute the Jupyter notebook for a detailed walkthrough:
 ```bash
 jupyter notebook code/analysis.ipynb
 ```
3. Export the notebook as a PDF or HTML for publication.

## Troubleshooting
- **Missing Dependencies**: Re-run `pip install -r requirements.txt`.
- **Data Integrity Errors**: Verify checksums in `data/raw/` using `code/utils/checksum.py`.
- **SUS Imputation Failures**: Ensure participants completed at least 9/10 SUS items.

## Best Practices
- Use consistent lighting and environment for all participants.
- Record screen interactions for qualitative analysis.
- Backup raw data regularly to prevent loss.

## Support
For issues or questions, refer to the `docs/api_reference.md` or contact the project maintainers.
