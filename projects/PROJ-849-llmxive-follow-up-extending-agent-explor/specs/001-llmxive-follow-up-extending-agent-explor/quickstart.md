# Quickstart: Semantic Divergence Diagnostic

## Prerequisites

- Python 3.11+
- Git
- 7 GB+ RAM available
- Internet access (for dataset download)

## Installation

1. **Clone and Navigate**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-849-llmxive-follow-up-extending-agent-explor/code/
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Data Preparation

1. **Download MathVista**:
   The system will automatically download the dataset on first run. Ensure you have sufficient disk space for the cache.
   ```bash
   # Optional: Pre-download to verify access
   python -c "from datasets import load_dataset; load_dataset('AI4Math/MathVista', split='test', streaming=True)"
   ```

2. **Verify Tool Mapping**:
   Ensure `data/tool_mappings/mathvista_tool_map.json` exists in the project root.
   ```bash
   ls -la data/tool_mappings/mathvista_tool_map.json
   ```

## Running the Diagnostic

Execute the main pipeline:

```bash
python src/cli/run_diagnostic.py --output data/results/divergence_analysis.json
```

**Options**:
- `--limit`: Max records to process (default: a configurable upper limit).
- `--seed`: Random seed for reproducibility (default: a fixed integer).
- `--skip-simulation`: Skip AXPO simulation and use cached results if available.

## Expected Output

The script generates `data/results/divergence_analysis.json` containing:
- `metadata`: Run configuration, timestamps, sample size.
- `results`: List of processed problem instances.
- `statistics`: Pearson correlation, p-value, and Logistic Regression metrics.

## Troubleshooting

- **Memory Error**: Ensure no other heavy processes are running. The system attempts to downsample automatically if memory exceeds a predefined threshold.
- **Timeout**: The job will abort after a predefined time limit. If this occurs, reduce the `--limit` parameter.
- **Missing Tool Mapping**: The script will exit with "Tool Mapping Missing" if the JSON file is not found.
