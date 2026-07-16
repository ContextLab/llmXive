# Quickstart: llmXive follow-up: extending "ArcANE"

## Prerequisites

- Python 3.11+
- Sufficient RAM (for CPU quantized models)
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-919-llmxive-follow-up-extending-arcane-do-ro
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
   *Note: `requirements.txt` includes `transformers`, `llama-cpp-python`, `scipy`, `pandas`, `hypothesis`.*

## Configuration

1. **Define Character Axes**:
   Edit `data/raw/axes.jsonl` to include your characters (e.g., "elizabeth_bennet", "sherlock_holmes").
   ```json
   {"character_id": "elizabeth_bennet", "coarse_axis": "Pride to Humility", "fine_axis": "Initial Arrogance to Self-Reflection"}
   ```

2. **Set Random Seeds**:
   Edit `config.yaml` to pin seeds for reproducibility.
   ```yaml
   seed: 42
   ```

## Running the Experiment

### Step 1: Axis Validation
Run the axis validation step to ensure inter-rater reliability.
```bash
python -m src.cli.run_experiment --mode validate_axes
```
*Expected Output: Kappa coefficient > 0.6. If not, the process aborts.*

### Step 2: Calibration
Run the Judge calibration to ensure reliability.
```bash
python -m src.cli.run_experiment --mode calibration
```
*Expected Output: Kappa coefficient > 0.6. If not, the process aborts.*

### Step 3: Probe Generation
Generate "Out-of-World" probes.
```bash
python -m src.cli.run_experiment --mode generate_probes
```
*Expected Output: `data/derived/probes.jsonl` with a sufficient number of valid probes per character to support robust analysis.*

### Step 4: Execution
Run the main experiment (Target Model + Judge).
```bash
python -m src.cli.run_experiment --mode run_experiment
```
*Note: This may take up to 6 hours on CPU. Logs are written to `logs/experiment.log`. Timeouts are marked as missing.*

### Step 5: Analysis
Generate statistical results.
```bash
python -m src.cli.run_experiment --mode analyze
```
*Expected Output: `data/derived/stats_summary.json` with ANOVA/Friedman results.*

## Verification

1. **Check Data Integrity**:
   ```bash
   python -m src.lib.utils verify_checksums
   ```

2. **Reproduce Results**:
   ```bash
   python -m src.cli.run_experiment --mode full_repro
   ```
   *This re-runs the entire pipeline from raw data to results.*