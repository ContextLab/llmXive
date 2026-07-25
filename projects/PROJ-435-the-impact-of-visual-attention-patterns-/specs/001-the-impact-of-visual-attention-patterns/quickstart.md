# Quickstart: The Impact of Visual Attention Patterns on Susceptibility to Misleading Headlines

## Prerequisites

- Python 3.11+
- Git
- Access to Hugging Face datasets (no authentication required for public datasets)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd projects/PROJ-435-the-impact-of-visual-attention-patterns-
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

The pipeline is executed via the `code/cli/run_pipeline.py` script.

1. **Download and preprocess data**:
   ```bash
   python code/cli/run_pipeline.py --stage preprocess
   ```
   This step:
   - Fetches data from Hugging Face.
   - Applies I-VT fixation detection.
   - Filters participants with >20% data loss.
   - Maps ROIs.
   - Outputs `data/derived/preprocessed_gaze.csv`.

2. **Calculate valence**:
   ```bash
   python code/cli/run_pipeline.py --stage valence
   ```
   This step:
   - Calculates emotional valence using NRC (fallback to VADER if coverage < 50% for ALL headlines).
   - Logs switches to `output/runtime.log`.
   - Outputs `data/derived/valence_scores.csv`.

3. **Merge and analyze**:
   ```bash
   python code/cli/run_pipeline.py --stage analyze
   ```
   This step:
   - Merges datasets.
   - Runs mixed-effects regression.
   - Applies Holm-Bonferroni correction.
   - Outputs `data/processed/regression_results.json`.

4. **Robustness check**:
   ```bash
   python code/cli/run_pipeline.py --stage robustness
   ```
   This step:
   - Sweeps fixation duration cutoffs (50ms, 100ms, 150ms).
   - Outputs `data/processed/robustness_results.json`.

## Testing

Run the test suite to verify the pipeline:
```bash
pytest tests/
```
This includes:
- Unit tests for preprocessing and valence calculation.
- Integration tests for the full pipeline.
- Contract validation tests against `contracts/` schemas.

## Troubleshooting

- **Data Fetching Errors**: Ensure you have internet access and that the Hugging Face URLs are correct.
- **Memory Errors**: If the dataset is too large, the pipeline will automatically sample a subset. Check `output/runtime.log` for sampling details.
- **Valence Switch**: If NRC coverage is low, the pipeline will switch to VADER. Check `output/runtime.log` for the switch log.