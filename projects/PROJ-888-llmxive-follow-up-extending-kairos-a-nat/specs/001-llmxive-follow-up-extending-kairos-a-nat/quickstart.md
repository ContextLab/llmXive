# Quickstart: llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

## 1. Prerequisites

- Python 3.11+
- `pip`
- Access to Hugging Face Hub (for `lerobot/libero_plus`).
- GitHub Actions Free Tier runner (2-core, 7GB RAM) for execution.

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-888-llmxive-follow-up-extending-kairos-a-nat

# Install dependencies
pip install -r code/requirements.txt
```

## 3. Data Preparation

The pipeline automatically downloads `lerobot/libero_plus` via the `datasets` library.
```bash
python code/main.py --mode download --dataset lerobot/libero_plus
```
*Note: If `lerobot/libero_plus` is not found or schema is invalid, the script will exit with an error. Do not attempt to substitute with other datasets.*

## 4. Running the Pipeline

Execute the full study (quantization, training, analysis):
```bash
python code/main.py --mode full --horizons 100,500,1000 --bits 4,6,8,16
```

### Key Arguments
- `--mode`: `download`, `quantize`, `train`, `analyze`, `full`.
- `--horizons`: List of prediction horizons.
- `--bits`: Quantization levels to test.
- `--seed`: Random seed for reproducibility.

## 5. Verifying Results

Check the `results/` directory for artifacts:
- `stats_results.json`: LMM p-values and coefficients.
- `power_analysis_report.json`: Required sample size $N$.
- `resource_profile.json`: CPU/RAM usage logs.

Run tests:
```bash
pytest tests/
```

## 6. Troubleshooting

- **OOM Error**: Reduce dataset subset size in `config.py`.
- **1-bit Collapse**: Script will exit with code 1. Check quantization level.
- **Dataset Not Found**: Verify internet access and HF Hub availability for `lerobot/libero_plus`.