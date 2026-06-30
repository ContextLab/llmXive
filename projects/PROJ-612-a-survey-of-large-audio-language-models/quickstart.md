# Quickstart Guide

## Prerequisites

- Python 3.11+
- pip
- Git

## Setup

1. **Clone the repository**:
 ```bash
 git clone
 cd survey-audio-llm-hallucination
 ```

2. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

3. **Download NLTK data** (required for WordNet synonyms):
 ```bash
 python -c "import nltk; nltk.download('wordnet')"
 ```

## Running the Pipeline

### Step 1: Initialize Data

Verify dataset checksums:
```bash
python code/checksum_data.py --verify
```

### Step 2: Run Inference & Hallucination Detection (US1)

```bash
python code/run_inference.py --config config.yaml
```
**Outputs**:
- `results/captions.json` (JSONL)
- `results/hallucination_rates.csv`

### Step 3: Analyze Training Data Correlation (US2)

```bash
python code/estimate_training_data.py
python code/analyze_correlation.py --stage correlation
```
**Outputs**:
- `data/training_data_estimates.yaml`
- `results/correlation_report.json`

### Step 4: Human Validation (US3)

1. **Generate crowd job template**:
 ```bash
 python code/submit_crowd_job.py --generate-template
 ```
2. **Submit job** (requires `PROLIFIC_API_KEY`):
 ```bash
 python code/submit_crowd_job.py --submit
 ```
3. **Retrieve judgments**:
 ```bash
 python code/retrieve_crowd_judgments.py
 ```
4. **Analyze agreement**:
 ```bash
 python code/analyze_correlation.py --stage kappa
 ```
**Outputs**:
- `data/human_judgments.csv`
- `results/kappa_report.json`

## Configuration

Edit `config.yaml` to adjust:
- Model lists
- Dataset paths
- Sample limits per domain
- Exclusion keywords

## Troubleshooting

- **OOM Errors**: Reduce `sample_limits` in `config.yaml`.
- **Missing Data**: Check `data/raw/` for required JSON files.
- **API Failures**: Ensure `PROLIFIC_API_KEY` is set in environment.

## Next Steps

- Review `docs/ARCHITECTURE.md` for design details.
- Run `tests/` to validate pipeline integrity.
