# Quickstart: Investigating the Relationship Between Pupil Dilation and Cognitive Load During Visual Search

## Prerequisites

- Python 3.11+
- Git
- Internet access for dataset download

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-174-investigating-the-relationship-between-p
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Data Preparation

The pipeline expects raw eye‑tracking data in `data/raw/`.

1. **Download the verified visual‑search dataset**:
   ```bash
   # Primary dataset with salience metadata
   datalad install -d data/raw -s https://openneuro.org/datasets/ds004248.git
   ```
   *If `datalad` is unavailable, you may manually download the EDF/CSV files from the OpenNeuro page and place them in `data/raw/`.*

2. **Validate dataset suitability**:
   ```bash
   python code/data_loader.py --validate
   ```
   This script checks that the required columns (`pupil_diameter`, `timestamp`, `search_time`) and the **stimulus metadata file** (`salience_map.npy`) are present. If the metadata is missing, the script **aborts** with a clear error. No fallback to unsuitable datasets is permitted.

## Running the Full Pipeline

From the `code/` directory, execute:

```bash
python main.py --config config.yaml
```

### Configuration Options (`config.yaml`)

- `random_seed`: Integer (default 42) – pinned for reproducibility.
- `low_pass_cutoff`: Float (default 4.0 Hz) – pupil filter.
- `blink_threshold`: Float (default 0.2) – proportion of interpolated samples allowed.
- `classification_thresholds`: List [0.01, 0.05, 0.10] – decision thresholds for sensitivity analysis.
- `data_path`: String (path to raw data) – default `data/raw/`.
- `sliding_window_ms`: Integer (200) – window size for real‑time classifier (logged per Principle VII).

## Output

All results are written to `outputs/`:

- `correlations.csv` – Pearson r, raw and Bonferroni‑adjusted p‑values.
- `lme_results.json` – Fixed‑effect estimates, SEs, p‑values, and LRT.
- `classifier_results.csv` – Accuracy, precision, recall, ROC‑AUC per threshold. Includes `validation_type` ("Independent" or "Internal Consistency").
- `quality_report.csv` – Exclusion counts and reasons.
- `evaluation_log.json` – Includes the **exact integer values** of `random_seed` and `sliding_window_ms` for full traceability.

## Validation

Run the test suite to confirm a successful installation:

```bash
pytest tests/
```

## Troubleshooting

- **Missing `stimulus_salience` metadata**: The pipeline will **abort** with a clear error. Provide a dataset that includes the `salience_map.npy` file to enable full analysis.
- **Memory errors**: Reduce batch size in `config.yaml` or work with a subset of subjects.
- **Dataset not found**: Verify the OpenNeuro URL and your internet connection; the pipeline does not fall back to other datasets.