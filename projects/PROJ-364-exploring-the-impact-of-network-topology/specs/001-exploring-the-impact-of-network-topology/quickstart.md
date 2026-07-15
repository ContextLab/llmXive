# Quickstart: Exploring the Impact of Network Topology on Heat Dissipation in 2D Materials

## Prerequisites

- Python 3.11+
- `git`
- Access to a GitHub Actions runner (or a local machine with ≤ 7 GB RAM)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-364-exploring-the-impact-of-network-topology
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Data Setup

1. **Check for real data**: Verify if a paired defect/conductivity dataset is available. If yes, download and checksum it.
   ```bash
   mkdir -p data/raw
   # Example (if dataset found):
   # wget -O data/raw/paired_defects.csv <verified-url>
   # python code/utils/checksum_data.py data/raw/paired_defects.csv
   ```

2. **If no real data is found**, generate synthetic data (validation only):
   ```bash
   python code/data_ingestion/generate_synthetic.py --output data/raw/synthetic_defects.csv --seed 42
   # Record checksum of the generated file
   python code/utils/checksum_data.py data/raw/synthetic_defects.csv
   ```

## Running the Pipeline

Execute the full analysis:

```bash
python code/main.py --config code/config.yaml
```

### Configuration (`code/config.yaml`)

Key fields you may adjust:

```yaml
proximity_threshold: 2.0          # nm, baseline physical value
threshold_multiplier: 2.0         # used only when statistical_override=true
statistical_override: false
bootstrap_iterations: 1000
random_seed: 12345
```

## Output

- **Results**: `results/analysis_results.json` (validated against `analysis.schema.yaml`).  
- **Plots**: `results/plots/` (scatter plots with regression lines).  
- **Logs**: `logs/pipeline.log`.  

## Testing

Unit tests:

```bash
pytest code/tests/unit/
```

Integration test (full pipeline on synthetic data):

```bash
pytest code/tests/integration/
```

## Troubleshooting

- **Memory errors**: Ensure `streaming=True` is set in the data loader (default).  
- **No real data**: Verify the checksum log; if the download fails, fall back to synthetic data (validation only).  
- **Graph disconnected warnings**: Check the log; metrics are still computed on the LCC and flagged accordingly.