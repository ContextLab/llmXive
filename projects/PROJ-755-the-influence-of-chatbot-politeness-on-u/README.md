# The Influence of Chatbot Politeness on User-Perceived Quality

## Project Overview

This project investigates the relationship between chatbot politeness and user-perceived quality using mixed-effects modeling and robustness analysis.

## Environment Configuration

This project uses environment variables for sensitive configuration, specifically the Hugging Face API token required for dataset downloads.

### Local Development

1. Copy the template file:
 ```bash
 cp.env.example.env
 ```
2. Edit `.env` and add your Hugging Face token:
 ```
 HF_TOKEN=your_actual_token_here
 ```
3. The project code (via `code/utils/env_config.py`) will automatically load this file when running scripts locally.

### CI/CD (GitHub Actions)

**Do not** use the `.env` file in CI. Instead:
1. Go to your repository Settings > Secrets and variables > Actions.
2. Add a new secret named `HF_TOKEN`.
3. The CI workflow (`.github/workflows/ci.yml`) will inject this secret into the environment during execution.

This approach ensures reproducibility on fresh runners and prevents accidental leakage of credentials.

## Usage

See `docs/quickstart.md` for a step-by-step guide to running the full pipeline.

## Requirements

- Python 3.9+
- R 4.0+
- Dependencies listed in `requirements.txt`

## License

[Project License]