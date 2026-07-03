# Quickstart: The Effect of Priming on Prosocial Behavior in Online Communities

## Prerequisites
- Python 3.11+
- `pip`

## Installation

1. **Clone the repository** and navigate to the project directory.  
2. **Install dependencies**:

   ```bash
   cd projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/code
   pip install -r requirements.txt
   ```

3. **Download NLTK data**:

   ```bash
   python -c "import nltk; nltk.download('punkt'); nltk.download('vader_lexicon')"
   ```

## Running the Pipeline

The pipeline runs in sequential stages. Each stage writes its output to `data/processed/` and logs progress.

### Step 1: Ingest & Anonymize
```bash
python 01_ingest.py
```
* Downloads the **primary verified multi‑subreddit dataset** `pushshift/reddit`.  
* Verifies presence of all five target subreddits; if any are missing, attempts to load the fallback dataset (same source refreshed). If that also lacks required subreddits, the script **aborts with an error**.  
* Computes `thread_age` before stripping timestamps.  
* Hashes usernames and strips timestamps.  
* Outputs `data/processed/raw_anonymized.parquet`.

### Step 2: Classify Threads
```bash
python 02_classify.py
```
* Applies keyword logic with negation exclusion.  
* Labels `thread_type` as “Prime” or “Control”.  
* Logs “Negation Exclusions”.  
* Outputs `data/processed/classified.parquet`.

### Step 3: Score Comments
```bash
python 03_score.py
```
* Computes VADER sentiment scores and `neg_score` (VADER `neg` component).  
* Computes `prosocial_action_count` using the secondary lexicon (excluding prime keywords).  
* Ensures CPU‑only execution; runtime is monitored to stay < 4 h for TARGET_N = 10 000.  
* Outputs `data/processed/scored.parquet`.

### Step 4: Validation (Human‑Generated Gold Standard Required)
**Before running this step, you must create the validation file** `data/validation/gold_standard.csv` **by following the Human Annotation Protocol** described in `research.md`:

1. Recruit **at least three independent raters**.  
2. Provide them with the codebook (prosocal action verbs, VADER neg interpretation).  
3. Perform a **stratified random sample** (≥ 50 samples per `thread_type` × `subreddit` stratum; merge strata only when necessary to meet the threshold).  
4. Collect the annotations and save them in a CSV with columns `comment_id`, `human_label_prosocial`, `human_label_neg`, plus a `human_raters` column listing the rater IDs.

Then run:

```bash
python 04_validate.py --gold data/validation/gold_standard.csv
```
* Calculates Cohen’s Kappa for the prosocial lexicon and VADER negativity.  
* **Fails** with a clear error if Kappa < 0.7 or if the gold‑standard file is missing or lacks the required `human_raters` metadata.

### Step 5: Statistical Analysis
```bash
python 05_analyze.py
```
* Fits the Linear Mixed‑Effects Model (random intercept for `thread_id`; `user_id` included only if its variance component is positive and identifiable).  
* Performs sensitivity analysis (p < 0.01, 0.05, 0.10).  
* Generates `results/analysis_results.json` and `results/boxplot.png`.

## Expected Outputs
- `data/processed/scored.parquet`: Final analysis dataset.  
- `results/analysis_results.json`: Statistical summary (p‑value, coefficients, validation Kappa, runtime).  
- `results/boxplot.png`: Visualization of prosocial counts by thread type.  
- `logs/pipeline.log`: Execution logs including warnings for missing subreddits, dataset fallback attempts, and any variance‑component diagnostics for `user_id`.

## Troubleshooting
- **Memory Error**: Reduce `TARGET_N` in `code/utils/constants.py`.  
- **Dataset Missing Subreddits**: Check `logs/pipeline.log` for “Subreddit Filter Warning”. The pipeline will abort if no verified multi‑subreddit source is found.  
- **LMM Convergence**: If the model fails to converge, the script will automatically refit without the `user_id` random effect and log the decision.  
- **Validation Failure**: Ensure `gold_standard.csv` is present, was created by **human raters**, and includes the `human_raters` column; otherwise the validation step will stop with an explanatory message.  

