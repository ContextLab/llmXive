# Quick Start Guide: Phenomenological AI First-Person Experience Modeling

This guide provides instructions for setting up the environment and running the
phenomenological AI research pipeline.

## Prerequisites

- Python 3.10 or higher
- pip package manager
- At least 8GB RAM (16GB recommended for local 7B models)
- CPU-only execution (no GPU required for primary CI path)

## Environment Setup

### 1. Clone and Navigate to Project

```bash
cd projects/PROJ-592-phenomenological-ai-first-person-experie
```

### 2. Create Virtual Environment

```bash
python -m venv.venv
source.venv/bin/activate # On Windows:.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r code/requirements.txt
```

### 4. Download Required Models (Optional - for local execution)

For the primary CI pipeline (TinyLlama), the model will be downloaded automatically.
For local 7B models (optional):

```bash
# Download TinyLlama GGUF (primary CI model)
# This will be handled automatically by runner.py

# For local 7B models (requires 16GB+ RAM)
# Follow instructions in runner_local.py
```

## Running the Pipeline

The main entry point is `code/main.py`. Use the `--mode` flag to select the
pipeline phase.

### Generation Mode

Generate phenomenological reports using the configured model and prompting strategies.

```bash
python code/main.py --mode generation --config code/config.py
```

This will:
- Load base prompts from `data/prompts/base_prompts.json`
- Apply four prompting strategies (Direct, Hypothetical, Comparative, Role-play)
- Generate ~80 samples per prompt per strategy
- Save outputs to `data/raw/`

### Analysis Mode

Compute phenomenological metrics (Consistency, Stability, Marker Presence).

```bash
python code/main.py --mode analysis --config code/config.py
```

This will:
- Load generated reports from `data/raw/`
- Compute internal consistency using NLI models
- Calculate semantic stability via embeddings
- Count phenomenological markers
- Save metrics to `data/processed/validity_scores.csv`

### Validation Mode

Perform statistical analysis and prepare for human validation.

```bash
python code/main.py --mode validate --config code/config.py
```

This will:
- Run statistical tests (ANOVA/Kruskal-Wallis)
- Apply FDR correction and Tukey HSD post-hoc tests
- Perform sensitivity analysis
- Prepare stratified samples for human rating

### Full Pipeline

Run the complete pipeline from generation to validation.

```bash
python code/main.py --mode full --config code/config.py
```

## Individual Task Execution

You can also run individual components directly:

### Generate Control Corpus

```bash
python code/generation/control_corpus.py
```

### Run Consistency Analysis

```bash
python code/analysis/consistency.py
```

### Run Stability Analysis

```bash
python code/analysis/stability.py
```

### Run Marker Analysis

```bash
python code/analysis/markers.py
```

### Run Statistical Analysis

```bash
python code/analysis/stats.py
```

### Run Sensitivity Analysis

```bash
python code/analysis/sensitivity_analysis.py
```

### Run Human Rater Preparation

```bash
python code/validation/human_rater.py
```

## Output Files

After successful execution, you should find:

- `data/raw/phenomenological_reports.json` - Generated reports
- `data/raw/control_corpus.json` - Control samples
- `data/processed/validity_scores.csv` - Computed metrics
- `data/qualitative/` - Human ratings (when completed)
- `figures/` - Analysis plots (when generated)

## Troubleshooting

### CUDA Errors

The primary pipeline is designed for CPU-only execution. If you encounter CUDA errors:
- Ensure you're using the TinyLlama model (not 7B models)
- Check that `llama-cpp-python` is installed correctly
- Verify no GPU drivers are being invoked

### Memory Errors

- For 7B models: Ensure you have at least 16GB RAM
- For TinyLlama: 8GB RAM should be sufficient
- Reduce batch sizes if necessary

### Missing Data Files

- Run `python scripts/init_project.py` to create directory structure
- Ensure `data/prompts/base_prompts.json` exists
- Check that all required datasets are accessible

## Verification

To verify the pipeline is working correctly:

```bash
# Run a small subset
python code/main.py --mode generation --config code/config.py
python code/main.py --mode analysis --config code/config.py
python code/main.py --mode validate --config code/config.py

# Check output files exist
ls -la data/raw/
ls -la data/processed/
```

## Expected Runtime

- Generation: ~2-4 hours (depending on sample count)
- Analysis: ~30 minutes
- Validation: ~15 minutes
- Full pipeline: ≤6 hours on free-tier resources

## Next Steps

1. Review `research.md` for methodological details
2. Check `specs/contracts/` for data schemas
3. Read `code/validation/rubric.md` for human rating criteria
4. Explore `data-model.md` for entity relationships
