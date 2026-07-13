# Phenomenological AI: First-Person Experience Modeling - Quick Start

This guide provides instructions for setting up the environment and running the research pipeline.

## Environment Setup

### Prerequisites
- Python 3.11+
- pip package manager
- At least 8GB RAM (recommended 16GB for local 7B models)

### Installation

1. Clone the repository and navigate to the project root:
 ```bash
 git clone <repository-url>
 cd PROJ-592-phenomenological-ai-first-person-experie
 ```

2. Create and activate a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

4. Download the required model (TinyLlama-1.1B-Chat-v1.0-GGUF):
 ```bash
 # Ensure the model file exists at code/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
 # If missing, download from HuggingFace:
 # huggingface-cli download TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf --local-dir code/models
 ```

5. Initialize project directories (if not already done):
 ```bash
 python scripts/init_project.py
 ```

## CLI Usage

The main entry point is `code/main.py`. Use the `--task` argument to select the phase or specific operation.

### Generation Phase (US1)

Generate the corpus of phenomenological reports using the configured model and prompting strategies.

```bash
# Run full generation (phenomenological reports + control corpus)
python code/main.py --task generate --config code/config.py

# Generate control corpus only
python code/main.py --task generate_control --config code/config.py
```

**Output**: `data/raw/phenomenological_reports.json`, `data/raw/control_corpus.json`

### Analysis Phase (US2)

Compute metrics (Consistency, Stability, Markers) and perform statistical analysis.

```bash
# Run full analysis pipeline (metrics + stats)
python code/main.py --task analyze --config code/config.py

# Run statistical orchestration only (produces validity_scores.csv)
python code/main.py --task stats --config code/config.py
```

**Output**: `data/processed/validity_scores.csv`, `data/processed/metrics_*.json`

### Validation Phase (US3)

Select samples for human rating and run the rating pipeline.

```bash
# Run stratified sampling to select validation set
python code/main.py --task select_validation_sample --config code/config.py

# Run human rating pipeline (requires pre-configured rubric)
python code/main.py --task validate_human --config code/config.py
```

**Output**: `data/qualitative/ratings.csv`, `data/qualitative/agreement_metrics.json`

### Sensitivity Analysis

Run specific sensitivity tests for robustness validation.

```bash
# Run Kappa sensitivity analysis
python code/main.py --task sensitivity-kappa --config code/config.py
```

### Full Pipeline

Execute the entire research workflow: Generation → Analysis → Validation.

```bash
python code/main.py --task full --config code/config.py
```

## Data Outputs

After a successful run, the following artifacts will be available:

- `data/raw/phenomenological_reports.json`: Generated phenomenological reports
- `data/raw/control_corpus.json`: Control samples from external dataset
- `data/processed/validity_scores.csv`: Aggregated validity scores (Consistency, Stability, Markers)
- `data/qualitative/ratings.csv`: Human rater scores
- `figures/`: Generated plots and visualizations

## Troubleshooting

- **Import Errors**: Ensure you are running from the project root and `.venv` is activated.
- **Model Not Found**: Verify the GGUF file exists in `code/models/`.
- **CUDA Errors**: This pipeline is designed for CPU-only execution. Ensure no GPU drivers are interfering.

## Reproducibility

To archive all artifacts for reproducibility, run:
```bash
python code/utils/archiver.py
```
This will create a tarball in `data/archives/` containing prompts, seeds, scripts, and anonymized ratings.