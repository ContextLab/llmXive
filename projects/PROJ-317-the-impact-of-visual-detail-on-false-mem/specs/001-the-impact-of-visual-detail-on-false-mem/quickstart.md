# Quickstart: Visual Detail and False Memory Susceptibility

## Prerequisites

* Python 3.11+
* Git
* (Optional) HuggingFace CLI (if using private datasets, though COCO is public)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-317-the-impact-of-visual-detail-on-false-mem
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

### Step 0: Power Analysis (Blocking Gate)
Run the power analysis to determine sample size.
```bash
python code/analysis/stats.py --power-analysis
```
*Check `data/analysis/power_report.json`. If N < 50, the pipeline halts.*

### Step 1: Generate Stimuli (Phase 1)
This step downloads images (COCO 2017), filters for complexity, and creates manipulated versions.

```bash
python code/stimuli/downloader.py --output data/stimuli
python code/stimuli/filter.py --input data/stimuli/raw --output data/stimuli/filtered
python code/stimuli/manipulator.py --input data/stimuli/filtered --output data/stimuli/manipulated
python code/stimuli/metadata.py --input data/stimuli/manipulated --output data/stimuli/metadata
```
*Note: Check `data/logs/manipulation_errors.log` for any skipped images.*

### Step 2: Run Participant Interface (Phase 2)
Start the web interface for data collection.
*Note: For local testing, you can simulate a participant using `code/tests/simulate_participant.py`.*

```bash
streamlit run code/interface/app.py
```
*Access at `
*Note: The consent form will enforce a brief reading time before the session starts.*

### Step 3: Analyze Results (Phase 3)
Run the statistical analysis on collected data.

```bash
python code/analysis/stats.py --input data/responses --output data/analysis/results.json
python code/analysis/viz.py --input data/analysis/results.json --output data/analysis/plots.png
```

## Verification

1. **Check Stimuli**: Ensure `data/stimuli/` contains at least 30 pairs of images (enhanced/reduced).
2. **Check Logs**: Verify `data/logs/manipulation_errors.log` exists (may be empty).
3. **Check Analysis**: Ensure `data/analysis/results.json` contains `anova_p` and `effect_size`.
4. **Check Ethics**: Ensure `data/ethics/consent_template.md` contains the IRB approval number.

## Troubleshooting

* **"No images found"**: The downloader may have failed to fetch COCO. Check network or switch to the mock generator by setting `USE_MOCK=true` in environment variables.
* **"Session incomplete"**: Participants who drop out are logged in `data/logs/dropouts.log`. Ensure N ≥ 50 for valid power.
* **"Memory Error"**: If processing large images, reduce the batch size in `manipulator.py`.
* **"Consent Timer"**: If the consent timer is not working, check the browser console for JavaScript errors.