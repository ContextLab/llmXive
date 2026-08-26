# The Influence of Chatbot Politeness on User-Perceived Quality

## Project Overview
This project investigates the relationship between chatbot politeness and user-perceived quality using dialogue datasets and statistical modeling (CLMM).

## Prerequisites
- Python 3.11+
- R-base with `lme4` and `ordinal` packages
- Hugging Face account (for dataset access)

## Environment Configuration
This project uses environment variables for sensitive configuration.
1. Copy the template: `cp code/.env.example code/.env`
2. Edit `code/.env` and insert your Hugging Face token:
 ```
 HF_TOKEN=your_huggingface_token_here
 ```
3. The token is required to download authenticated datasets like **HCI_P2**.
 Without it, the data acquisition step (T015) will fail.

## Installation
1. Create a virtual environment: `python -m venv venv && source venv/bin/activate`
2. Install dependencies: `pip install -r requirements.txt`
3. Ensure R packages are installed:
 ```bash
 Rscript -e 'install.packages(c("lme4", "ordinal", "EValue"))'
 ```

## Usage
Run the pipeline in order:
1. **Setup**: `python code/setup_project_structure.py`
2. **Demographics Verification**: `python code/00_verify_demographics.py`
3. **Download & Score**: `python code/01_download_and_score.py`
4. **CLMM Analysis**: `python code/02_fit_clmm.py`
5. **Robustness**: `python code/03_robustness_analysis.py`

## Directory Structure
- `data/raw/`: Original downloaded datasets
- `data/processed/`: Cleaned, scored, and aggregated data
- `code/`: Implementation scripts
- `contracts/`: Schema definitions
- `docs/`: Documentation

## Contributing
Please ensure all tests pass before committing. Use `ruff` and `black` for formatting.
