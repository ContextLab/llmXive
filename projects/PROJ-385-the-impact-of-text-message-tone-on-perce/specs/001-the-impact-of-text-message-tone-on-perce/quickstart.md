# Quickstart: The Impact of Text Message Tone on Perceived Emotional Support

## Prerequisites

- Python 3.11+
- `pip`
- `git`
- (Optional) Prolific API Key for real data collection.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-385-the-impact-of-text-message-tone-on-perce
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline is executed sequentially. Run the following commands from the project root:

### Step 0: Power Analysis
Calculates the required sample size (N) based on literature effect sizes.
```bash
python code/01_power_analysis.py --output data/processed/power_analysis_results.json --seed 42
```
*Output*: `data/processed/power_analysis_results.json` (contains `target_N`).

### Step 1: Generate Stimuli
Generates the factorial set of text messages.
```bash
python code/01_generate_stimuli.py --output data/raw/stimuli.csv --seed 42
```

### Step 2: Simulate Ratings (CI Validation Only)
Generates synthetic human ratings for the stimuli to validate the pipeline. **These results are not empirical findings.**
```bash
python code/02_simulate_ratings.py --input data/raw/stimuli.csv --power-json data/processed/power_analysis_results.json --output data/raw/simulated_ratings.csv --seed 42
```

### Step 3: Run Primary Analysis (Validation Mode)
Executes the Linear Mixed-Effects Model on simulated data to verify code correctness.
```bash
python code/03_lmm_analysis.py --stimuli data/raw/stimuli.csv --ratings data/raw/simulated_ratings.csv --output data/processed/lmm_validation.json --mode validation
```

### Step 4: Collect Real Data (Optional/Manual)
Interfaces with Prolific API to gather real human ratings. Requires `PROLIFIC_API_KEY` environment variable.
```bash
export PROLIFIC_API_KEY="your_key_here"
python code/04_collect_real_data.py --input data/raw/stimuli.csv --power-json data/processed/power_analysis_results.json --output data/raw/real_ratings.csv --mode real
```

### Step 5: Run Primary Analysis (Research Mode)
Executes the LMM on **real** data.
```bash
python code/03_lmm_analysis.py --stimuli data/raw/stimuli.csv --ratings data/raw/real_ratings.csv --output data/processed/lmm_results.json --mode research
```

### Step 6: Run Sensitivity Analysis
Tests the robustness of the interaction effect to different cue definitions.
```bash
python code/04_sensitivity_analysis.py --results data/processed/lmm_results.json --output data/processed/sensitivity_report.json
```

### Step 7: Generate Report
Compiles results into a summary JSON/Markdown.
```bash
python code/05_report_generation.py --results data/processed/lmm_results.json --sensitivity data/processed/sensitivity_report.json --output report.md
```

## Validation

To ensure data integrity, run the contract tests:
```bash
pytest code/tests/ -v
```
*Note*: Tests read `data/raw/stimuli.csv` and `data/raw/simulated_ratings.csv` from disk. Ensure Step 1 and Step 2 are run first.

## Troubleshooting

- **Missing Dependencies**: Ensure `statsmodels` and `numpy` are installed.
- **Data Errors**: If `ratings.csv` is missing, re-run Step 2 (simulation) or Step 4 (real collection).
- **Memory Issues**: The simulation uses ~500MB RAM. If running on a constrained runner, reduce `--n_participants` in Step 2.
- **API Errors**: If Step 4 fails, check `PROLIFIC_API_KEY` and network connectivity.