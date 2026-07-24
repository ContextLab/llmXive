# Quickstart: The Effects of Gamified Habit Tracking

## Prerequisites
-   Python 3.11+
-   `pip` (Python package manager)
-   Access to the project repository.

## Setup Instructions

### 1. Clone and Install
```bash
git clone <repo-url>
cd <project-dir>
pip install -r code/requirements.txt
```

### 2. Data Preparation
The pipeline requires a `data/consent/` directory to verify ethical handling.
```bash
mkdir -p data/consent
# Place a dummy consent file for testing (e.g., consent_form_sample.pdf)
# In production, this must contain real consent documentation.
# For the public MyPersonality dataset, the Hugging Face license serves as consent.
echo "Consent Verified" > data/consent/verified.txt
```

### 3. Generate Synthetic Data
Since no open longitudinal dataset with personality traits exists, generate the synthetic dataset:
```bash
python code/data/synthetic_generator.py --seed [RANDOM_SEED] --n_users --weeks 50
```
*Output*: `data/raw/synthetic_data.csv` (N=500, Random Assignment)

### 4. Run the Pipeline
Execute the main orchestration script:
```bash
python code/main.py
```
*This script performs:*
1.  Consent verification (FR-010).
2.  Data ingestion and weekly aggregation (FR-001).
3.  Control group size validation (FR-008) and Event threshold check (FR-009).
4.  VIF check and Mixed-Effects modeling (FR-002).
5.  FDR Correction (FR-007).
6.  Survival analysis (FR-003).
7.  Bootstrapping and Robustness checks (FR-004).
8.  Report generation (FR-005).

### 5. View Results
The final report will be available at:
`data/reports/final_analysis.html`

## Troubleshooting
-   **Error: "Data Insufficiency"**: Ensure `synthetic_generator.py` produced at least 100 users and 30 non-gamified users.
-   **Error: "Consent Missing"**: Ensure `data/consent/` directory is not empty.
-   **Model Convergence Warning**: The pipeline automatically detects high VIF and removes collinear traits. Check `logs/modeling.log` for details.
-   **Error: "Insufficient Events"**: If dropout events < 10 per group, the survival analysis is skipped, and only descriptive stats are reported.
