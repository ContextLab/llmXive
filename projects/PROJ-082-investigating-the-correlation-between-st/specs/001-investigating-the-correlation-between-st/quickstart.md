# Quickstart: Investigating the Correlation Between Structural Brain Connectivity and Individual Music Preferences

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-082-investigating-the-correlation-between-st
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

## Usage

### 1. Prepare Input Data

Place your study data in `data/raw/studies.csv` with the following columns:
- `author`, `year`, `tract_name`, `metric`, `r`, `n`, `qualitative_desc`

*Note: If you do not have real data, use the provided synthetic data generator in `tests/data/synthetic_data.py`.*

### 2. Run the Analysis

Execute the main script:
```bash
python code/main.py --input data/raw/studies.csv --output data/processed/results.json
```

### 3. Generate Visualizations

The script automatically generates plots in `data/processed/plots/`:
- `forest_plot.png`
- `funnel_plot.png`
- `correlation_plot.png`

### 4. Verify Results

Check the output JSON (`data/processed/results.json`) for:
- `synthesis_mode`: "quantitative" or "narrative"
- `pooled_r` (if quantitative)
- `i_squared` (must have 2 decimal places)
- `egger_skipped_reason` (if N < 10)

### 5. Run Tests

```bash
pytest tests/ -v
```

## Troubleshooting

- **Memory Error**: Ensure you are not loading a massive dataset. The pipeline is designed for <100 studies.
- **Egger's Test Error**: If N < 10, the test is skipped automatically. Check `egger_skipped_reason`.
- **PNG Size**: If PNGs exceed 5MB, reduce DPI in `visualization.py` (default is set to a moderate magnitude).

## Output Format

The final output is a JSON file containing the meta-analysis results and paths to the generated plots. All statistics are reproducible via the pinned random seeds in `code/utils.py`.
