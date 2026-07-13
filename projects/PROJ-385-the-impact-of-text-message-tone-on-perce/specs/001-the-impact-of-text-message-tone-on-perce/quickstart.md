# Quickstart: The Impact of Text Message Tone on Perceived Emotional Support

## 1. Prerequisites

-   Python 3.11+
-   `git`
-   A terminal or command prompt.

## 2. Setup

1.  **Clone the repository** (or navigate to the project root):
    ```bash
    git clone <repo-url>
    cd projects/PROJ-385-the-impact-of-text-message-tone-on-perce
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: This installs `statsmodels`, `pandas`, `numpy`, `pytest`, and `pyyaml`.*

## 3. Running the Pipeline

The pipeline is executed in sequential steps.

### Step 1: Generate Stimuli
Generates the factorial design of text messages.
```bash
python code/01_generate_stimuli.py
```
*Output*: `data/raw/stimuli.csv`

### Step 2: Simulate Data Collection
Simulates participant ratings based on the generated stimuli.
*Note: This script supports a `--mode null` flag to test Type I error control.*
```bash
python code/02_simulate_ratings.py
```
*Output*: `data/raw/ratings.csv`

### Step 3: Clean Data
Removes straight-lining participants and checks randomization.
```bash
python code/03_clean_data.py
```
*Output*: `data/processed/clean_ratings.csv`

### Step 4: Primary Analysis
Runs the Linear Mixed-Effects Model with full factorial decomposition.
```bash
python code/04_run_lmm.py
```
*Output*: `data/processed/analysis_results.json` (contains primary interaction p-values).

### Step 5: Sensitivity Analysis
Tests robustness against different structural definitions of "Cue Intensity".
```bash
python code/05_sensitivity_analysis.py
```
*Output*: `data/processed/sensitivity_report.csv`.

## 4. Verification

Run the test suite to ensure contract compliance:
```bash
pytest tests/ -v
```
This validates:
-   Stimuli match the factorial design.
-   Ratings conform to the schema (1-7 scale).
-   **Contract tests** validate all data against the YAML schemas (`stimulus.schema.yaml`, `rating.schema.yaml`, `analysis_result.schema.yaml`).
-   Analysis logic handles null hypotheses correctly.

## 5. Troubleshooting

-   **Missing Data Files**: Ensure you run steps 1-3 in order. The analysis scripts require `data/processed/clean_ratings.csv`.
-   **Import Errors**: Verify you are in the `venv` and `requirements.txt` was installed.
-   **Memory Errors**: Unlikely given the small dataset size. If encountered, ensure no other heavy processes are running on the CI runner.