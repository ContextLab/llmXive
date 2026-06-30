# Quickstart: Survey of Large Audio Language Models – Hallucination Analysis

## 1. Prerequisites
- Python 3.11+
- Git
- GitHub Actions Runner (or local equivalent with GB+ RAM)

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-612-a-survey-of-large-audio-language-models

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## 3. Data Preparation
The pipeline automatically downloads datasets from verified HuggingFace sources and computes checksums.
- **LibriSpeech**: Downloaded via `datasets` library.
- **FMA Small**: Downloaded via `datasets` library.
- **ESC-50**: Downloaded via `datasets` library.

```bash
# Initialize data directory and compute checksums
mkdir -p data/raw data/processed results
python code/checksum_data.py --download  # Downloads data and records checksums to state/...yaml
```

## 4. Running the Pipeline

### Step 1: Run Inference & Detection
```bash
python code/run_inference.py --models "model1,model2" --domains "speech,music,environmental"
```
*This generates `results/hallucination_rates.csv`.*

### Step 2: Analyze Correlation
```bash
python code/analyze_correlation.py --input results/hallucination_rates.csv --training-data data/processed/training_data_estimates.yaml
```
*This generates `results/correlation_report.json`.*

### Step 3: Human Validation (Manual + Automated Retrieval)
1. Extract 150 samples from `results/captions_subset.csv` (stratified by domain).
2. Upload to crowdsourcing platform (compliant with ≥minimum wage standards).
3. **Retrieve Judgments**: Run the automated retrieval script:
   ```bash
   python code/retrieve_crowd_judgments.py --platform "mturk" --output data/processed/human_judgments.csv
   ```
4. Compute Cohen’s κ:
   ```bash
   python code/compute_cohen_kappa.py --input data/processed/human_judgments.csv
   ```

## 5. Verification
- Check `results/pipeline.log` for errors.
- Verify `results/hallucination_rates.csv` contains rows for available domains.
- Ensure `results/correlation_report.json` states "associational" framing and contains `rank_order_description` (no p-values).
- Verify `state/...yaml` contains checksums for raw data.

## 6. Troubleshooting
- **OOM Error**: Reduce batch size in `config.yaml`.
- **Missing Data**: Check `research.md` for dataset availability notes. If metadata is missing, samples are excluded and logged.
- **Model Load Failure**: Verify model size ≤2B params.
- **Time Limit**: If pipeline exceeds a predetermined time threshold, sample size is automatically reduced. Check `pipeline.log` for reduction notice.