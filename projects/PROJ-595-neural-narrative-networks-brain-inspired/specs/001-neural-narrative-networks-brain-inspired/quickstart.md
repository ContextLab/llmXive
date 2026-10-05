# Quickstart: Neural Narrative Networks

## Prerequisites

- Python 3.11+
- `pip` (or `conda`)
- 7 GB+ RAM
- Internet access (for dataset download)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-595-neural-narrative-networks-brain-inspired
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Data Ingestion

Run the data ingestion pipeline to download and preprocess datasets:

```bash
python code/data_ingestion/download_neural.py
python code/data_ingestion/download_text.py
python code/data_ingestion/preprocess.py
```

*Note: This step may take a variable duration depending on network speed. It includes HRF-aligned extraction and intersection checking.*

## Model Processing

Process the shared stories using the brain-inspired (SAE) and baseline (TinyLSTM) models:

```bash
python code/models/generator.py --model sae --output data/processed/sae_stories.jsonl
python code/models/generator.py --model baseline --output data/processed/baseline_stories.jsonl
```

*Note: The model processes only the exact story stimuli from the fMRI dataset, not new generations.*

## Analysis & Visualization

Run the RSA analysis and permutation test:

```bash
python code/analysis/rsa_computation.py
python code/analysis/permutation_test.py
python code/analysis/visualization.py
```

## Verification

Verify the outputs:

1. Check that `data/processed/neural/roi_left_hipp.npy` exists and is non-empty.
2. Check that `data/analysis/results/permutation_test_results.csv` contains a p-value < 0.05 (if significant).
3. Ensure the generated stories in `data/processed/sae_stories.jsonl` have at least N >= 10 entries (the intersection size).

## Troubleshooting

- **Memory Error**: If you encounter a `MemoryError`, reduce the number of stories sampled in `preprocess.py` or enable chunked loading.
- **Missing Data**: If the pipeline halts with "ROI definition failed", verify that the OpenNeuro dataset contains the required masks or coordinates.
- **Insufficient Intersection**: If the pipeline halts with E002, the number of shared stories is insufficient for RSA. The analysis cannot proceed.
