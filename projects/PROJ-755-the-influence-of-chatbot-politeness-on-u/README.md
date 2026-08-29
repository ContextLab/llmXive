# The Influence of Chatbot Politeness on User-Perceived Quality

## Project Overview
This research project investigates the relationship between chatbot politeness and user-perceived quality of conversations. We analyze dialogue datasets using cumulative link mixed-effects models (CLMM) to determine if polite chatbot responses correlate with higher quality ratings.

## Environment Configuration

### Local Development
This project requires environment variables for sensitive configuration, specifically the Hugging Face token for dataset access.

1. Copy the template file:
 ```bash
 cp.env.example.env
 ```
2. Edit `.env` and add your Hugging Face token:
 ```
 HF_TOKEN=your_actual_token_here
 ```

**Security Note**: The `.env` file is listed in `.gitignore` and must never be committed to the repository.

### CI/CD (GitHub Actions)
For automated pipelines, do not use `.env` files. Instead, configure `HF_TOKEN` as a **Repository Secret** in GitHub Actions:
1. Go to Repository Settings > Secrets and variables > Actions
2. Add a new secret named `HF_TOKEN`
3. The workflow file will automatically inject this as an environment variable.

## Installation

1. Install Python dependencies:
 ```bash
 pip install -r requirements.txt
 ```
2. Ensure R and required packages (`lme4`, `ordinal`) are installed for mixed-effects modeling.

## Usage
Run the pipeline steps in order:
1. Data Acquisition & Scoring: `python code/01_download_and_score.py`
2. CLMM Analysis: `python code/02_fit_clmm.py`
3. Robustness Analysis: `python code/03_robustness_analysis.py`

## License
MIT
