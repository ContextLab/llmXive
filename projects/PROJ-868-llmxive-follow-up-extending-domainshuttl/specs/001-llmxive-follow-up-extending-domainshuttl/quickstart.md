# Quickstart: llmXive follow-up: extending "DomainShuttle"

## Prerequisites

- Python 3.10+
- Git
- Access to a machine with at least 7GB RAM (or GitHub Actions runner).
- DomainShuttle weights available locally (assumed to be in `./models/domainshuttle/`).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-868-llmxive-follow-up-extending-domainshuttl
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins PyTorch to a CPU-only wheel version.*

## Running the Pipeline

The pipeline is executed via `src/cli.py`. Each phase can be run independently.

### Phase 1: Data Acquisition & Embedding
Downloads the WebVid subset, extracts 5 frames per video, computes complexity, and generates embeddings.
```bash
python src/cli.py --phase data_prep
```
*Output*: `data/processed/embeddings/`, `data/processed/complexity_scores.csv`

### Phase 2: Compression Training
Trains Autoencoders for dimensions, 24, 32, 40, 48, 64, 80, 96, 112, 128, 160, 192, 256.
```bash
python src/cli.py --phase compress
```
*Output*: `data/processed/compressed/`, `data/processed/models/`

### Phase 3: Generation & Fidelity
Generates 5 frames per video and computes CLIP similarity scores.
```bash
python src/cli.py --phase evaluate
```
*Output*: `data/results/fidelity_scores.csv`

### Phase 4: Analysis
Runs segmented regression and generates plots.
```bash
python src/cli.py --phase analyze
```
*Output*: `data/results/phase_transition_plot.png`

### Full Pipeline (End-to-End)
```bash
python src/cli.py --phase all
```

## Testing

Run the contract tests to ensure data validity:
```bash
pytest tests/contract/
```

Run unit tests for complexity scoring and autoencoder logic:
```bash
pytest tests/unit/
```

## Troubleshooting

- **OOM Error**: Reduce `BATCH_SIZE` in `src/config/settings.py`.
- **Timeout**: If generation hangs, increase `TIMEOUT_SECONDS` or reduce the number of subjects in `config/settings.py`.
- **Missing DomainShuttle**: Ensure the `DOMAINSHUTTLE_ROOT` environment variable points to the model weights. If missing, the pipeline will halt with a clear error.