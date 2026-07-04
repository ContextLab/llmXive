# Quickstart: Framing Effects Simulation (R Implementation)

## Prerequisites

- R 4.3+ (or RStudio)
- Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-399-the-impact-of-framing-on-perceived-sever
    ```

2.  **Install Dependencies**:
    The project uses `renv` or a `DESCRIPTION` file for dependency management.
    ```bash
    # If using renv
    R -e "renv::restore()"
    
    # Or manually install
    R -e "install.packages(c('lme4', 'lmerTest', 'pwr', 'dplyr', 'ggplot2', 'tidyr', 'data.table'))"
    ```

## Running the Analysis

The pipeline consists of four sequential R scripts. Run them in order:

1.  **Data Preparation & Synthetic Generation**:
    ```bash
    Rscript code/01_data_prep.R
    ```
    *Output*: `data/processed/synthetic_dataset.csv`

2.  **Power Analysis**:
    ```bash
    Rscript code/02_power_analysis.R
    ```
    *Output*: Power calculation report (printed to console and saved to `results/power_analysis.txt`).

3.  **Statistical Analysis**:
    ```bash
    Rscript code/03_analysis.R
    ```
    *Output*: Model coefficients, p-values, effect sizes (printed to console).

4.  **Export Results**:
    ```bash
    Rscript code/04_export.R
    ```
    *Output*: `results/results.md`, `results/plots/`

## Verification

To verify the results:
- Check `results/results.md` for the Bonferroni-adjusted p-value and Cohen's d.
- Ensure `data/processed/synthetic_dataset.csv` has exactly 300 rows (10 stimuli × 2 conditions × 15 participants).
- Confirm that `framing_condition` is balanced ([deferred] 'harm', [deferred] 'fact').

## Troubleshooting

- **Missing Dataset**: If the HuggingFace dataset fails, the script will generate synthetic stimuli automatically.
- **Model Convergence**: If `lme4` warns about singular fits, the script will proceed with a warning and report fixed-effects only.
- **Power < 0.80**: The script will print a warning but continue to the main analysis.
