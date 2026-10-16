# Quickstart: Neural Narrative Networks

## Prerequisites
- Python 3.11 or newer  
- `pip` (or `conda`)  
- Internet access (for dataset download)  
- At least 7 GB RAM (recommended sufficient memory for headroom)  

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

## 1. Data Ingestion
```bash
python code/data_ingestion/download_neural.py   # OpenNeuro ds001495
python code/data_ingestion/download_text.py    # ROCStories (pre‑training only)
python code/data_ingestion/preprocess.py
```
*Outputs*:  
- `data/processed/neural/roi_*.npy` (left/right hippocampus, DLPFC)  
- `data/processed/text/rocstories_pretrain.jsonl` (pre‑training corpus)  
- `data/processed/text/fMRI_story_transcripts.jsonl` (held‑out test set, ≥ 100 stories).

## 2. Model Pre‑training (Sparse Autoencoder)
```bash
python code/models/sparse_autoencoder.py --train data/processed/text/rocstories_pretrain.jsonl --output model/sae_pretrained.pt
```
*The training logs will report the sparsity ratio; it must be ≤ 0.20.*

## 3. Model Generation on Test Set
```bash
# Brain‑inspired model (Sparse Autoencoder + Gating) on the fMRI story set
python code/models/generator.py --model brain_inspired \
    --input data/processed/text/fMRI_story_transcripts.jsonl \
    --output data/processed/brain_inspired_hidden.npy

# Baseline TinyLSTM (quantized) on the same test set
python code/models/generator.py --model baseline \
    --input data/processed/text/fMRI_story_transcripts.jsonl \
    --output data/processed/baseline_hidden.npy
```
*Both commands respect the CPU‑only memory caps and will abort with a clear error if RAM exceeds 7 GB.*

## 4. RSA Analysis & Permutation Test
```bash
python code/analysis/rsa_computation.py   # computes RSA matrices
python code/analysis/permutation_test.py   # A large number of permutations with early‑stopping
python code/analysis/visualization.py      # generates heatmaps & bar plot
```
*Key outputs*:
- `data/analysis/rsa_matrices/brain_inspired_rsm.csv`
- `data/analysis/rsa_matrices/baseline_rsm.csv`
- `data/analysis/results/permutation_test_results.csv`
- `figures/` (heatmaps & bar plot)

## 5. Verification
```bash
# Check that neural files exist and are non‑empty
ls data/processed/neural/roi_*.npy
# Verify story count in the test set
python -c "cnt=sum(1 for _ in open('data/processed/text/fMRI_story_transcripts.jsonl')); print('Test stories:', cnt)"
# Inspect permutation result
head data/analysis/results/permutation_test_results.csv
```

## Troubleshooting
- **MemoryError**: Reduce the number of stories processed (`--max_stories 2000`) or enable chunked loading (`preprocess.py --chunk_size 100`).  
- **Missing ROI**: If DLPFC mask not found, the pipeline automatically falls back to Harvard‑Oxford coordinates; check the log for the fallback message.  
- **Insufficient Test Stories**: If fewer than 100 shared stories are found, the pipeline halts with error `E002`. In that case, verify the OpenNeuro dataset version or consider a different open fMRI story dataset.  

Enjoy reproducible, brain‑inspired story generation!  

---

