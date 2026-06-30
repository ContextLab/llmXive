# Phenomenological AI: First-Person Experience Modeling - Quick Start Guide

This guide provides the essential steps to set up the environment and run the
automated science pipeline for generating and analyzing phenomenological reports.

## Prerequisites

- Python 3.11+
- ≥8GB RAM (for CPU-only execution)
- 20GB+ free disk space for model weights and generated data

## 1. Environment Setup

### Clone and Navigate
```bash
git clone <repository-url>
cd PROJ-592-phenomenological-ai-first-person-experie
```

### Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### Install Dependencies
The project uses pinned dependencies defined in `code/requirements.txt`.
```bash
pip install --upgrade pip
pip install -r code/requirements.txt
```

### Verify Installation
Ensure `llama-cpp-python` is correctly installed for CPU inference:
```bash
python -c "import llama_cpp; print(llama_cpp.__version__)"
```

## 2. Project Initialization

Run the initialization script to create the required directory structure:
```bash
python scripts/init_project.py
```

This creates:
- `code/`: Source code
- `data/raw/`: Generated samples
- `data/processed/`: Analyzed metrics
- `data/qualitative/`: Human ratings
- `tests/unit/`, `tests/integration/`: Test suites
- `specs/contracts/`: Data schemas

## 3. Running the Pipeline

The main entry point is `code/main.py`. It supports three distinct modes
corresponding to the project's user stories.

### Mode 1: Generation (User Story 1)
Generates the corpus of phenomenological reports using TinyLlama-1.1B (CPU-safe).
This step creates the raw data required for analysis.

```bash
python code/main.py --mode generation
```

**What it does:**
- Loads 20 base prompts from `data/prompts/base_prompts.json`
- Applies 4 prompting strategies (Direct, Hypothetical, Comparative, Role-play)
- Generates ~80 samples per strategy (totaling ~6,400 samples) [UNRESOLVED-CLAIM: c_4ad78dba — status=not_enough_info]
- Saves outputs to `data/raw/phenomenological_reports.json`
- Generates a control corpus from `datasets.load_dataset("arxiv_nlp")` [UNRESOLVED-CLAIM: c_57053a7a — status=not_enough_info]

**Output:** `data/raw/phenomenological_reports.json`, `data/raw/control_corpus.json`

### Mode 2: Analysis (User Story 2)
Computes validity metrics (Consistency, Stability, Markers) and performs statistical analysis.
Requires generation data to be present.

```bash
python code/main.py --mode analysis
```

**What it does:**
- Runs Consistency Analysis (NLI-based contradiction detection)
- Runs Stability Analysis (embedding cosine similarity)
- Runs Marker Analysis (sensory, temporal, intentional keyword counts)
- Orchestrates statistical tests (ANOVA/Kruskal-Wallis, FDR, Tukey)
- Performs sensitivity analysis on metric weights

**Output:** `data/processed/validity_scores.csv`, `data/processed/statistical_results.json`, `data/processed/experience_traces.json`

### Mode 3: Validation (User Story 3)
Prepares data for human evaluation and archives artifacts for reproducibility.

```bash
python code/main.py --mode validate
```

**What it does:**
- Stratifies reports for representative sampling
- Generates anonymized rating sheets for human raters
- Computes inter-rater reliability (Cohen's κ)
- Creates a reproducibility archive (`data/qualitative/archive.tar.gz`)

**Output:** `data/qualitative/rating_sheets.csv`, `data/qualitative/archive.tar.gz`

## 4. Full Pipeline Execution

To run the entire pipeline sequentially (Generation → Analysis → Validation):

```bash
python code/main.py --mode all
```

**Expected Duration:** ≤6 hours on a standard CPU (free-tier cloud instance).

## 5. Testing

Run unit tests to verify implementation correctness:

```bash
pytest tests/unit/ -v
```

Run integration tests to verify end-to-end data flow:

```bash
pytest tests/integration/ -v
```

## 6. Troubleshooting

- **CUDA Errors:** Ensure `llama-cpp-python` is installed without CUDA support.
 The pipeline is designed for CPU-only execution.
- **Memory Errors:** If running locally with 7B models (T012), ensure ≥16GB RAM.
 The primary CI path uses TinyLlama-1.1B which fits in ≤4GB RAM [UNRESOLVED-CLAIM: c_7204de6d — status=not_enough_info].
- **Missing Data:** If `data/raw/` is empty, run `--mode generation` first.
- **Schema Validation:** All outputs are validated against schemas in `specs/contracts/`.
 If validation fails, check the logs for specific field errors.

## 7. Configuration

Edit `code/config.py` to customize:
- Model paths (default: `TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF`)
- Seed values for reproducibility
- Phenomenological marker dictionaries (sensory, temporal, intentional)
- Output paths and logging levels

## 8. Next Steps

- Review `research.md` for the theoretical framework and hypothesis definitions.
- Examine `data-model.md` for schema details and data flow diagrams.
- Read `specs/contracts/` for precise data format specifications.
- Consult `code/validation/rubric.md` for the human rating criteria.