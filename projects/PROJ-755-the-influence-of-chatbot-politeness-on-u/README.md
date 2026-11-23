# The Influence of Chatbot Politeness on User-Perceived Quality

## Project Overview

This project investigates the correlation between chatbot politeness (measured via BERT-based models and lexicon dictionaries) and user-perceived quality ratings. It implements a reproducible scientific pipeline involving data acquisition from Hugging Face, politeness scoring, statistical modeling (CLMM), and robustness analysis.

## Prerequisites

- Python 3.9+
- R (with `lme4` and `ordinal` packages)
- Hugging Face account (for dataset/model access)

## Environment Configuration

### Local Development

1. Copy the environment template:
 ```bash
 cp.env.example.env
 ```
2. Edit `.env` and add your Hugging Face token:
 ```
 HF_TOKEN=your_actual_token_here
 ```
3. Install Python dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

### CI/CD (GitHub Actions)

For automated runs, do **not** use a `.env` file. Instead, configure the Hugging Face token as a GitHub Secret:
1. Go to Repository Settings > Secrets and variables > Actions.
2. Create a new secret named `HF_TOKEN`.
3. Reference it in the workflow file (e.g., `.github/workflows/ci.yml`) using `${{ secrets.HF_TOKEN }}`.

## Usage

See `docs/quickstart.md` for a step-by-step guide to running the full pipeline.

## Directory Structure

- `code/`: Python scripts and utilities
- `data/`: Raw and processed datasets
- `tests/`: Unit and integration tests
- `contracts/`: Schema definitions
- `specs/`: Research design documents
- `state/`: Project state tracking (checksums, logs)

## License

MIT