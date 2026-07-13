# Phenomenological AI: First-Person Experience Modeling - Quick Start

This guide provides instructions for setting up the environment and running the pipeline.

## Environment Setup

### Prerequisites

- Python 3.9+
- pip (package manager)
- Access to a CPU-only environment (GPU is not required for the primary CI pipeline)

### Installation

1. Clone the repository and navigate to the project root:
 ```bash
 git clone <repository-url>
 cd PROJ-592-phenomenological-ai-first-person-experie
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

 **Note**: The primary CI pipeline uses `TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF` (4-bit quantized) via `llama-cpp-python`. This model is optimized for CPU execution.

3. Verify the installation:
 ```bash
 python -c "import llama_cpp; print(llama_cpp.__version__)"
 ```

## CLI Usage

The main entry point for the pipeline is `code/main.py`. It supports several modes of operation via the `--task` argument.

### Available Tasks

- `generate`: Generate phenomenological reports using TinyLlama and four prompting strategies.
- `generate_control`: Generate control samples from the arxiv_nlp dataset.
- `analyze`: Compute consistency, stability, and marker metrics on generated reports.
- `stats`: Perform statistical analysis (ANOVA/Kruskal-Wallis) on validity scores.
- `validate_human`: Prepare data for human validation (requires `code/validation/rubric.md`).
- `sensitivity-kappa`: Analyze robustness of conclusions across kappa thresholds.
- `archive`: Package all artifacts for reproducibility.
- `full`: Run the entire pipeline from generation to archiving.

### Basic Commands

#### 1. Generation Mode

Generate the corpus of phenomenological reports:

```bash
python code/main.py --task generate --config code/config.py
```

This will:
- Load 20 base prompts from `data/prompts/base_prompts.json`.
- Apply 4 prompting strategies (Direct, Hypothetical, Comparative, Role-play).
- Generate ~80 samples per strategy per prompt (totaling a substantial dataset).
- Save outputs to `data/raw/`.

#### 2. Control Corpus Mode

Generate control samples for discriminant validity:

```bash
python code/main.py --task generate_control --config code/config.py
```

This will:
- Load samples from `datasets.load_dataset("arxiv_nlp")`.
- Save control samples to `data/raw/control_corpus.json`.

#### 3. Analysis Mode

Compute validity metrics (Consistency, Stability, Markers):

```bash
python code/main.py --task analyze --config code/config.py
```

This will:
- Load generated reports from `data/raw/`.
- Compute metrics using `code/analysis/consistency.py`, `code/analysis/stability.py`, and `code/analysis/markers.py`.
- Save results to `data/processed/validity_scores.csv`.

#### 4. Statistical Analysis Mode

Run statistical tests on validity scores:

```bash
python code/main.py --task stats --config code/config.py
```

This will:
- Load `data/processed/validity_scores.csv`.
- Perform Shapiro-Wilk and Levene tests.
- Run ANOVA + FDR + Tukey (if assumptions hold) or Kruskal-Wallis (if violated).
- Save statistical results to `data/processed/statistical_results.json`.

#### 5. Human Validation Mode

Prepare data for human rating:

```bash
python code/main.py --task validate_human --config code/config.py
```

This will:
- Load generated reports.
- Apply the validation rubric from `code/validation/rubric.md`.
- Save anonymized ratings to `data/qualitative/`.

#### 6. Sensitivity Analysis (Kappa)

Analyze robustness of conclusions:

```bash
python code/main.py --task sensitivity-kappa --config code/config.py
```

#### 7. Archiving

Package all artifacts for reproducibility:

```bash
python code/main.py --task archive --config code/config.py
```

This will:
- Collect prompts, seeds, scripts, and anonymized ratings.
- Create a reproducible archive in `data/archive/`.

#### 8. Full Pipeline

Run the entire pipeline end-to-end:

```bash
python code/main.py --task full_pipeline --config code/config.py
```

This executes: Generation → Control → Analysis → Stats → Validation → Archive.

## Output Artifacts

After a successful run, the following artifacts will be generated:

- `data/raw/*.json`: Generated phenomenological reports and control samples.
- `data/processed/validity_scores.csv`: Aggregated validity metrics (Consistency, Stability, Markers).
- `data/processed/statistical_results.json`: Statistical test outputs (ANOVA, Kruskal-Wallis, etc.).
- `data/qualitative/*.csv`: Anonymized human rating sheets.
- `data/archive/*.tar.gz`: Reproducibility archive containing all artifacts.

## Troubleshooting

### CUDA Errors

If you encounter CUDA errors, ensure you are using the CPU-only version of `llama-cpp-python` and that no GPU drivers are interfering. The primary CI pipeline is designed to run on CPU only.

### Missing Dependencies

If you encounter import errors, verify that all dependencies in `requirements.txt` are installed:

```bash
pip install -r requirements.txt --upgrade
```

### Timeout Errors

If generation tasks timeout, you can increase the timeout limit in `code/config.py` (look for `TIMEOUT_SECONDS`).

## Next Steps

- Review the `specs/` directory for detailed feature requirements.
- Read `research.md` for the theoretical background.
- Examine `data-model.md` for schema definitions.
