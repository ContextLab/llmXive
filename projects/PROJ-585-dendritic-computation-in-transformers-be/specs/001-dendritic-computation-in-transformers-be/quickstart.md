# Quickstart: Dendritic Computation in Transformers

## Prerequisites

- Python 3.11+
- pip
- Git
- At least 14 GB of free disk space
- CPU-only environment (no GPU required)

## Installation

1. **Clone the repository**
 ```bash
 git clone
 cd dendritic-transformers
 ```

2. **Create a virtual environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**
 ```bash
 pip install -r requirements.txt
 ```
 *Note: `requirements.txt` pins CPU-only versions of PyTorch and other libraries.*

4. **Download and verify datasets**
 ```bash
 python code/utils/download_data.py
 ```
 This script downloads the SST-2 dataset from verified HuggingFace sources and generates checksums.

## Running the Experiments

### 1. Train Baseline and Dendritic Models

Run the training script for both architectures across multiple seeds:

```bash
python code/experiments/train.py --config config.yaml
```

- This will train the baseline and dendritic models for multiple seeds.
- A hard timeout is enforced per run.
- Logs and checkpoints are saved to `data/experiments/`.

### 2. Perform Probing Analysis

After training, run the probing pipeline:

```bash
python code/experiments/probe.py --input-dir data/experiments/
```

- This trains linear classifiers on intermediate layers.
- Results are saved to `data/experiments/[seed]/probing_results.json`.

### 3. Statistical Analysis

Generate final statistics and plots:

```bash
python code/experiments/analyze.py
```

- Performs paired Wilcoxon tests.
- Applies Benjamini-Hochberg correction for multiple comparisons.
- Outputs summary statistics and effect sizes.

## Verification

To verify the implementation:

1. **Check Architecture Matching**
 ```bash
 python code/tests/test_architecture_match.py
 ```
 Ensures parameter and FLOP counts match within tolerance.

2. **Check Data Integrity**
 ```bash
 python code/tests/test_data_hygiene.py
 ```
 Verifies checksums and file existence.

3. **Run Unit Tests**
 ```bash
 pytest code/tests/
 ```

## Troubleshooting

- **Out of Memory**: Reduce `batch_size` in `config.yaml`. The default is set for a moderate amount of RAM.
- **Training Timeout**: The script automatically stops after a predefined duration. If results are incomplete, check `logs.jsonl` for the final step.
- **Dataset Errors**: Ensure `data/raw/glue_sst2/` contains the downloaded files. Re-run `download_data.py` if checksums fail.

## Next Steps

- Review `research.md` for detailed methodology.
- Examine `data/experiments/` for specific results.
- Contribute to the paper draft in `docs/paper.md`.
