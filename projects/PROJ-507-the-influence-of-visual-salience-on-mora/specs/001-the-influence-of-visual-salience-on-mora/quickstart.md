# Quickstart: The Influence of Visual Salience on Moral Judgments

## Prerequisites

- Python 3.11+
- Git
- (Optional) Docker for isolated survey hosting
- (Required) Human annotators for the annotation pipeline

## Installation

1. **Clone the Repository**:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-507-the-influence-of-visual-salience-on-mora
 ```

2. **Create Virtual Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Workflow

### Step 1: Data Ingestion & Pre-Screening
Run the pipeline to download a larger subset of COCO data (N=500) for pre-screening.

```bash
python code/dataset_loader.py --subset-size 500
```
*Output*: `data/raw/scenarios_pre_screen.csv`.

### Step 2: Human Annotation (Manual Step)
Run the annotation interface (or use a shared spreadsheet) to:
1. Filter for morally ambiguous scenarios (Dual-rater, κ ≥ 0.7).
2. Identify and validate 'non-causal' objects.
3. Export the final list to `data/raw/scenarios.csv`.

### Step 3: Stimulus Generation
Run the pipeline to generate manipulated images and compute validation metrics.

```bash
python code/stimulus_gen.py
```
*Output*: `data/processed/stimuli_manifest.csv` and images in `data/processed/images/`.

### Step 4: Naturalness Pre-test (Optional but Recommended)
Run a small pilot (N=20) to validate naturalness.

```bash
python code/pre_test.py
```
*Output*: Updates `naturalness_pass` in `stimuli_manifest.csv`.

### Step 5: Run the Survey
Start the local survey server for testing.

```bash
python code/survey_server.py
```
*Access*: Open ` in a browser.
*Note*: For public data collection, export the static HTML/JS from the server and deploy to a free hosting service (e.g., Vercel, Render).

### Step 6: Statistical Analysis
After collecting data, run the analysis script.

```bash
python code/analysis.py
```
*Output*: Console report with One-way ANOVA results, GLMM output, post-hoc tables, and a plot saved to `data/processed/analysis_report.pdf`.

## Verification

To verify the installation and data pipeline:

```bash
pytest tests/
```
This runs unit tests for image manipulation stats, **linkage validation tests** (Principle VII), and integration tests for the survey data flow.