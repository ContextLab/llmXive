# Quickstart: The Impact of Visual Search Strategies on Attentional Capture by Emotional Faces

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI execution)

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-290-the-impact-of-visual-search-strategies-o
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Data Download

1. **Run Download Script**:
   ```bash
   python code/data/download.py --dataset <dataset-name>
   ```
   - **Note**: Replace `<dataset-name>` with the HuggingFace dataset identifier.
   - **Retry Logic**: Automatic exponential backoff for network failures.

2. **Validate Data**:
   ```bash
   python code/data/validate.py
   ```
   - **Output**: Logs integrity checks; excludes incomplete records.

## Feature Extraction

1. **Extract Fixation Metrics**:
   ```bash
   python code/features/extraction.py
   ```
   - **Output**: `data/processed/features.csv`

2. **Classify Strategies**:
   ```bash
   python code/features/classification.py
   ```
   - **Output**: `data/processed/labels.csv`

## Statistical Analysis

1. **Fit LMM**:
   ```bash
   python code/models/lmm.py
   ```
   - **Output**: Model coefficients, convergence logs, adjusted p-values.

2. **Power Analysis**:
   ```bash
   python code/models/power.py
   ```
   - **Output**: Achieved power for effect size d=0.5.

## Results

- **Reports**: `results/reports/`
- **Figures**: `results/figures/`
- **Logs**: `results/logs/`

## Troubleshooting

- **Network Errors**: Check connectivity; retry logic handles up to 3 attempts.
- **Model Convergence**: If LMM fails, fallback to simpler linear model (logged).
- **Missing Variables**: Pipeline halts with specific error; check dataset documentation.

## Next Steps

- Review `results/reports/` for analysis outcomes.
- Validate citations using the Reference-Validator Agent.
- Proceed to `research_review` stage if all success criteria are met.
