# Quickstart: The Influence of Perceived Agency in AI Interactions on Trust

## Prerequisites

- Python 3.11 or higher
- Git
- A text editor or IDE (e.g., VS Code)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd projects/PROJ-286-the-influence-of-perceived-agency-in-ai-
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Analysis Pipeline

1. **Prepare the data**:
   - Place the raw CSV export from the data collection interface in `data/raw/`.
   - Ensure the file is named `raw_data.csv` (or update `code/analysis/config.yaml` accordingly).
   - **Important**: The CSV must conform to `contracts/participant.schema.yaml` (e.g., 7-point Likert scale, correct column names).

2. **Run the power analysis**:
   ```bash
   python code/analysis/power_analysis.py
   ```
   This will generate `research/power_calculation.json`.

3. **Run the main analysis**:
   ```bash
   python code/analysis/main.py
   ```
   This will:
   - Load and clean the data.
   - Perform planned contrasts (High vs. Low).
   - Perform post-hoc tests with Tukey correction.
   - Calculate effect sizes.
   - Generate visualizations and save results to `data/outputs/`.

4. **Run the sensitivity analysis**:
   ```bash
   python code/analysis/sensitivity.py
   ```
   This will test the robustness of the results to different exclusion thresholds.

## Running Tests

```bash
pytest tests/
```

## Generating the Report

The analysis pipeline will automatically generate a summary report in `data/outputs/analysis_report.md`. This report includes:
- Descriptive statistics.
- Results of planned contrasts.
- Results of post-hoc tests.
- Effect sizes.
- Sensitivity analysis results.

## Troubleshooting

- **Missing dependencies**: Ensure you activated the virtual environment and ran `pip install -r code/requirements.txt`.
- **Data format errors**: Check that the raw CSV matches the schema defined in `data-model.md` and `contracts/participant.schema.yaml`.
- **Permission errors**: Ensure you have write access to the `data/` and `research/` directories.
- **Scale Item Mismatch**: If the data uses a 5-point scale but the schema expects 7, verify that `docs/trust_scale_items.md` was generated correctly and the survey interface was updated.