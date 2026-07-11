# Quickstart: The Effect of Sensory Deprivation on Dream Recall and Bizarreness

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-146-the-effect-of-sensory-deprivation-on-dre
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

## Running the Pipeline

### Step 1: Generate Synthetic Data

The pipeline will automatically generate synthetic data based on `data/protocols/protocol.yaml`.

```bash
python code/generate_data.py --scenario A  # Options: A, B, C
```

Output: `data/synthetic/scenario_A.csv` (Contains `deprivation_intensity`, `latent_bizarreness`, etc. **No `condition` column**).

### Step 2: Ingest and Validate Data (Dynamic Thresholding)

The `ingest.py` script derives the `condition` column based on the threshold parameter and validates against `contracts/processed-data.schema.yaml`.

```bash
python code/ingest.py --input data/synthetic/scenario_A.csv --threshold 0.5
```

Output: Validated dataset in `data/processed/scenario_A_threshold_0.5.csv` (includes derived `condition`).

### Step 3: Fit Models

```bash
python code/models.py --input data/processed/scenario_A_threshold_0.5.csv
```

Output: Model results in `results/models/`.

### Step 4: Run Sensitivity Analysis (Coverage Probability)

This step generates 50 independent synthetic datasets internally, applies the threshold to each, and calculates coverage probability.

```bash
python code/sensitivity.py --input data/synthetic/scenario_A.csv --threshold 0.5 --bootstrap 1000 --datasets 50
```

Output: Sensitivity results in `results/sensitivity/`.

### Step 5: Generate Report

```bash
python code/report.py --models results/models/ --sensitivity results/sensitivity/
```

Output: Final report in `results/reports/`.

## Testing

Run unit tests:
```bash
pytest tests/unit/
```

Run contract tests:
```bash
pytest tests/contract/
```

## Troubleshooting

-   **Memory Error**: Ensure no large datasets are loaded; synthetic data is small.
-   **Model Convergence**: If models fail to converge, reduce iterations or use Firth correction.
-   **Zero Recall**: If a condition has zero recall, Firth correction is automatically applied.
-   **Ethics Directory**: Ensure `data/ethics/` exists (contains placeholder waiver).
-   **Schema Validation**: Ensure `data/processed/` output matches `contracts/processed-data.schema.yaml`.