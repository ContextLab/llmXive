# Quickstart: The Impact of Visual Distraction on Cognitive Control in Remote Work Environments

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local environment for testing).
- Unsplash API Access Key (for downloading images).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-479-the-impact-of-visual-distraction-on-cogn
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Data Source Selection

This project uses **real data** from two sources:
- **Cognitive Data**: OpenML (Dataset ID: 44000 - Stroop Task Data).
- **Workspace Images**: Unsplash API (search query: "home office desk").

**Proxy Linkage**: The two datasets are linked via environmental metadata (e.g., "Home Office" -> "Home Office"). This is the only feasible approach given the lack of a single public dataset linking participant IDs to workspace images.

## Execution

1. **Download Data**:
   ```bash
   python code/01_data_acquisition.py
   ```
   This script downloads cognitive data from OpenML and images from Unsplash, then performs proxy linkage. It creates `data/processed/linked_data.csv`.

2. **Extract Visual Metrics**:
   ```bash
   python code/02_visual_metrics.py
   ```
   This script computes edge density, color entropy, and object count from the downloaded images.

3. **Run Analysis**:
   ```bash
   python code/03_analysis.py
   ```
   This script performs correlation, regression, VIF checks, and Holm-Bonferroni correction.

4. **Run Sensitivity Analysis**:
   ```bash
   python code/04_sensitivity.py
   ```
   This script performs bootstrap resampling and binning sensitivity checks, generating `results/statistics/binning_sensitivity_table.csv`.

5. **Generate Reports**:
   ```bash
   python code/05_reporting.py
   ```
   This script generates scatter plots, final JSON/CSV reports, and a `justification.md` file for the p<0.05 threshold.

## Interpretation of Results

- **Correlation Coefficients (r)**: Values range from -1 to 1. Negative values indicate that higher visual complexity is associated with lower accuracy or slower reaction times.
- **P-values**: Values < 0.05 (after Holm-Bonferroni correction) indicate statistical significance.
- **VIF**: Values ≥ 5 indicate high collinearity; in such cases, PCA was applied.
- **Causal Claims**: **None**. All findings are framed as associational.
- **p<0.05 Justification**: See `results/statistics/justification.md` for the explicit justification of the significance threshold.

## Troubleshooting

- **Missing Data**: If `linked_data.csv` is empty, check `code/01_data_acquisition.py` for API key issues or metadata mismatches.
- **Object Detection Failure**: If YOLO fails on specific images, `object_count` will be NaN. The analysis script excludes these from object-count-based tests.
- **High VIF**: If VIF ≥ 5, the script automatically switches to PCA. Check `results/statistics/vif_report.json` for details.
- **PII**: All image files are renamed to `img_<hash>.jpg` and EXIF data is stripped to remove PII.