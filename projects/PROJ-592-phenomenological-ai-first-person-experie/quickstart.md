# Phenomenological AI: First-Person Experience Modeling - Quick Start

This guide provides instructions for setting up the environment and running the automated science pipeline for modeling first-person experience in language models.

## Prerequisites

- Python 3.9+
- pip (Python package manager)
- Git

## Environment Setup

1. **Clone the repository** (if not already done):
 ```bash
 git clone <repository-url>
 cd projects/PROJ-592-phenomenological-ai-first-person-experie
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

 *Note: Ensure you have sufficient disk space for model downloads (TinyLlama ~2GB).*

4. **Verify installation**:
 ```bash
 python -c "import llama_cpp; print('llama-cpp-python installed')"
 python -c "import datasets; print('datasets installed')"
 ```

## Project Structure

- `code/`: Source code for generation, analysis, and validation
- `data/raw/`: Generated phenomenological reports and control corpus
- `data/processed/`: Computed metrics and statistical analysis results
- `data/qualitative/`: Human rater inputs and outputs
- `specs/`: Feature specifications and contracts
- `tests/`: Unit and integration tests

## Running the Pipeline

The main entry point is `code/main.py`. It supports three primary modes of operation corresponding to the user stories.

### Mode 1: Generation (User Story 1)

Generates the corpus of phenomenological reports using CPU-tractable models and four prompting strategies.

```bash
python code/main.py --task generate --config code/config.py
```

**Output**: `data/raw/generation_output.jsonl` (and related files per strategy)

**Options**:
- `--task generate`: Run the full generation pipeline
- `--task generate_control`: Run the control corpus generation
- `--config`: Path to configuration file (default: `code/config.py`)

### Mode 2: Analysis (User Story 2)

Computes Internal Consistency, Semantic Stability, and Marker Presence metrics, then performs statistical analysis.

```bash
python code/main.py --task analyze --config code/config.py
```

**Output**: `data/processed/validity_scores.csv`, `data/processed/statistical_results.json`

**Options**:
- `--task analyze`: Run the full analysis pipeline (metrics + stats)
- `--task stats`: Run only the statistical analysis on existing scores
- `--task sensitivity-kappa`: Run sensitivity analysis for Cohen's κ thresholds

### Mode 3: Validation (User Story 3)

Facilitates human evaluation, computes inter-rater reliability, and archives artifacts.

```bash
python code/main.py --task validate_human --config code/config.py
```

**Output**: `data/qualitative/ratings.csv`, `data/qualitative/anonymized_ratings.csv`

**Options**:
- `--task validate_human`: Run the human rating pipeline
- `--task select_validation_sample`: Select a stratified sample for human rating

### Full Pipeline

To run the entire pipeline end-to-end (Generation → Analysis → Validation):

```bash
python code/main.py --task full_pipeline --config code/config.py
```

**Expected Runtime**: ≤ 6 hours on free-tier CPU environments (as per T033).

## Troubleshooting

- **CUDA Errors**: Ensure you are running in a CPU-only environment. The primary CI path uses `TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF` which runs on CPU.
- **Import Errors**: Verify that `requirements.txt` dependencies are installed and that `code/` is in your `PYTHONPATH`.
- **Missing Data**: If output files are missing, check the logs in `logs/` for specific error messages during execution.

## Testing

Run unit tests to verify the implementation:

```bash
python -m pytest tests/unit/ -v
```

Run integration tests:

```bash
python -m pytest tests/integration/ -v
```

## Configuration

Edit `code/config.py` to adjust:
- Model paths and IDs
- Seed values for reproducibility
- Phenomenological marker dictionaries (sensory, temporal, intentional)
- Output paths and file names

## Reproducibility

All generated artifacts, seeds, and configurations are archived for reproducibility. Run the archiver script to create a reproducible package:

```bash
python code/utils/archiver.py
```