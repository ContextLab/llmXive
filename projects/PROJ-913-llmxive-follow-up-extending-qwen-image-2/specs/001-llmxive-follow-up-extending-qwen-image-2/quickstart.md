# Quickstart: llmXive Follow-up: OPD Generalization Gap in Unified Diffusion

## Prerequisites

- Python 3.11+
- GB+ RAM (Free-tier GitHub Actions compatible)
- Access to Hugging Face Hub (no token required for public models, but recommended for rate limits)
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-913-llmxive-follow-up-extending-qwen-image-2
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

The pipeline is orchestrated by `code/main.py`. It performs the following steps in order:

1. **Data Acquisition**: Downloads models and curates prompts.
2. **Leakage Check**: Validates OOD set integrity.
3. **Inference**: Generates images (CPU-only).
4. **Scoring**: Evaluates images with VLMs.
5. **Analysis**: Computes statistics and generates the report.

### Execute Full Pipeline

```bash
python code/main.py
```

### Configuration

Edit `code/config.py` to adjust:
- `NUM_PROMPTS_ID`: Number of ID prompts (default: a representative sample size

The specific value to remove/generalize: 'a representative sample size'

Rewritten passage:).
- `NUM_PROMPTS_OOD`: Number of OOD prompts (default:).
- `IMAGES_PER_PROMPT`: Number of images per prompt (default: a specified count).
- `LEAKAGE_THRESHOLD`: Cosine similarity threshold (default:).
- `BOOTSTRAP_ITERATIONS`: Number of bootstrap iterations (default: a representative sample size).

### Output

- **Images**: `outputs/base_model/`, `outputs/rl_unified_model/`
- **Scores**: `data/processed/scores.jsonl`
- **Report**: `data/results/stats.json`
- **Logs**: `logs/pipeline.log`

## Troubleshooting

- **OOM Error**: Reduce `IMAGES_PER_PROMPT` or `NUM_PROMPTS_OOD` in `config.py`.
- **Leakage Detected**: The pipeline will abort if the OOD set fails the cosine similarity check. Re-run to trigger re-curation.
- **Download Failure**: The pipeline retries up to 3 times with exponential backoff.

## Verification

To verify the pipeline ran correctly:
1. Check `data/results/stats.json` for the `generalization_gap` and `p_value`.
2. Ensure `outputs/` contains images for both models.
3. Confirm `logs/pipeline.log` has no `[CRITICAL]` errors.
