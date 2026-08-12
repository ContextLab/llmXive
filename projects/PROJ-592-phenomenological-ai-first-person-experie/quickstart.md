# Phenomenological AI: First-Person Experience Modeling - Quick Start

## Overview

This pipeline generates phenomenological-style reports using LLMs, computes structural metrics, and performs statistical analysis to evaluate first-person experience modeling.

## Prerequisites

- Python 3.10+
- 16GB+ RAM recommended for local models
- CPU-only execution supported for TinyLlama

## Installation

```bash
# Clone and setup
git clone <repository-url>
cd PROJ-592-phenomenological-ai-first-person-experie

# Create virtual environment
python -m venv.venv
source.venv/bin/activate # On Windows:.venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Download TinyLlama model (required for generation)
mkdir -p models
# Download from: https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF
# Save as: models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

## Quick Start Commands

### 1. Generation Phase

Generate phenomenological reports using different prompting strategies:

```bash
python code/main.py --task generate --config code/config.yaml --limit 100
```

This will create samples in `data/raw/` with at least 80 samples per strategy (Direct, Hypothetical, Comparative, Role-play).

### 2. Control Corpus Generation

Generate technical report control samples:

```bash
python code/main.py --task generate_control --config code/config.yaml
```

### 3. Analysis Phase

Compute consistency, stability, and marker metrics:

```bash
python code/main.py --task analyze --config code/config.yaml
```

### 4. Statistical Analysis

Run statistical tests and generate reports:

```bash
python code/main.py --task stats --config code/config.yaml
```

Output: `data/processed/stats_report.json` and `data/processed/validity_scores.csv`

### 5. Validation Phase

Select stratified samples for human rating:

```bash
python code/main.py --task validate_human --config code/config.yaml
```

### 6. Full Pipeline

Execute the complete pipeline end-to-end:

```bash
python code/main.py --task full --config code/config.yaml
```

**Expected Runtime**: ≤6 hours on free-tier hardware with `--limit 100`

## Configuration

Edit `code/config.yaml` to customize:
- Model paths
- Generation parameters (temperature, tokens)
- Analysis thresholds
- Output paths

## Output Artifacts

After successful execution:
- `data/raw/`: Generated phenomenological reports (JSON)
- `data/processed/validity_scores.csv`: Computed metrics
- `data/processed/stats_report.json`: Statistical analysis results
- `data/qualitative/`: Stratified samples for validation

## Validation (T033)

To validate the pipeline executes within 6 hours:

```bash
time python code/main.py --task generate --config code/config.yaml --limit 100
```

Verify:
- Exit code 0
- Total time < 6 hours
- `data/raw/` contains ≥80 samples per strategy
- `data/processed/validity_scores.csv` exists after analysis
