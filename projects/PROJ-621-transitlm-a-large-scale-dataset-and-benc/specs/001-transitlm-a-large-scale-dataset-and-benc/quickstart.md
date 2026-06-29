# Quickstart: Map-Free Transit Route Generation with LLMs

## Prerequisites

- Python 3.11+
- 7GB+ RAM (GitHub Actions free-tier compatible)
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-621-transitlm-a-large-scale-dataset-and-benc
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

## Data Preparation

1. **Download GTFS Data**:
   - The script will automatically fetch the **NYC MTA GTFS Feed** from the canonical source.
   - If the live feed fails, it will generate a **deterministic synthetic GTFS** (Seed 42).
   - Place the downloaded/generated data in `data/raw/`.

2. **Run the Data Conversion Script**:
   ```bash
   python src/data/gtfs_to_text.py --input data/raw/ --output data/processed/
   ```
   - This script generates map-free text sequences and validates for coordinate leakage.

3. **Build the Ground-Truth Graph**:
   ```bash
   python src/data/build_graph.py --input data/raw/ --output data/graph/gtfs_graph.pkl
   ```

## Training (Optional)

To fine-tune the model (CPU-only):
```bash
python src/models/train.py --data data/processed/train.csv --model llama-3-1.5b --output models/fine_tuned/
```
- *Note: This step may take several hours on CPU. Adjust batch size if OOM occurs.*

## Inference & Validation

Run the full benchmark pipeline:
```bash
python src/cli/run_benchmark.py \
  --data data/processed/ \
  --graph data/graph/gtfs_graph.pkl \
  --model models/fine_tuned/ \
  --baseline zero-shot \
  --output results/benchmark_results.json
```

## Statistical Analysis

Generate the statistical report:
```bash
python src/analysis/stats.py --input results/benchmark_results.json --output results/statistical_report.md
```

## Verification

- **Coordinate Leakage Check**:
  ```bash
  grep -rE "[0-9]+\.[0-9]+" data/processed/
  ```
  - Expected output: None.

- **Schema Validation**:
  ```bash
  pytest tests/contract/
  ```

## Troubleshooting

- **OOM Error**: Reduce `batch_size` in `train.py` to 1.
- **No Routes Generated**: Check if the model is hallucinating station names. Verify `parsed_stations` extraction logic.
- **Graph Validation Fails**: Ensure the GTFS graph is built correctly and matches the station names in the text.
