# Quickstart: Investigating the Role of Microglial Morphology in Age-Related Cognitive Decline

## Prerequisites

- Python 3.11+
- `pip`
- Access to a Linux environment (or WSL2 on Windows).
- **Note**: As no verified public dataset URLs exist for the specific matched biological data, this quickstart uses **synthetic data generation** to validate the pipeline logic.

## 1. Setup Environment

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r projects/PROJ-123-investigating-the-role-of-microglial-mor/code/requirements.txt
```

## 2. Generate Synthetic Data (Validation Mode)

Since real matched datasets are unavailable (see `research.md`), run the synthetic generator to create a mock dataset that satisfies the schema requirements.

```bash
python projects/PROJ-123-investigating-the-role-of-microglial-mor/code/main.py --mode generate-synthetic --output data/processed/synthetic_dataset.csv
```

*This command creates:*
- Mock microscopy images (simulated in memory or dummy files).
- A CSV with `image_id`, `brain_region`, `pathology_status`, and mock morphological metrics.
- A CSV with `subject_id`, `raw_cognitive_score`, and `cohort_id`.
- **Null Hypothesis Cases**: Includes samples where the interaction effect is zero to validate non-detection.

## 3. Run the Pipeline

Execute the full pipeline: ingestion (mock), extraction (mock), normalization, classification, PCA, regression, and sensitivity analysis.

```bash
python projects/PROJ-123-investigating-the-role-of-microglial-mor/code/main.py --mode run-full --data data/processed/synthetic_dataset.csv
```

*Expected Output:*
- `reports/final_report.md`: Contains regression coefficients, interaction p-values, and the `causality_warning`.
- `reports/sensitivity_analysis.json`: P-value variation across Sholl steps {2, 5, 10}.
- Console logs: Warnings for excluded subjects (if any) and VIF checks.
- **Power Report**: Includes observed power for the interaction term.

## 4. Verify Results

Check the `reports/final_report.md` for:
1.  **Interaction Term**: Is the p-value for `PathologyStatus * BrainRegion` < 0.05? (Or correctly non-significant in null cases).
2.  **VIF**: Are all VIF scores < 5.0?
3.  **Causality**: Is `causality_warning` set to `true`?
4.  **Sensitivity**: Is the interaction p-value stable across Sholl steps?
5.  **Interpretability**: Are PC loadings included to map back to original features?

## 5. Running Tests

```bash
pytest tests/ -v
```

*Tests cover:*
- Extraction accuracy (mock comparison).
- VIF calculation logic.
- Sensitivity analysis sweep.
- Schema validation.
- **Null Hypothesis**: Ensuring the model correctly returns non-significance for null cases.

## 6. Integrating Real Data

Once verified public datasets are identified (or local data is provided):
1.  Place raw images in `data/raw/images/`.
2.  Place metadata CSVs in `data/raw/metadata/`.
3.  Update `code/config.py` with the correct file paths.
4.  Run `main.py --mode run-full --data data/raw/metadata/`.

*Note: Ensure data checksums are recorded in `state/` as per Constitution Principle III.*