# Quickstart: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

## Prerequisites
- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local environment with same constraints).

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/your-repo.git
   cd your-repo
   ```

2. **Set up the virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/requirements.txt
   ```

## Running the Pipeline

### 1. Ingest Data & Generate Stimuli (Phase 1)
```bash
python projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/01_data_ingestion.py
python projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/02_human_coding.py
python projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/03_stimulus_generation.py
```
- **Note**: This pipeline ingests **real images** from the verified Visual Genome dataset.
- The `02_human_coding.py` script manages the protocol for recruiting annotators to validate moral ambiguity (FR-008).
- This will create `data/processed/stimuli/` with low/medium/high variants for validated images.

### 2. Load & Clean Survey Data (Phase 2)
```bash
python projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/04_survey_data_loader.py
python projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/05_data_cleaning.py
```
- Loads `data/raw/survey_responses.csv` (from real pilot data collection).
- Filters straight-liners.
- Outputs `data/processed/cleaned_responses.csv`.

### 3. Run Statistical Analysis (Phase 3)
```bash
python projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/06_statistical_analysis.py
```
- Runs repeated-measures ANOVA on the real pilot data.
- Outputs `data/results/analysis_results.json`.

### 4. Generate Report (Phase 4)
```bash
python projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/07_report_generation.py
```
- Generates a summary report.

## Testing
Run the test suite:
```bash
pytest tests/
```

## Troubleshooting
- **Memory Error**: Reduce the number of images in the `data/raw/` directory.
- **Import Error**: Ensure the virtual environment is activated and `requirements.txt` is installed.
