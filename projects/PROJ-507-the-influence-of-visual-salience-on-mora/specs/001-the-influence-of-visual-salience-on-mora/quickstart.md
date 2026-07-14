# Quickstart: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

## Prerequisites

- Python 3.11 or higher
- Git
- Access to the HuggingFace datasets (for downloading `runwayml/stable-diffusion-v1-5` if using Option A)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd projects/PROJ-507-the-influence-of-visual-salience-on-mora
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Running the Pipeline

### Step 1: Data Curation

Run the data curation script to load text narratives and generate/select images:
```bash
python code/01_data_curation.py
```

### Step 2: Human Coding (Ambiguity)

Run the human coding script to identify morally ambiguous scenarios (real or simulation mode):
```bash
python code/02_human_coding.py
```

### Step 3: Salience Manipulation

Run the salience manipulation script to generate low, medium, and high salience variants:
```bash
python code/03_salience_manipulation.py
```

### Step 4: Pilot Manipulation Check

Run the pilot manipulation check script to confirm narrative preservation (separate panel):
```bash
python code/04_manipulation_check.py
```

### Step 5: Survey Deployment (Pilot Mode)

Run the survey deployment script to collect real data (or simulation mode for testing):
```bash
python code/05_survey_deployment.py
```

### Step 6: Data Cleaning

Run the data cleaning script to exclude invalid participants:
```bash
python code/06_data_cleaning.py
```

### Step 7: Statistical Analysis

Run the statistical analysis script to perform LMM and generate results:
```bash
python code/07_statistical_analysis.py
```

### Step 8: Power Analysis

Run the power analysis script to compute a priori and post-hoc power:
```bash
python code/08_power_analysis.py
```

### Step 9: Report Generation

Run the report generation script to create the final report:
```bash
python code/09_report_generation.py
```

## Testing

Run the test suite to verify the pipeline:
```bash
pytest tests/
```

## Output

The final report will be generated in `data/results/report.md`. The report includes:
- Description of the methodology
- Results of the statistical analysis (LMM table, R² effect sizes, confidence intervals)
- Figures and visualizations
- Limitations and future work
- Power analysis results