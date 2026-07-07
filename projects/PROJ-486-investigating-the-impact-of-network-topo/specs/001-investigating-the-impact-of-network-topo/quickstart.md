# Quickstart: Investigating the Impact of Network Topology on Neural Entrainment to Rhythmic Stimuli

## Prerequisites

- Python 3.10+
- `pip`
- (Optional) `huggingface-cli` if manual download is needed (though the script handles it).

## Installation

1. Clone the repository and navigate to the project directory.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Pipeline

### Option A: Full Run (with Data Download)
This attempts to download from verified URLs. **If data is missing or does not contain "rhythmic stimulus" metrics, the pipeline halts with a "Data Gap" error.**
```bash
python code/main.py --atlas Schaefer
```

### Option B: Unit Test Mode (Logic Validation Only)
Generates synthetic data to test the pipeline logic (correlation, correction, plotting) **without producing scientific results**. This is for CI validation only.
```bash
python code/main.py --atlas Schaefer --synthetic
```

### Option C: Sensitivity Analysis
Runs the primary analysis and the alternative parcellation (AAL) automatically.
```bash
python code/main.py --atlas Schaefer --sensitivity
```

## Output

- **Console**: Progress logs, validation warnings, power warnings, or "Data Gap" errors.
- **Files**:
  - `data/processed/topology_metrics.csv`: Calculated metrics.
  - `results/correlation_stats.json`: Statistical results (r, p, adj_p, vif).
  - `results/plots/scatter_plot.png`: Primary correlation visualization.
  - `results/plots/sensitivity_bar.png`: Comparison of effect sizes.

## Troubleshooting

- **Error: "Invalid Entrainment Data"**: Check the input CSV path or format. Ensure columns `subject_id` and `entrainment_metric` exist.
- **Error: "Data Gap"**: The verified datasets do not contain the specific variables needed (specifically "rhythmic stimulus" entrainment metrics). The pipeline has halted. **No scientific results are generated.**
- **Error: "Stimulus Mismatch"**: The entrainment dataset contains only "resting-state" data, which is insufficient for the "rhythmic stimuli" hypothesis.
- **Memory Error**: Unlikely on this scale, but ensure no other heavy processes are running.