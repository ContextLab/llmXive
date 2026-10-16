# Data Model: Neural Narrative Networks

## Overview
Defines schemas, file formats, and transformation pipelines for all data artifacts. All artifacts reside under `data/` and are version‑tracked via SHA‑256 checksums.

## Data Flow
1. **Raw Ingestion** – download OpenNeuro ds001495 parquet (`test-00000-of-00016.parquet`) and ROCStories parquet.  
2. **Preprocessing** – ROI extraction → HRF‑aligned event averages → combined neural matrix.  
3. **Story Corpora** –  
   - **Pre‑training Corpus**: ROCStories (pre‑training only) → `data/processed/text/rocstories_pretrain.jsonl`.  
   - **Test Corpus**: Story transcripts extracted from OpenNeuro ds001495 → `data/processed/text/fMRI_story_transcripts.jsonl`.  
4. **Model Input** – tokenized test corpus with event boundaries.  
5. **Model Output** – hidden‑state tensors for each story event (brain‑inspired & baseline).  
6. **Analysis** – RSA matrices (CSV) and permutation test results (CSV).  

## Entity Definitions

| Entity | Description | Format | Key Fields |
|--------|-------------|--------|------------|
| **Neural Timecourse** | HRF‑aligned BOLD matrix per ROI | `.npy` | `subject_id`, `roi`, `shape`, `checksum` |
| **Narrative Representation (Pre‑training)** | Hidden‑state vectors from SAE pre‑training on ROCStories (not used for RSA) | `.pt` | `model_type` = `"pretrain"`, `story_id`, `event_idx` |
| **Narrative Representation (Test)** | Hidden‑state vectors per story event from the **held‑out fMRI story set** | `.npy` or `.pt` | `model_type` (`"brain_inspired"` or `"baseline"`), `story_id`, `event_idx`, `sparsity_ratio` (SAE only) |
| **RSA Matrix** | Pairwise similarity (Pearson) between neural and model RDMs per ROI | `.csv` | `roi`, `model_type`, `shape`, `similarity_metric` |
| **Permutation Result** | Difference statistic, p‑value, convergence metrics | `.csv` | `observed_difference`, `p_value`, `permutations`, `convergence_variance`, `is_significant` |
| **Story Corpus (Pre‑training)** | ROCStories subset for model pre‑training | `.jsonl` | `story_id`, `text`, `event_boundary_method` = `"provided"` |
| **Story Corpus (Test)** | fMRI story transcripts used for RSA | `.jsonl` | `story_id`, `text`, `event_boundary_method` = `"inferred_nltk"` |

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
│   └── text/
│       ├── rocstories_pretrain.jsonl   # pre‑training corpus
│       └── fMRI_story_transcripts.jsonl   # test corpus extracted from OpenNeuro
├── analysis/
│   ├── rsa_matrices/
│   │   ├── brain_inspired_rsm.csv
│   │   └── baseline_rsm.csv
│   └── results/
│       └── permutation_test_results.csv
```

## Transformation Logic

1. **ROI Extraction** (`preprocess.py`)  
   - Load fMRI parquet (streaming).  
   - Apply Harvard‑Oxford masks (threshold 25 %).  
   - If DLPFC mask missing, use MNI coordinates (± 6 mm).  
   - FIR deconvolution (`statsmodels` FIR design) → event‑wise averages.  
   - Save each ROI as `.npy` with checksum.

2. **Story Processing** (`download_text.py` + `preprocess.py`)  
   - Load ROCStories parquet; convert to JSONL (`rocstories_pretrain.jsonl`).  
   - Extract story transcripts from OpenNeuro metadata; infer sentence boundaries via NLTK if not supplied.  
   - Save test corpus as `fMRI_story_transcripts.jsonl`. Verify **≥ 100** stories; abort otherwise.

3. **Model Generation** (`generator.py`)  
   - Load **test** corpus only.  
   - Pass through Sparse Autoencoder + Gating (brain‑inspired) or TinyLSTM (baseline) to obtain hidden states; enforce sparsity ≤ 0.20 for SAE. Save hidden‑state tensors.

4. **RSA Computation** (`rsa_computation.py`)  
   - Load neural ROI `.npy` and model hidden states from the **test corpus** only.  
   - Compute RDMs (1 – Pearson) and correlate neural‑model RDMs. Export symmetric CSV matrices.

5. **Permutation Test** (`permutation_test.py`)  
   - Shuffle story labels, recompute RSA difference, repeat **2 000** permutations; stop early if variance < 0.001 over last 1 000 iterations.  
   - Apply Holm‑Bonferroni across ROIs.

6. **Visualization** (`visualization.py`)  
   - Heatmaps of RSA matrices (seaborn).  
   - Bar plot of RSA distances with 95 % CI and significance stars.

---

