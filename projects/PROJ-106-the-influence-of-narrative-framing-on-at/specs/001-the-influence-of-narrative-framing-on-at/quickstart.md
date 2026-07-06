# Quickstart: The Influence of Narrative Framing on Attitudes Towards AI Assistance

## Prerequisites
-   Python 3.11+
-   `pip` or `venv`
-   (Optional) Survey platform access (Qualtrics/Google Forms) for real data.
-   (Required) IRB/Ethics Approval documentation for the 'Ethics Gate'.

## Setup

1.  **Clone and Navigate**:
    ```bash
    cd projects/PROJ-106-the-influence-of-narrative-framing-on-at
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Dependencies include: `pandas`, `numpy`, `scipy`, `statsmodels`, `textstat`, `vaderSentiment`, `sentence-transformers`, `pytest`.*

4.  **Verify Environment**:
    ```bash
    pytest tests/ -v
    ```
    *All tests should pass, verifying stimulus generation, randomization, and pilot logic.*

## Workflow

### Phase 0: Ethics Gate
**Mandatory**: Ensure IRB approval is documented in `data/ethics/irb_approval.pdf`.
```bash
python code/00_ethics_gate.py
```
*Output*: Updates `state/projects/PROJ-106...yaml` with ethics status. Blocks further steps if missing.

### Phase 0.5: Pilot Study (FR-011)
Run the pilot to validate the manipulation check.
```bash
python code/03_pilot_study.py --n 30
```
*Output*: `data/processed/pilot_validation_report.json`.
*Gate*: If manipulation check discrimination is low, the script halts and prompts for instrument revision.

### Phase 1: Generate Stimuli
Run the stimulus generation script to create the Partner and Tool vignettes.
```bash
python code/01_stimulus_generation.py
```
*Output*: `data/stimuli/vignettes.csv`. Validates readability (SC-001), sentiment (SC-005), and semantic similarity.

### Phase 2: Randomization (Simulation)
Simulate participant assignment (or prepare for real deployment).
```bash
python code/02_randomization.py --n 350 --seed 42
```
*Output*: `data/raw/assignment_log.csv`. Verifies 50/50 split (FR-002).

### Phase 3: Data Collection (Simulation or Import)
**Option A: Simulate Data (Testing)**
```bash
python code/04_data_collection.py --mode simulate --n 350
```
*Output*: `data/raw/survey_export_simulated.csv`.

**Option B: Import Real Data**
Place your raw CSV from Qualtrics/Google Forms in `data/raw/` and run:
```bash
python code/04_data_collection.py --mode import --file data/raw/your_export.csv
```

### Phase 4: Analysis
Run the full statistical pipeline.
```bash
python code/05_analysis.py
```
*Output*:
-   `data/processed/results_summary.json` (P-values, Cohen's d, FDR-adjusted p-values).
-   `data/processed/power_report.txt` (MDES calculation, power status).
-   Console output with key findings (ITT primary analysis).

### Phase 5: Validation
Ensure the pipeline meets all Success Criteria.
```bash
pytest tests/ -v --tb=short
```
*Checks*:
-   SC-001: Readability diff ≤ 2.0.
-   SC-002: MDES report generated; if N < 300, flag is correct.
-   SC-003: FDR correction applied.
-   SC-005: Sentiment diff ≤ 0.05.
-   FR-007: Sensitivity analysis test passes.

## Troubleshooting
-   **ImportError**: Ensure `venv` is active and `requirements.txt` was installed.
-   **Ethics Gate Failed**: Place your IRB approval document in `data/ethics/irb_approval.pdf` and re-run.
-   **Stimulus Validation Failed**: The script will halt if readability, sentiment, or semantic constraints are not met. Edit the template in `code/01_stimulus_generation.py` and re-run.
-   **Pilot Failed**: If the manipulation check does not discriminate, revise the question in `code/03_pilot_study.py` and re-run the pilot.
-   **Low Power**: If N < 300, the script will report the MDES. Consider recruiting more participants or interpreting results as exploratory.
