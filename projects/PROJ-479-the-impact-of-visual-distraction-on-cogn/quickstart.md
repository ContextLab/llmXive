# Quickstart Guide: The Impact of Visual Distraction on Cognitive Control

This guide provides instructions for setting up and running the research pipeline for analyzing the impact of visual distraction on cognitive control in remote work environments.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- At least 4GB of available RAM (8GB recommended for image processing)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <project-directory>
```

2. Install dependencies:
```bash
pip install -r code/requirements.txt
```

## Data Source Selection

This pipeline supports two data sources: real public datasets (if available) and a synthetic data fallback. The system automatically attempts to download real data first.

### Real Dataset Path

The pipeline attempts to download cognitive task data (Stroop/Flanker) from HuggingFace or OpenML.

**Verification Steps:**
- The script `code/01_data_acquisition.py` checks for the existence of specific dataset IDs (`StroopTaskDataset`, `FlankerDataset`).
- If a linked dataset with participant-level image paths is found and successfully downloaded, the pipeline proceeds with real data.
- If the download fails or no linked dataset exists (verified by the check), the system sets a `synthetic_fallback` flag and transitions to the synthetic generation path.
- **Note:** No manual intervention is required to switch to real data; the script handles this logic automatically.

### Synthetic Data Path

If real data is unavailable, the pipeline generates synthetic data to ensure the analysis can proceed.

**Generation Process:**
1. **Participant Records:** Generates N ≥ 100 synthetic participant records simulating the negative correlation structure between visual complexity and cognitive performance (reaction time/accuracy) as described in literature.
2. **Workspace Images:** Simultaneously generates corresponding synthetic workspace images using Pillow. These images are linked to participant metadata (lighting, room type, demographics).
3. **Atomic Generation:** The generation of participants and images occurs in a single execution step to ensure data integrity.
4. **Quality Control:** Immediately after generation, edge density is computed on a sample of images. If the standard deviation of edge density is 0 (indicating no variance), the script raises a `ValueError` and halts execution to prevent invalid data.
5. **Configuration:** The correlation structure is derived from a configurable `target_correlation` parameter, and the generation logic uses a `literature_source` parameter for traceability.

## Running the Pipeline

Execute the pipeline in the following order:

1. **Data Acquisition:**
```bash
python code/01_data_acquisition.py
```
This step produces `data/processed/merged_data.csv` and `results/statistics/power_analysis_report.md`.

2. **Visual Metrics Extraction:**
```bash
python code/02_visual_metrics.py
```
This step computes edge density, color entropy, and object count, producing `data/processed/final_analysis_data.csv`.

3. **Statistical Analysis:**
```bash
python code/03_analysis.py
```
This step performs correlations, VIF analysis, PCA (if needed), and bootstrap resampling, producing `results/statistics/statistics.json` and `results/sensitivity/`.

4. **Visualization:**
```bash
python code/04_visualization.py
```
This step generates scatter plots and visual summaries in `results/plots/`.

5. **Final Report:**
The final report is generated automatically at the end of the analysis step (T045 logic) and is saved to `results/report.md`.

## Interpretation of Results

**CRITICAL:** All findings in this pipeline are **associational**. No causal claims are made regarding the relationship between visual distraction and cognitive control.

### Associational Framing

The analysis computes Pearson correlation coefficients, linear regression slopes, and confidence intervals. These metrics describe the strength and direction of relationships between variables but do not imply that changes in visual complexity *cause* changes in cognitive performance.

- **Correlation (r):** Measures the linear association between two variables.
- **Regression (β):** Estimates the change in the outcome variable associated with a one-unit change in the predictor variable, holding other factors constant in the model.
- **Confidence Intervals:** Provide a range of plausible values for the population parameter, based on the sample data.

### Real Dataset Interpretation

When using real datasets, results reflect the specific population and conditions of the source data. Generalizability to other remote work environments should be considered carefully. The associations observed are valid for the dataset analyzed but may not hold universally.

### Synthetic Data Interpretation

When using synthetic data, results demonstrate the pipeline's ability to detect the *simulated* negative correlation structure defined during generation. These results validate the methodological framework and code correctness but do not represent empirical findings about real human behavior. The synthetic data is generated with a configurable `target_correlation` parameter to ensure the pipeline functions correctly under known conditions.

## Output Files

- `data/processed/merged_data.csv`: Combined cognitive and image metadata.
- `data/processed/final_analysis_data.csv`: Cleaned dataset with visual metrics.
- `results/statistics/statistics.json`: Correlation and regression results.
- `results/statistics/vif_report.json`: Variance Inflation Factor scores.
- `results/sensitivity/bootstrap_results.json`: Bootstrap resampling confidence intervals.
- `results/plots/`: Scatter plots and trend lines.
- `results/report.md`: Comprehensive final report including methods citations and alpha threshold justification.

## Troubleshooting

- **Missing Dependencies:** Ensure all packages in `code/requirements.txt` are installed.
- **Image Processing Failures:** Check that `data/raw/` contains valid image files. The pipeline logs specific errors for unmatched participant IDs and image processing failures.
- **Memory Errors:** If running out of memory during image processing, ensure you have at least 8GB of RAM available. The pipeline processes images sequentially to minimize memory footprint.
- **Synthetic Data Generation Failure:** If the script raises a `ValueError` regarding zero variance in edge density, check your system's random seed configuration. The global seed is managed by `code/utils.py`.