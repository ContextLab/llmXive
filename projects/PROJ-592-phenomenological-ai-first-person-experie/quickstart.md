# Phenomenological AI: First-Person Experience Modeling - Quick Start Guide

This guide provides instructions for setting up the environment and running the automated science pipeline for phenomenological report generation and analysis.

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- At least 4GB of available RAM (8GB+ recommended for analysis phases)
- CPU-only execution (no GPU required)

## Environment Setup

1. **Clone the repository** and navigate to the project directory:
 ```bash
 cd PROJ-592-phenomenological-ai-first-person-experie
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

 *Note: If you encounter permission errors, ensure you are using a virtual environment.*

4. **Verify installation**:
 ```bash
 python -c "import llama_cpp; print('llama-cpp-python installed successfully')"
 ```

## Project Structure

```
code/ # Source code
 config.py # Configuration and marker definitions
 main.py # Pipeline orchestration
 generation/ # Data generation scripts
 analysis/ # Metric computation and statistical analysis
 validation/ # Human rating and validation scripts
 utils/ # Utility functions (logging, I/O, archiving)
data/
 raw/ # Generated phenomenological reports
 processed/ # Computed metrics and statistical results
 qualitative/ # Human rating data
specs/ # Feature specifications and contracts
tests/ # Unit and integration tests
```

## CLI Usage Examples

The main pipeline is controlled via `code/main.py` with the `--mode` argument.

### 1. Generation Mode

Generate the corpus of phenomenological reports using the TinyLlama model and four prompting strategies.

```bash
python code/main.py --mode generation
```

**What it does:**
- Loads 20 base prompts from `data/prompts/base_prompts.json`
- Applies 4 prompting strategies (Direct, Hypothetical, Comparative, Role-play)
- Generates ~80 samples per prompt per strategy using `TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF`
- Outputs to `data/raw/phenomenological_reports.json`

**Expected duration:** 2-4 hours on CPU (depending on hardware)

### 2. Control Corpus Generation

Generate a control corpus from real-world text for discriminant validity testing.

```bash
python code/main.py --mode generate_control
```

**What it does:**
- Downloads samples from the `arxiv_nlp` dataset
- Generates ≥80 control samples
- Outputs to `data/raw/control_corpus.json`

### 3. Analysis Mode

Compute phenomenological metrics (Consistency, Stability, Markers) on generated reports.

```bash
python code/main.py --mode analysis
```

**What it does:**
- Runs consistency analysis using NLI model (`cross-encoder/stsb-distilroberta-base`)
- Computes semantic stability via embedding cosine similarity
- Counts phenomenological markers (sensory, temporal, intentional)
- Outputs to `data/processed/metrics.json`

**Expected duration:** 30-60 minutes

### 4. Statistics Mode

Perform statistical analysis and hypothesis testing on computed metrics.

```bash
python code/main.py --mode stats
```

**What it does:**
- Checks normality (Shapiro-Wilk) and homogeneity (Levene) assumptions
- Runs ANOVA + FDR correction + Tukey HSD (if assumptions met)
- Runs Kruskal-Wallis test (if assumptions violated)
- Performs sensitivity analysis on metric weights
- Outputs to `data/processed/validity_scores.csv` and `data/processed/statistical_results.json`

**Expected duration:** 10-20 minutes

### 5. Validation Mode

Prepare samples for human evaluation and compute inter-rater reliability.

```bash
python code/main.py --mode validate
```

**What it does:**
- Stratified sampling of reports for human rating
- Loads validation rubric from `code/validation/rubric.md`
- Calculates Cohen's κ for inter-rater agreement
- Outputs to `data/qualitative/ratings.csv`

**Expected duration:** 5-10 minutes (excluding human rating time)

### 6. Full Pipeline

Execute the entire pipeline from generation to validation.

```bash
python code/main.py --mode full_pipeline
```

**What it does:**
- Runs all phases sequentially: Generation → Control → Analysis → Stats → Validation
- Ensures data dependencies are met between phases
- Outputs all artifacts to their respective directories

**Expected duration:** 3-6 hours total

## Troubleshooting

### CUDA/GPU Errors
This project is designed for CPU-only execution. If you encounter CUDA errors:
- Ensure you are using the TinyLlama-1.1B-GGUF model (not 7B models)
- Verify `llama-cpp-python` was installed with CPU support: `pip install llama-cpp-python --force-reinstall --no-binary llama-cpp-python`

### Import Errors
If you see `ImportError: cannot import name 'X' from 'Y'`:
- Ensure you are running from the project root directory
- Verify `code/` is in your Python path: `PYTHONPATH=code:$PYTHONPATH python code/main.py`

### Memory Errors
If the process is killed due to memory:
- Reduce `MAX_SAMPLES_PER_PROMPT` in `code/config.py`
- Close other memory-intensive applications
- Use a machine with ≥8GB RAM for the analysis phase

## Output Verification

After running the pipeline, verify the following outputs exist:

- `data/raw/phenomenological_reports.json` (≥6400 samples: 20 prompts × 4 strategies × 80 samples)
- `data/raw/control_corpus.json` (≥80 samples)
- `data/processed/metrics.json` (Consistency, Stability, Marker scores)
- `data/processed/validity_scores.csv` (Statistical test results)
- `data/qualitative/ratings.csv` (Human rating data, if validated)

## Next Steps

1. Run the full pipeline to generate initial results
2. Review `data/processed/statistical_results.json` for hypothesis test outcomes
3. Conduct human validation using the rubric in `code/validation/rubric.md`
4. Generate the reproducibility archive with `python code/utils/archiver.py`

For detailed API documentation, refer to the docstrings in each module under `code/`.