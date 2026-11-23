# Quickstart Guide: The Impact of Social Comparison on Self-Perception

This guide outlines the steps to run the full research pipeline, from data generation to analysis.

## Prerequisites

- Python 3.8+
- Install dependencies: `pip install -r requirements.txt`

## Step 1: Initialize Project Structure

Run the initialization script to create necessary directories:
```bash
bash scripts/init_structure.sh
```

## Step 2: Pre-Test Validation (Phase 0 & 7)

Before collecting any data (even synthetic), run the pre-test to ensure stimuli are visually indistinguishable.

1. Generate pre-test results:
 ```bash
 python code/simulate_pretest.py --seed 42 --n 30 --input data/stimuli/ --output data/pretest/results.json
 ```

2. Run the gate launch validation:
 ```bash
 python scripts/gate_launch.py
 ```
 *This will fail if `data/pretest/results.json` is missing or if the p-value < 0.05.*

## Step 3: Data Collection (Simulation)

Since this is a research implementation, we use synthetic data generation to test the pipeline integrity.
**WARNING: The following data is synthetic and for testing ONLY.**

Run the participant simulator:
```bash
python code/simulate_participant.py --n 150 --output data/raw/mock_responses/
```
*Note: Use the `--n` flag. The `--n-participants` flag is not supported.*

## Step 4: Data Processing & Cleaning

The data collection interface writes raw JSONL files. We need to filter for complete sessions.
(Note: In a full implementation, T014 logic would be executed here to filter partials.
For this simulation, all generated sessions are marked complete).

## Step 5: Analysis (User Story 3)

Run the statistical analysis pipeline:
```bash
python code/analysis.py
```

This will:
1. Load processed data.
2. Validate completeness and participant count (N >= 150).
3. Fit the LME model.
4. Apply Bonferroni correction.
5. Save results to `data/analysis_results.json`.

## Expected Outputs

- `data/pretest/results.json`: Pre-test p-value.
- `data/raw/mock_responses/mock_sessions.jsonl`: Raw simulated session data.
- `data/analysis_results.json`: Final statistical results.

## Troubleshooting

- **Gate Launch Failed**: Ensure `data/pretest/results.json` exists and contains `p_value > 0.05`.
- **Analysis Failed**: Ensure you have generated at least 150 participants in `data/raw/mock_responses/`.
- **Argparse Errors**: Ensure you are using `--n` instead of `--n-participants` for the simulator.