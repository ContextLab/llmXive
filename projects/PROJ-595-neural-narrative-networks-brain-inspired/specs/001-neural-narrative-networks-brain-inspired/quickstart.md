# Quickstart: Neural Narrative Networks

## Prerequisites
- Python 3.11 or newer  
- `pip` (or `conda`)  
- Internet access (for dataset download)  
- At least **7 GB** RAM (recommended for headroom)  

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
- `text/text_data_metadata.json` (metadata for contract)
- `text/fMRI_story_transcripts.jsonl` (≥ 100 stories – see plan note on dataset limitation)

## 3. Model Pre‑training (Sparse Autoencoder)
```bash
python code/models/sparse_autoencoder.py \
    --train data/processed/text/rocstories_pretrain.jsonl \
    --output models/sae_pretrained.pt \
    --save-repr data/processed/neural/pretrain_sae_hidden.pt
```
*The log --- **NOTE** --- reports the activation sparsity ratio that must be ≤ 0.20. If the ratio exceeds the threshold ... **[** ... **]** ... ... *???* *corrupted text here due to placeholder in original US‑2* *— see spec for details.* 

## 4. ****  ---  ---  **  </ ? ? ?? 



---



---



  







... 



 



...



 































---































```

