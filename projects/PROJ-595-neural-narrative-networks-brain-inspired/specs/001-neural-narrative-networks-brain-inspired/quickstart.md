# Quickstart: Neural Narrative Networks

## Prerequisites
- Python 3.11 or newer  
- `pip` (or `conda`)  
- Internet access (for dataset download)  
- At least 7 GB RAM (recommended for headroom)  

## Installation
```bash
# Clone the repository (replace <repo-url> with the actual URL)
git clone <repo-url>
cd projects/PROJ-595-neural-narrative-networks-brain-inspired

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r code/requirements.txt
```

## 1. Project Setup
```bash
# Create a standard .gitignore (required for verification)
python - <<'PY'
import pathlib, textwrap
p = pathlib.Path('.gitignore')
p.write_text(textwrap.dedent('''\
    __pycache__/
    *.pyc
    *.pyo
    *.pyd
    .Python
    env/
    venv/
    build/
    develop-eggs/
    dist/
    downloads/
    eggs/
    .eggs/
    lib/
    lib64/
    parts/
    sdist/
    var/
    *.egg-info/
    .installed.cfg
    *.manifest
    *.spec
    data/raw/
    data/processed/
    .mypy_cache/
    .pytest_cache/
    .coverage
    htmlcov/
    .tox/
    .nox/
    .coverage.*
    coverage.xml
    *.cover
    .cache/
    .ipynb_checkpoints/
    .DS_Store
    '''))
PY
```

## 2. Data Ingestion
```bash
# Download and preprocess fMRI data
python code/data_ingestion/download_neural.py   # OpenNeuro ds001495

# Download ROCStories (pre‑training only)
python code/data_ingestion/download_text.py    # ROCStories

# Preprocess both modalities
python code/data_ingestion/preprocess.py
```
*Outputs* (under `data/processed/`):
- `neural/roi_left_hipp.npy`, `roi_right_hipp.npy`, `roi_dlpfc.npy`
- `text/rocstories_pretrain.jsonl`
- `text/fMRI_story_transcripts.jsonl` (≥ 100 stories)

## 3. Model Pre‑training (Sparse Autoencoder)
```bash
python code/models/sparse_autoencoder.py \
    --train data/processed/text/rocstories_pretrain.jsonl \
    --output models/sae_pretrained.pt \
    --save-repr data/processed/neural/pretrain_sae_hidden.pt
```
*The log reports the activation sparsity ratio; it must be ≤ 0.20.*

## 4. Story Generation on Test Set
```bash
# Brain‑inspired model (SAE + gating)
python code/models/generator.py --model brain_inspired \
    --input data/processed/text/fMRI_story_transcripts.jsonl \
    --output data/processed/brain_inspired_hidden.npy

# Baseline model (quantized TinyLSTM)
python code/models/generator.py --model baseline_transformer \
    --input data/processed/text/fMRI_story_transcripts.jsonl \
    --output data/processed/baseline_transformer_hidden.npy \
    --quantize bitsandbytes
```
Both commands respect the CPU‑only memory caps and will abort with a clear error if RAM exceeds 7 GB.

## 5. RSA Analysis & Permutation Test
```bash
# Compute RSA matrices (Pearson & Spearman)
python code/analysis/rsa_computation.py

# Run permutation test (2 000 permutations, no early‑stopping)
python code/analysis/permutation_test.py

# Generate figures
python code/analysis/visualization.py
```
*Key outputs*:
- `analysis/rsa_matrices/brain_inspired_rsm.csv`
- `analysis/rsa_matrices/baseline_transformer_rsm.csv`
- `analysis/results/permutation_test_results.csv`
- `figures/` (heatmaps & bar plot)

## 6. Verification
```bash
# Verify .gitignore exists
ls .gitignore

# Check neural files exist and are non‑empty
ls data/processed/neural/roi_*.npy

# Confirm story count in the test set
python -c "cnt=sum(1 for _ in open('data/processed/text/fMRI_story_transcripts.jsonl')); print('Test stories:', cnt)"

# Validate contracts
python -m pytest tests/contract/  # assumes contract tests are provided
```

## Troubleshooting
- **MemoryError**: Reduce the number of stories processed (`--max_stories 2000`) or enable chunked loading (`preprocess.py --chunk_size 100`).  
- **Missing DLPFC mask**: The pipeline automatically falls back to Harvard‑Oxford coordinates; check the log for the fallback message.  
- **Insufficient Test Stories**: If fewer than 100 stories are found, the pipeline halts with error `E002`. Verify the OpenNeuro dataset version or consider an alternative open fMRI story dataset.  

You now **have a fully reproducible, CPU‑compatible pipeline** for evaluating brain‑inspired narrative generation against human fMRI data. Enjoy!  

---


