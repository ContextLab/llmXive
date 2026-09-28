# Quickstart Guide: Visual Crowding & Facial Emotion Recognition

This guide walks you through setting up the environment and running the full pipeline for the study on the impact of visual crowding on facial emotion recognition accuracy.

## Prerequisites

- Python 3.9+
- pip
- A modern web browser (for viewing reports)
- At least 14 GB of free disk space (for dataset and intermediate artifacts)
- At least 8 GB RAM (recommended)

## 1. Environment Setup

Clone the repository and navigate to the project root:

```bash
git clone <repository-url>
cd PROJ-357-the-impact-of-visual-crowding-on-facial-
```

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configuration

The project uses `code/config.py` to manage environment variables and random seeds.
Ensure your environment is set up correctly. The default RAVDESS dataset URL is verified in `code/utils/verify_ravdess.py`.

## 3. Running the Pipeline

The pipeline consists of several stages. You can run them sequentially or execute the master script.

### Option A: Run the Master Pipeline Script

The master script orchestrates the entire flow from data download to final report generation.

```bash
python code/run_full_pipeline.py
```

*Note: If `run_full_pipeline.py` does not exist, run the stages manually as described below.*

### Option B: Run Stages Manually

#### Stage 1: Data Download & Preparation
Downloads the RAVDESS dataset and extracts frames.

```bash
python code/utils/download.py
python code/utils/frame_extractor.py
```

#### Stage 2: Stimuli Generation
Generates visual crowding stimuli with controlled parameters.

```bash
python code/utils/stimulus_gen.py
python code/utils/stimuli_manifest.py
python code/utils/manifest_validator.py
```

#### Stage 3: Clutter Metrics Computation
Computes visual clutter metrics for generated stimuli.

```bash
python code/utils/clutter_metrics.py
```

#### Stage 4: Synthetic Human Data Collection
Generates synthetic pilot data mimicking human judgments.

```bash
python code/analysis/pilot_runner.py
python code/analysis/aggregate_judgments.py
```

#### Stage 5: Analysis & Reporting
Fits the GLMM model and generates the final report.

```bash
python code/analysis/glmm_model.py
python code/analysis/reporting.py
```

## 4. Output Artifacts

After successful completion, the following artifacts will be available:

- **Stimuli**: `data/interim/stimuli/` (Generated images)
- **Manifest**: `data/interim/stimuli_manifest.json`
- **Clutter Metrics**: `data/processed/clutter_metrics.csv`
- **Human Judgments**: `data/processed/human_judgments.csv`
- **Regression Results**: `data/processed/regression_results.json`
- **Model Config**: `artifacts/model_config.yaml`
- **Final Report**: `artifacts/final_report.md` (or similar, check `code/analysis/reporting.py`)

## 5. Verification

To verify the integrity of the generated artifacts, run the hygiene check:

```bash
python code/utils/hygiene.py
```

This updates the state file with SHA256 checksums for all data and artifact directories.

## Troubleshooting

- **Memory Errors**: If you encounter memory errors during clutter metric computation, ensure you have at least 8GB RAM. The `clutter_metrics.py` script includes chunked processing logic.
- **Dataset Download Failures**: Ensure you have a stable internet connection. The script attempts to fetch from the verified HuggingFace URL.
- **GLMM Convergence**: If the GLMM fails to converge, the pipeline automatically falls back to a fixed-effects only model and logs a warning.

## Next Steps

Once the pipeline completes, review the `artifacts/final_report.md` for the associational analysis results and the `data/processed/validation_report.json` for metric correlations.