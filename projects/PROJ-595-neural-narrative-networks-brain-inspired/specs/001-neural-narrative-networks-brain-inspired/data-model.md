# Data Model: Neural Narrative Networks

## Overview
Defines schemas, file formats, and transformation pipelines for all data artifacts. All artifacts reside under `data/` and are version‑tracked via SHA‑256 checksums.

## Data Flow
1. **Raw Ingestion** – download OpenNeuro ds001495 parquet and ROCStories parquet.  
2. **Preprocessing** – ROI extraction → HRF‑aligned event averages → combined neural matrix.  
3. **Story Corpora** –  
   - **Pre‑training**: ROCStories → `data/processed/text/rocstories_pretrain.jsonl`.  
   - **Test**: Story transcripts from OpenNeuro → `data/processed/text/fMRI_story_transcripts.jsonl`.  
4. **Model Input** – tokenized test corpus with event boundaries.  
5. **Model Output** – hidden‑state tensors per story event for the held‑out fMRI story set (brain‑inspired and baseline).  
6. **Analysis** – RSA matrices (CSV) and permutation test results (CSV).  

## Entity Definitions

| Entity | Description | Format | Key Fields |
|--------|-------------|--------|------------|
| **Neural Timecourse** | HRF‑aligned BOLD matrix per ROI | `.npy` | `subject_id`, `roi`, `shape`, `checksum` |
| **Narrative Representation (Pre‑training)** | Hidden‑state vectors from the Sparse Autoencoder during ROCStories pre‑training (not used for RSA). | `.pt` | `model_type`=`"pretrain"`, `story_id`, `event_idx`, `hidden_dim`, `checksum` |
| **Narrative Representation (Test)** | Hidden‑state vectors per story event from the held‑out fMRI story set. | `.npy` or `.pt` | `model_type` (`"brain_inspired"` or `"baseline_transformer"`), `story_id`, `event_idx`, `sparsity_ratio` (SAE only) |
| **RSA Matrix** | Pairwise similarity (Pearson and Spearman) between neural and model representations across different story conditions. | `.csv` | `roi`, `model_type`, `similarity_metric`, `shape` |
| **Permutation Result** | Difference statistic, p‑value, convergence, and significance flag. | `.csv` | `observed_difference`, `p_value`, `permutations`, `convergence_variance`, `is_significant` |
| **Story Corpus (Pre‑training)** | ROCStories subset for model pre‑training. | `.jsonl` | `story_id`, `text`, `event_boundary_method`=`"provided"` |
| **Story Corpus (Test)** | fMRI story transcripts used for RSA. | `.jsonl` | `story_id`, `text`, `event_boundary_method`=`"inferred_nltk"` |

## Storage Layout
```text
data/
├── raw/
│   ├── openneuro/
│   │   └── test-00000-of-00016.parquet
│   └── rocstories/
│       └── train-00000-of-00001-c17b7a9172e87209.parquet
├── processed/
│   ├── neural/
│   │   ├── roi_left_hipp.npy
│   │   ├── roi_right_hipp.npy
│   │   └── roi_dlpfc.npy
│   │   └── pretrain_sae_hidden.pt   # new artifact
│   └── text/
│       ├── rocstories_pretrain.jsonl
│       └── fMRI_story_transcripts.jsonl
├── analysis/
│   ├── rsa_matrices/
│   │   ├── brain_inspired_rsm.csv
│   │   └── baseline_transformer_rsm.csv
│   └── results/
│       └── permutation_test_results.csv
```

## Transformation Logic
1. **ROI Extraction** (`preprocess.py`)  
   - Stream fMRI parquet.  
   - Apply Harvard‑Oxford masks (threshold 25 %).  
   - If DLPFC mask missing, use MNI coordinates fallback.  
   - FIR deconvolution (`statsmodels` FIR design) → event‑wise averages.  
   - Save each ROI as `.npy` with SHA‑256 checksum.

2. **Story Processing** (`download_text.py` + `preprocess.py`)  
   - Load ROCStories parquet; convert to JSONL (`rocstories_pretrain.jsonl`).  
   - Extract story transcripts from OpenNeuro metadata; infer sentence boundaries via NLTK if absent; save as `fMRI_story_transcripts.jsonl`.  
   - Verify **≥ 100** stories; abort otherwise.

3. **Model Generation** (`generator.py`)  
   - Load **test** corpus only.  
   - For brain‑inspired: pass through Sparse Autoencoder + Gating, enforce sparsity ≤ 0.20, save hidden states (`brain_inspired_hidden.npy`).  
   - For baseline: pass through quantized TinyLSTM, save hidden states (`baseline_transformer_hidden.npy`).  

4. **Pre‑training Representation Save** (`sparse_autoencoder.py`)  
   - During SAE pre‑training on ROCStories, record hidden‑state vectors for each story event and serialize to `pretrain_sae_hidden.pt`.  

5. **RSA Computation** (`rsa_computation.py`)  
   - Load neural ROI `.npy` and model hidden states (test set only).  
   - Compute RDMs (1 – Pearson) and 1 – Spearman; correlate neural‑model RDMs per ROI **per subject**, then average across subjects. Export symmetric CSV matrices.

6. **Permutation Test** (`permutation_test.py`)  
   - Shuffle story labels, recompute RSA difference, repeat **2 000** permutations (fixed); no early‑stopping.  
   - Apply Holm‑Bonferroni across ROIs.

7. **Visualization** (`visualization.py`)  
   - Heatmaps of RSA matrices (seaborn).  
   - Bar plot of RSA distances with 95 % CI and significance stars.

---

