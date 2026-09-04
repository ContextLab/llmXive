# Quickstart: The Influence of Chatbot Politeness on User-Perceived Quality

## Prerequisites

- Python 3.11+
- `pip`
- Hugging Face CLI (optional, for authentication)
- Sufficient disk space (for datasets and model cache)
- Sufficient RAM recommended (for processing)

## Installation

1. **Clone and Setup**
   ```bash
   cd projects/PROJ-755-the-influence-of-chatbot-politeness-on-u
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r code/requirements.txt
   ```

3. **Configure Environment**
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your Hugging Face token (required for dataset download):
     ```
     HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
     ```

## Running the Pipeline

### 1. Download and Process Data
```bash
python code/data/loader.py --datasets YCAI3/HCI_P2,facebook/Persona-Chat,daanelson/EmpatheticDialogues
python code/data/preprocess.py --input data/raw/merged_dataset.zip --output data/processed/dialogues_with_scores.csv
```
*This will download all three datasets, filter incomplete dialogues, compute politeness scores, and save the processed CSV.*

### 2. Run Power Analysis (Optional)
```bash
python code/analysis/power_analysis.py --input data/processed/dialogues_with_scores.csv --output results/power_analysis_report.json
```
*Estimates the Minimum Detectable Effect (MDE) and power for the current sample size.*

### 3. Run Primary Analysis (CLMM)
```bash
python code/analysis/clmm.py --input data/processed/dialogues_with_scores.csv --output results/clmm_results.csv
```
*Fits the Cumulative Link Mixed-Effects model and outputs coefficients, p-values, and confidence intervals.*

### 4. Run Robustness and Subgroup Analysis
```bash
python code/analysis/robustness.py --input data/processed/dialogues_with_scores.csv --output results/robustness_results.csv
```
*Runs lexicon-based analysis and subgroup splits (age/gender) if sample sizes permit.*

### 5. Validate Outputs
```bash
python code/utils/schema_validator.py --schema contracts/output.schema.yaml --input results/clmm_results.csv
```
*Validates that the output CSV matches the expected schema.*

## Expected Outputs

- `data/processed/dialogues_with_scores.csv`: Cleaned dataset with politeness scores.
- `results/clmm_results.csv`: Primary model results.
- `results/robustness_results.csv`: Secondary model results.
- `results/power_analysis_report.json`: Power and MDE estimates.
- `logs/pipeline.log`: Detailed execution logs, including filtering counts and convergence diagnostics.

## Troubleshooting

- **Dataset Download Failed**: Ensure `HF_TOKEN` is set in `.env` and the token is valid.
- **Model Convergence Failure**: Check `logs/pipeline.log` for diagnostic messages. The script will automatically attempt a simplified model (without random effects) if the full CLMM fails.
- **Memory Error**: The pipeline uses streaming by default. If memory is still an issue, reduce the `--batch_size` in `preprocess.py`.
- **Subgroup Analysis Skipped**: If a subgroup has < 30 samples, it will be logged and skipped (as per FR-006).