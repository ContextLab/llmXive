# Quickstart: llmXive Follow-up: Extending EnterpriseClawBench

## Prerequisites

- Python 3.11+
- Sufficient RAM available (for CPU-only training)
- `EnterpriseClawBench` dataset files in `data/raw/` (or configured loader)

## Installation

1. **Clone the repository** and navigate to the project root.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins `torch` to CPU-only versions and excludes `bitsandbytes`.*

## Data Setup

Ensure the `EnterpriseClawBench` raw logs are present in `data/raw/`.
- If using the local loader, place logs in `data/raw/enterprise_clawbench/`.
- Run the checksum verification script:
  ```bash
  python code/src/utils/check_data.py
  ```

## Running the Pipeline

### 1. Data Feasibility & Citation Verification (Phase 0)
Check data availability and verify citations.
```bash
python code/main.py --stage verify --input data/raw/
```
*If data is missing, this stage halts the pipeline.*

### 2. Feature Extraction (FR-001)
Extract syntactic, pragmatic, and semantic proxy features from raw logs.
```bash
python code/main.py --stage extract --input data/raw/ --output data/processed/features.json
```

### 3. Triplet Construction (FR-002)
Construct training triplets from extracted features.
```bash
python code/main.py --stage pair --input data/processed/features.json --output data/processed/triplets.json
```

### 4. Model Training (FR-003)
Train the T5-small adapter on CPU.
```bash
python code/main.py --stage train --input data/processed/triplets.json --epochs [training_duration] --batch-size 4
```
*Note: The script automatically monitors RAM and will reduce batch size if it approaches 7GB.*

### 5. Evaluation (FR-004, FR-005)
Evaluate the adapter on the Lite set

The research question remains: How effective is the adapter across diverse tasks?
Method: Benchmarking on the Lite task suite.
References: [Preserve original citations verbatim] and compute statistical significance (McNemar's Test).
```bash
python code/main.py --stage evaluate --input data/processed/triplets.json --lite-set data/lite/ --output data/processed/results.csv
```

### 6. Versioning & State Update (Phase 5)
Generate content hashes and update the project state.
```bash
python code/src/utils/hash_artifacts.py
```

## Verification

- **Memory Check**: Review `code/logs/training.log` for "Peak RSS" entries. Must be ≤ 7GB.
- **Statistical Check**: Review `data/processed/results.csv` for the `p_value` column (McNemar's test).
- **Reproducibility**: Re-run the pipeline with `--seed 42` to ensure identical results.
