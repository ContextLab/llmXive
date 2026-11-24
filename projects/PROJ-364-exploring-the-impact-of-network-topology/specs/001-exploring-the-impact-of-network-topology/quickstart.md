# Quickstart: Exploring the Impact of Network Topology on Heat Dissipation in 2D Materials

## Prerequisites
- Python 3.11+  
- Git  
- Ability to run a GitHub Actions free‑tier runner (or a local machine with ≤ 7 GB RAM)

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd projects/PROJ-364-exploring-the-impact-of-network-topology

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r code/requirements.txt
```

## Data Setup

```bash
# Create data directory
mkdir -p data/raw

# Attempt to download a real paired dataset (if one becomes available)
# Example placeholder – replace with the verified URL when found:
# wget -O data/raw/paired_defects.csv <verified-url>
# python code/utils/checksum.py data/raw/paired_defects.csv

# If no real data exists, generate synthetic data (validation‑only mode)
python code/data_ingestion/generate_synthetic.py \
    --output data/raw/synthetic_defects.csv \
    --seed 42
python code/utils/checksum.py data/raw/synthetic_defects.csv
```

## Configuration (`code/config.yaml`)

```yaml
# Proximity threshold handling
proximity_threshold: 2.5          # nm, baseline physical value (FR‑008)
statistical_override: false       # set true to use multiplier mode
threshold_multiplier: 2.0         # used only when override is true

# Statistical settings
bootstrap_iterations: 1000        # verified fact
random_seed: 12345
```

## Running the Full Pipeline

```bash
python code/main.py --config code/config.yaml
```

- **When real data is present**: the script will perform graph construction, metric extraction, statistical analysis, bootstrap confidence intervals, multiple‑comparison correction, and sensitivity analysis.  
- **When only synthetic data is present**: the script runs up to metric extraction, logs “validation‑only mode”, and exits without hypothesis testing.

## Outputs

- **Results JSON**: `results/analysis_results.json` (validated against `contracts/analysis.schema.yaml`).  
- **Plots**: `results/plots/` (scatter plots with regression lines).  
- **Logs**: `logs/pipeline.log`.  

## Testing

```bash
# Unit tests
pytest tests/unit/

# Integration test (runs pipeline on synthetic data)
pytest tests/integration/
```

## Troubleshooting

- **Memory errors**: Ensure streaming ingestion is active (`chunksize` in `pandas.read_csv` or `streaming=True` for HuggingFace datasets).  
- **No real data**: Check `logs/pipeline.log` for the fallback message; synthetic data will be used automatically.  
- **Disconnected graph warnings**: Appear in the log; metrics are still computed on the LCC and flagged.

---


