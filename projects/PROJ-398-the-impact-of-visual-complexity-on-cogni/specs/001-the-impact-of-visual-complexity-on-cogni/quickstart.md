# Quickstart: The Impact of Visual Complexity on Cognitive Load During Remote Meetings

## 1. Prerequisites

- Python 3.11+
- `pip`
- (Optional) `git`

## 2. Installation

1.  **Clone the repository** (or navigate to the project root).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins versions for CPU-only execution.*

## 3. Running the Pipeline

### Step 1: Generate Synthetic Stimuli (Pipeline Validation Only)
If no `data/stimuli/` exists, run the generation script:
```bash
python code/main.py --action generate_stimuli --count 50
```
This creates 50 images in `data/stimuli/` and logs metadata. **These are for code testing only.**

### Step 2: Extract Visual Complexity Metrics
Run the metric extraction pipeline:
```bash
python code/main.py --action extract_metrics --input data/stimuli/ --output data/derived/metrics.json
```
*This step runs YOLOvn inference on CPU. Ensure you have ~2GB RAM free.*

### Step 3: Prepare Human Pilot Data (Mandatory for Validation)
**WARNING**: You MUST collect real human ratings (n=20) for the pilot study to validate metrics.
- **Do NOT** use `simulate_pilot` for scientific validation.
- To test the *code logic* only (not validation), you may generate a placeholder file:
  ```bash
  python code/main.py --action generate_placeholder_ratings --output data/measurements/pilot_ratings_placeholder.csv
  ```
  *Note: The analysis script will reject `pilot_ratings_placeholder.csv` for the validation gate and will output "VALIDATION ONLY - NOT SCIENTIFIC" if used.*

### Step 4: Run Statistical Analysis
Execute the full analysis pipeline:
```bash
python code/main.py --action run_analysis --metrics data/derived/metrics.json --ratings data/measurements/pilot_ratings.csv --output data/derived/model_results.json
```
*The script will check the `source` flag in the ratings file. If `source` is not `real`, the output will be marked "VALIDATION ONLY" and will contain no hypothesis test results.*

## 4. Verifying Results

Check the output report:
```bash
cat data/derived/model_results.json
```
Verify the correlation coefficient (r > 0.5) and the adjusted p-values. **Ensure the report does not state "VALIDATION ONLY".** If it does, the data was synthetic and the results are not scientific findings.

## 5. Running Tests

Ensure all contracts and logic are valid:
```bash
pytest tests/ -v
```

## 6. Troubleshooting

- **OOM Error**: If YOLOv8n fails due to memory, reduce the batch size in `code/metrics/extraction.py`.
- **Schema Validation Fail**: Ensure all JSON files match the schemas in `contracts/`. Run `pytest tests/test_contracts.py` for details.
- **No Verified Dataset**: The pipeline uses synthetic data for testing. If you have real images, place them in `data/stimuli/` and re-run `extract_metrics`.
- **Validation Gate Failed**: Ensure `data/measurements/pilot_ratings.csv` contains real human ratings and is flagged as `source: real`.