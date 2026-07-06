# Quickstart: The Influence of Simulated Social Validation on Neural Responses to Novel Information

## Prerequisites

- Python 3.11+
- 7 GB+ RAM available
- Internet connection (for dataset download)

## Installation

1. **Clone the repository** and navigate to the project directory.
   ```bash
   git clone <repo-url>
   cd projects/PROJ-496-the-influence-of-simulated-social-valida
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

## Running the Pipeline

The pipeline is executed in three stages.

### Stage 1: Dataset Search
Run the search script to identify eligible datasets.
```bash
python code/main.py --stage search
```
- **Output**: `data/results/search_results.csv`.
- **Expected**:
  - If **Eligible**: Lists the dataset ID.
  - If **Partial** or **None**: Outputs "No eligible datasets found" and exits with code 0 (Negative Finding). The pipeline terminates here.

### Stage 2: Preprocessing & Extraction (Only if Eligible Dataset Found)
If an Eligible dataset is found, run preprocessing.
```bash
python code/main.py --stage preprocess --dataset-id <ID>
```
- **Output**: `data/processed/p300_measures.csv`.
- **QC Check**: The script will automatically flag participants failing the [deferred] retention or 2-15 µV amplitude criteria. If QC fails, the pipeline aborts and generates a Negative Finding Report.

### Stage 3: Analysis & Reporting (Only if QC Passed)
Run the statistical model.
```bash
python code/main.py --stage analyze
```
- **Output**:
  - **Primary Path**: `data/results/model_results.json` (LMM + Bayes Factors), `data/results/report.pdf`.
  - **Negative Finding Path**: `data/results/negative_finding_report.json`, `data/results/negative_finding_report.pdf`.

## Verification

- **Check Data Integrity**:
  ```bash
  python code/main.py --stage verify-checksums
  ```
- **Run Tests**:
  ```bash
  pytest tests/
  ```

## Troubleshooting

- **Memory Error**: Reduce the number of subjects processed or increase RAM. The pipeline is optimized for ~7 GB RAM.
- **No Dataset Found**: This is a valid outcome. Review `logs/search.log` for details. The project will generate a "Negative Finding" report and exit with code 0.
- **Bayes Factor Not Significant**: The pipeline automatically reports the Bayes Factor. If BF < 3 and p > 0.05, the report will state "No significant effect found" and proceed to the sensitivity analysis.
- **QC Failed**: If the dataset fails the QC criteria (SC-002), the pipeline will abort and generate a "Negative Finding" report explaining the failure.
