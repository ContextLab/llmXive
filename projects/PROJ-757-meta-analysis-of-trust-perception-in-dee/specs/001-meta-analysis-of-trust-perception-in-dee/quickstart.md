# Quickstart: Meta‑Analysis of Trust Perception in Deepfake Facial Stimuli

## Prerequisites

- **Python**: 3.11+
- **R**: 4.3+ (with `metafor`, `esc`, `ggplot2`)
- **Git**: For version control.

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install R dependencies (via renv or manually)
# Ensure R is in PATH
Rscript -e 'install.packages(c("metafor", "esc", "ggplot2", "dplyr"), repos="https://cloud.r-project.org")'
```

### 2. Configure Environment

Set API keys if required (e.g., for Semantic Scholar):
```bash
export SEMANTIC_SCHOLAR_API_KEY="your_key_here"
```
*Note: OpenAlex and arXiv do not require keys for basic usage.*

### 3. Run the Pipeline

The pipeline is executed in phases:

```bash
# Phase 1: Search and Screen (Generates inclusion_criteria.yaml)
# NOTE: If Kappa < 0.6, this step will HALT and flag for human review.
python code/01_search_and_screen.py

# Phase 2: Effect Size Calculation
python code/02_effect_size_calc.py

# Phase 3: Meta-Analysis (R script invoked via Python driver)
python code/03_meta_analysis_driver.py

# Phase 4: Robustness Checks and Plotting (Generates PDFs)
python code/04_robustness_checks.py
```

### 4. Verify Outputs

Check the `results/` directory for:
- `figures/PRISMA_flow.pdf`
- `figures/Forest.pdf` (Labeled axes, visible CIs)
- `figures/Funnel.pdf` (Labeled axes, visible CIs)
- `results/robustness/sensitivity_analysis.csv`
- `data/screening/inclusion_criteria.yaml`

### 5. Run Tests

```bash
pytest tests/
```

## Troubleshooting

- **R Script Fails**: Ensure `rpy2` is installed and R is in the system PATH.
- **API Rate Limits**: The search script includes exponential backoff. Wait 60 seconds if errors persist.
- **Missing Data**: Check `data/harmonized/effect_sizes.csv` for `NaN` values in critical fields.
- **Low Power**: If the log reports "Insufficient Power for Moderator Analysis", check `results/robustness/subgroup_analysis.csv` for fallback results.
- **Human Adjudication Required**: If the pipeline halts in Phase 1, check `screening_log.csv` for `adjudication_required=True` and resolve manually.