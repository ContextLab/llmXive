# Quickstart: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

## Prerequisites

- Python 3.11+
- Git
- Hugging Face CLI (optional, for dataset streaming)
- Access to GitHub Actions (for CI) or local environment

## Setup

1. **Clone Repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-507-the-influence-of-visual-salience-on-mora
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

3. **Download Datasets** (if not streaming):
   ```bash
   # Example for MoralD subset (adjust with actual URL)
   huggingface-cli download moral_d --local-dir data/raw/moral_d_subset
   ```

4. **Run Pilot Power Analysis** (Phase 0):
   ```bash
   python code/00_pilot_power_analysis.py --config config/pilot.yaml
   ```

5. **Run Human Coding Simulation** (for pilot):
   ```bash
   python code/02_human_coding.py --config config/human_coding.yaml
   ```

6. **Generate Stimuli**:
   ```bash
   python code/03_manipulate_stimuli.py --config config/manipulation.yaml
   ```

7. **Run Survey Pilot** (simulated):
   ```bash
   python code/04_survey_deployment.py --mode pilot --num-participants 10
   ```

8. **Clean Data and Run Analysis**:
   ```bash
   python code/05_data_cleaning.py --input data/processed/responses.csv --output data/processed/cleaned_responses.csv
   python code/06_analysis_clmm.py --input data/processed/cleaned_responses.csv --output data/processed/results.json
   ```

## Configuration

- **`config/pilot.yaml`**: Pilot parameters for power analysis.
- **`config/human_coding.yaml`**: Ambiguity thresholds (mean ≥3.5, κ ≥0.6).
- **`config/manipulation.yaml`**: Salience levels, contrast/brightness parameters.
- **`config/pre_registration.yaml`**: Precision threshold and other pre-registered values.
- **`config/analysis.yaml`**: CLMM settings, correction methods.

## Validation

- **Stimulus Integrity**: Check `data/processed/stimuli/` for CLIP similarity ≥0.95, RMS contrast ≥15%, and Moral Intent Preservation score ≥0.90.
- **Data Cleaning**: Verify excluded participants in `data/processed/cleaned_responses.csv`.
- **Analysis Output**: Confirm CLMM table with odds ratios and p-values in `data/processed/results.json`.

## Troubleshooting

- **CLIP/BERT Slow**: Use `device="cpu"`; if too slow, offload to Kaggle GPU.
- **Dataset Not Found**: Use alternative open dataset (e.g., COCO) with manual annotation or synthetic generation.
- **CLMM Convergence Failure**: Switch to robust alternative (LMM/bootstrap).