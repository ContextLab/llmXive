# Quickstart: The Impact of Perspective-Taking on Moral Outrage in Online Discourse

## Prerequisites
- Python 3.11+
- Access to the "Against the Others!" dataset (placed in `data/raw/` via verified URL)
- GitHub account (for CI execution)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-183-the-impact-of-perspective-taking-on-mora
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

### Option 1: Local Execution (Development)
Ensure `data/raw/twitter_posts.parquet` and `data/raw/participant_responses.csv` are present.

```bash
# Run the full pipeline
python code/main.py
```

This will:
1. Curate stimuli (`01_stimulus_curation.py`).
2. Clean participant data (`02_data_cleaning.py`).
3. Calculate ICC and run the appropriate analysis (t-test or LME) (`03_analysis.py`).
4. Output results to `data/processed/`.

### Option 2: GitHub Actions (CI)
Push to the `001-perspective-taking-outrage` branch. The workflow `.github/workflows/run_analysis.yml` will:
1. Set up Python 3.11.
2. Install dependencies.
3. Run the pipeline.
4. Upload `data/processed/` as artifacts.

## Verifying Results

1. **Check Stimuli**:
   ```bash
   cat data/processed/stimuli.json | jq 'length'  # Should reflect the total number of stimuli (posts multiplied by the number of instructions per post)
   ```

2. **Check Cleaned Data**:
   ```bash
   cat data/processed/cleaned_participants.csv | wc -l  # Should be > 0
   ```

3. **Check Analysis**:
   ```bash
   cat data/processed/analysis_results.json | jq '.[] | select(.test_type == "t_test" or .test_type == "mixed_effects")'
   ```

## Troubleshooting

- **Error: DATASET_INSUFFICIENT**: The "Against the Others!" dataset has fewer than 60 posts on target topics. Check `data/raw/twitter_posts.parquet`.
- **Error: Attention Check Failures**: If too many participants are excluded, check the raw data for straight-lining or poor attention check design.
- **Error: Missing Consent**: If all participants are excluded, check for the `consent_given` flag in raw data.
- **Memory Error**: Ensure no GPU libraries are installed. The pipeline is CPU-only.