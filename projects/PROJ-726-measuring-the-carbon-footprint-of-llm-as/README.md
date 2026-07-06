# Measuring the Carbon Footprint of LLM‑Assisted Code Generation

## Project Structure

- `code/`: Source code for data downloading, inference, and analysis.
- `data/raw/`: Raw datasets downloaded from external sources (e.g., HuggingFace).
- `data/processed/`: Processed data ready for analysis (e.g., JSON results, CSVs).
- `data/outputs/`: Final analysis outputs and sensitivity results.
- `tests/`: Unit and contract tests.
- `output/`: Final reports and figures.
- `specs/`: Project specifications and design documents.

## Setup

1. Ensure Python 3.11+ is installed.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Run the setup script (if directories are missing):
 ```bash
 python code/setup_project_structure.py
 ```

## Execution Flow

1. **Download Data**: `python code/download_data.py`
2. **Run Inference**: `python code/run_inference.py`
3. **Calculate Emissions**: `python code/calculate_emissions.py`
4. **Statistical Analysis**: `python code/statistical_analysis.py`
5. **Generate Report**: `python code/generate_report.py`

## License

MIT
