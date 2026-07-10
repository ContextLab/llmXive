# Quickstart: Predicting Plant Secondary Metabolite Profiles from Genomic Data

## Prerequisites

-   Python 3.11+
-   `conda` or `venv`
-   Internet access for data download (or mock data generation)
-   **Optional**: `antiSMASH 7.0` installed locally (only if running on real data manually, not on CI)

## Installation

1.  **Clone & Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-198-predicting-plant-secondary-metabolite-pr
    python -m venv venv
    source venv/bin/activate
    pip install -r code/requirements.txt
    ```

2.  **Verify Environment**:
    Ensure Python is accessible.
    ```bash
    python --version
    ```

## Running the Pipeline

### 1. Configure Species List
Edit `config/species_list.yaml` to include your target species (e.g., *Arabidopsis*, *Rice*, *Maize*).
```yaml
species:
  - id: "Arabidopsis_thaliana"
    clade: "Brassicaceae"
  - id: "Oryza_sativa"
    clade: "Poaceae"
  # ... add at least 10 species
```
**Note**: If these species do not have matched genome/metabolite data available in public repositories, the pipeline will generate a **mock dataset** for validation.

### 2. Execute Data Download & Alignment
```bash
python code/main.py --step download_and_align
```
*This step attempts to download genomes, runs antiSMASH (if local), fetches metabolites, and creates `data/processed/aligned_dataset.csv`. If no real data is found, it generates a mock dataset.*

### 3. Run Modeling & Validation
```bash
python code/main.py --step model_and_validate
```
*This step performs PVR, Random Forest/Elastic Net training, Permutation tests. **Note: PIC is not run due to data limitations.**.*

### 4. Run Sensitivity Analysis
```bash
python code/main.py --step sensitivity_sweep
```
*This step sweeps the 10th, 25th, 50th percentile thresholds and generates the robustness report.*

## Expected Outputs

-   `data/processed/aligned_dataset.csv`: The final feature-target matrix (real or mock).
-   `results/model_metrics.json`: R², p-values (perm), VIF scores. **Note: No PIC p-value.**
-   `results/sensitivity_report.csv`: R² variation across thresholds.
-   `logs/pipeline.log`: Execution logs with warnings for missing data.

## Troubleshooting

-   **"Insufficient species count"**: Ensure your `species_list.yaml` has ≥10 species with both genome and metabolite data available. If not, the pipeline will default to mock data.
-   **"antiSMASH timeout"**: This step is skipped on CI. If running locally, reduce the number of species in the list (max 20 recommended).
-   **"No plant data found"**: The pipeline will generate a mock dataset for CI validation. Real results require manual data assembly.