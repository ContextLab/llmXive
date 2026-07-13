# Quickstart: llmXive follow-up: extending "ResearchClawBench: A Benchmark for End-to-End Autonomous Scientific Re"

## Prerequisites

- Python 3.11+
- Access to the ResearchClawBench dataset (placed in `data/raw/` with known checksum).
- The `rubric_schema.json` file in `assets/`.
- Curated templates in `assets/templates/`.

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**requirements.txt** (example):
```text
pandas>=2.0.0
scipy>=1.11.0
pytest>=7.0.0
pyyaml>=6.0
jsonschema>=4.0.0
tqdm>=4.65.0
numpy>=1.24.0
```

## Data Setup

1. Ensure the ResearchClawBench dataset is available.
   - Place it in `data/raw/researchclaw.json`.
   - **Verify Checksum**: Run `python -m src.data.validate_dataset` to ensure the local file matches the expected checksum. If not, abort.
2. Verify the dataset contains the `failure_mode` field.

## Running the Experiment

### 1. Validate Rubric & Pilot IRR (FR-008 Expanded)
Before running agents, verify the rubric logic and estimate IRR:
```bash
python -m src.scoring.validate_rubric --pilot
```
- Expected output: Set A (Low Score), Set B (High Score), and `results/pilot_irr.json`.
- If `margin_validity` is false (IRR > 5), the main experiment will be marked "inconclusive" by default.

### 2. CPU Compatibility Check
Verify agents are CPU-compatible:
```bash
python -m src.agents.cpu_compat --check
```
- Excludes or substitutes agents that require GPU or >7GB RAM.

### 3. Execute Agents
Run the full experiment (3 generations per task/condition):
```bash
python -m src.cli.run_experiment --tasks 10 --agents 7 --timeout 6h --generations 3
```
- This launches up to 420 runs with a 6-hour timeout per run.
- Logs are saved to `results/execution_logs.csv`.

### 4. Score Results
Apply the rubric to all completed runs:
```bash
python -m src.scoring.score_runs
```
- Output: `results/scores.csv` (averaged over generations).

### 5. Statistical Analysis
Run the decoupling analysis:
```bash
python -m src.analysis.run_stats
```
- Output: `results/stats_report.json`.
- Includes TOST results for Scientific Core and Wilcoxon tests for Protocol Alignment.

## Interpreting Results

- **Protocol Alignment**: Look for a significant p-value (<0.05) and positive effect size.
- **Scientific Core**: Look for "safe" status in the TOST test (p-values < 0.05 for both bounds AND pilot IRR ≤ 5).
- **Power Warning**: If N < 30 due to timeouts/conflicts, the report will flag low power.
- **Margin Validity**: If pilot IRR > 5, the "Scientific Core" result is "inconclusive" regardless of TOST p-values.

## Troubleshooting

- **Error: "Dataset checksum mismatch"**: The local dataset does not match the expected hash. Re-fetch or verify the source.
- **Error: "Agent not CPU-compatible"**: The agent requires GPU. Check `results/cpu_compat_report.json` for substitution details.
- **Timeout**: If runs exceed 6 hours, they are excluded. Check agent logs for bottlenecks.
- **Scaffold Conflict**: If detected, the run is excluded. Check `results/scaffold_conflicts.log`.


## projects/PROJ-957-llmxive-follow-up-extending-researchclaw/specs/001-llmxive-follow-up-extending-researchclaw/contracts/rubric_schema.json