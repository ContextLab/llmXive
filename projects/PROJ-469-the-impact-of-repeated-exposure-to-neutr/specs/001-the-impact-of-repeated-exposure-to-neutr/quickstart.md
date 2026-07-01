# Quickstart: 001-political-news-implicit-bias

## Prerequisites

- Python 3.11+
- `pip`
- Access to the Project Implicit Political IAT dataset (CSV) and codebook.

## Installation

1. Clone the repository.
2. Navigate to the project directory:
   ```bash
   cd projects/PROJ-469-the-impact-of-repeated-exposure-to-neutr/specs/001-political-news-implicit-bias
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Data Preparation

1. Download the Project Implicit Political IAT dataset and codebook.
2. Place them in `data/raw/`.
3. Ensure the codebook maps column names to `IAT_D_score`, `political_ideology`, `news_exposure_freq`.

## Running the Analysis

Execute the main pipeline:
```bash
python code/main.py
```

### Expected Output
- `results/report.pdf`: Full analysis report.
- `results/model_summary.csv`: Model coefficients and diagnostics.
- `results/diagnostics.csv`: Imputation and bootstrap diagnostics.

## Troubleshooting

- **Missing Variables**: If `ValueError` is raised, check the codebook mapping.
- **Missing Data**: If >50% missingness, the pipeline will halt.
- **Timeout**: If bootstrap exceeds 6 hours, partial results will be saved.

## Verification

1. Check `results/` for the presence of `report.pdf` and `model_summary.csv`.
2. Verify that the report frames findings as **associational**.
3. Confirm that the bootstrap CI is finite.
