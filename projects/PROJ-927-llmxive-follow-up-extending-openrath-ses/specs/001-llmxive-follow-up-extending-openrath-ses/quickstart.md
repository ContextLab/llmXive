# Quickstart: 001-session-first-reconstruction

## Prerequisites

- Python 3.11+
- `pip` or `poetry`
- Git

## Installation

1. **Clone the repository** (or navigate to the project directory):
   ```bash
   cd projects/PROJ-927-llmxive-follow-up-extending-openrath-ses
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins exact versions (e.g., `scipy==1.11.0`) to ensure reproducibility.*

## Running the Experiment

### 1. Generate Ground Truth (User Story 1)
Generate the synthetic workflows with a fixed seed.
```bash
python code/main.py --phase generate --seed 42 --count 500
```
*Output*: `data/raw/workflows/` containing 500 JSON files.

### 2. Inject Corruption & Execute Architectures (User Story 2)
Run the simulation for both architectures with corruption injection.
```bash
python code/main.py --phase simulate --corruption-rates 0.05,0.10,0.20 --architectures event_log,session_first
```
*Output*: `data/processed/corrupted_logs/` and execution logs.

### 3. Reconstruct & Evaluate (User Story 3)
Reconstruct states and calculate metrics.
```bash
python code/main.py --phase reconstruct --architectures event_log,session_first
```
*Output*: `data/processed/reconstruction_results/` and `data/results/aggregated_metrics.json`.

### 4. Statistical Analysis
Run the sensitivity sweep and statistical tests.
```bash
python code/main.py --phase analyze --test cochrans_q
```
*Output*: Updated `aggregated_metrics.json` with p-values and significance flags.

## Verification

To verify reproducibility:
1. Delete `data/processed/` and `data/results/`.
2. Re-run the `simulate`, `reconstruct`, and `analyze` phases.
3. Compare the SHA256 hashes of the new output files with the registered hashes in `state/projects/PROJ-927-llmxive-follow-up-extending-openrath-ses.yaml`. They must match exactly.

## Common Commands

- **Check Status**: `python code/main.py --status` (Shows checkpoint progress).
- **Resume**: `python code/main.py --phase simulate --resume` (Resumes from last completed workflow ID).
- **Validate Schemas**: `pytest tests/contract/` (Ensures all data files match the defined schemas).