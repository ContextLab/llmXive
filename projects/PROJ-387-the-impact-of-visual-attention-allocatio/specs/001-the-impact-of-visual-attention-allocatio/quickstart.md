# Quickstart: 001-visual-attention-recall

## Prerequisites

- Python 3.11+
- `pip` (Python package manager)
- Access to a verified eye-tracking dataset (Currently **unavailable** per `research.md`).

## Installation

1. **Clone Repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-387-the-impact-of-visual-attention-allocatio
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins versions for reproducibility (Constitution I).*

## Running the Pipeline

### 1. Data Ingestion (Validation Only)
Due to the lack of a verified dataset, this step will flag the data gap.
```bash
python code/ingestion/validate_data.py --input data/raw/sample.csv
```
**Expected Output**: Log message indicating "Dataset incompatible: Missing required columns (fixation_duration_ms, ...)" or "No verified source found for FR-002".

### 2. Statistical Analysis (Requires Valid Data)
If valid data is provided manually (bypassing verified constraint):
```bash
python code/analysis/lmm_model.py --input data/processed/cleaned.csv
```

### 3. Generate Report
```bash
python code/reporting/generate_report.py --input output/results/analysis.json
```

## Verification

- **Check Plots**: Verify `output/plots/` contains ≥2 files per valence category (FR-007).
- **Check Results**: Verify `output/results/` contains `p_value_corrected` (SC-003).
- **Check Runtime**: Ensure total execution <6 hours (SC-004).

## Troubleshooting

- **Memory Error**: Reduce sample size in `code/utils/config.py`.
- **Validation Fail**: Ensure input CSV contains all columns listed in `contracts/eye_tracking_schema.yaml`.
- **Data Gap**: Refer to `research.md` for details on missing verified datasets.
