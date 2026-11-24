# Data Model: Neural Narrative Networks

## Overview
Defines schemas, file formats, and transformation pipelines for all data artifacts. All artifacts reside under `data/` and are version‑tracked via SHA‑256 checksums.

## Data Flow
1. **Raw Ingestion** – download OpenNeuro ds001495 parquet and ROCStories parquet.  
2. **Preprocessing** – ROI extraction → HRF‑aligned event averages → combined neural matrix.  
3. **Story Corpora** –  
   - **Pre‑training**: ROCStories → `data/processed/text/rocstories_pretrain.jsonl`.  
   - **Test**: Story transcripts from OpenNeuro ds001495 → `data/processed/text/fMRI_story_transcripts.jsonl`.  
4. **Model Input** – tokenized test corpus with event boundaries.  
5. **Model Output** – hidden‑state tensors per story event for the held‑out fMRI story set (brain‑inspired and baseline models).  
6. **Analysis** – RSA matrices, permutation test results, mixed‑effects summary, power analysis, visualizations, and a consolidated `results_summary.csv`.  

## Entity Definitions

| Entity | Description | Format | Key Fields |
|--------|-------------|--------|------------|
| **Neural Timecourse** | HRF‑aligned BOLD matrix per ROI | `.npy` | `subject_id`, `roi`, `shape`, `checksum` |
| **Narrative Representation (Pre‑training)** | Hidden‑state vectors from the Sparse Autoencoder during ROCStories pre‑training (not used for RSA) | `.pt` | `model_type`=`"pretrain"`, `story_id`, `event_idx`, `hidden_dim`, `checksum` |
| **Narrative Representation (Test)** | Hidden‑state vectors per story event from the held‑out fMRI story set | `.npy` | `model_type` (`"brain_inspired"` or `"baseline_transformer"`), `story_id`, `event_idx`, `sparsity_ratio` (SAE only) |
| **RSA Matrix** | Pairwise similarity (Spearman & Pearson) between neural and model representations across different story conditions | `.csv` | `roi`, `model_type`, `similarity_metric`, `shape` |
| **Permutation Result** | Difference statistic, p‑value, convergence variance, significance flag | `.csv` | `observed_difference`, `p_value`, `permutations` = 10000, `convergence_variance`, `is_significant` |
| **Mixed‑Effects Summary** | Linear mixed‑effects model results (fixed effects, random intercepts, p‑values, AIC) | `.csv` | `roi`, `model_type`, `fixed_effect_estimate`, `p_value`, `AIC` |
| **Power Analysis** | Monte‑Carlo power estimate (estimated power, number of simulations, effect size assumption) | `.csv` | `estimated_power`, `n_simulations`, `effect_size`, `subject_count`, `story_count` |
| **Visualization** | PNG figures (RSA heatmaps and bar plot) | `.png` | `figure_type` (`"heatmap"` or `"bar"`), `roi` (if applicable) |
| **Results Summary** | Consolidated table of key metrics (sparsity, RAM, coherence, RSA distances, mixed‑effects p‑values, permutation p‑values, power estimate, and story count) | `.csv` | `metric_name`, `value` |
| **Narrative Text Corpus** | Processed story files for pre‑training and test | `.jsonl` | `story_id`, `text`, `event_boundary_method` |
| **Text Data Metadata** | JSON metadata satisfying `text-data.schema.yaml` | `.json` | `file_path`, `total_stories`, `sample_size`, `format`, `checksum`, `event_boundary_method` |

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
│   │   �├── roi_dlpfc.npy
│   │   └── pretrain_sae_hidden.pt
│   └── text/
│       ├── rocstories_pretrain.jsonl
│       ├── fMRI_story_transcripts.jsonl
│       └── text_data_metadata.json
├── analysis/
│   ├── rsa_matrices/
│   │   ├── brain_inspired_rsm.csv
│   │   └── baseline_transformer_rsm.csv
│   ├── results/
│   │   ├── permutation_test_results.csv
│   │   ├── mixed_effects_summary.csv
│   │   ├── power_estimate.csv
│   │   └── rsa_output_metadata.json
│   └── figures/
│       ├── rsa_heatmap_left_hipp.png
│       ├── rsa_heatmap_right_hipp.png
│       ├── rsa_heatmap_dlpfc.png
│       └── rsa_barplot.png
└── summary/
    └── results_summary.csv
```

## Transformation Logic
1. **ROI Extraction** (`preprocess.py`)  
   - Stream fMRI parquet.  
   - Apply Harvard‑Oxford masks (threshold 25 %).  
   - If DLPFC mask missing, download Harvard‑Oxford atlas via `nilearn` and extract DLPFC using MNI coordinates.  
   - FIR deconvolution → event‑wise averages.  
   - Save each ROI as `.npy` with SHA‑256 checksum.  

2. **Story Processing** (`download_text.py` + `preprocess.py`)  
   - Load ROCStories parquet; filter out any overlapping `story_id` with the fMRI transcripts; convert to JSONL (`rocstories_pretrain.jsonl`).  
   - Generate `text_data_metadata.json` containing total story count, sample size (used in analysis), checksum, and `event_boundary_method="provided"`.  
   - Extract story transcripts from OpenNeuro metadata; infer sentence boundaries via NLTK where absent, and save as `fMRI_story_transcripts.jsonl`.  

3. **Model Generation** (`generator.py`)  
   - Load **test** corpus only.  
   - **Brain‑inspired**: pass through Sparse Autoencoder + Gating, enforce sparsity ≤ 0.20, log StoryCoherence ≥ 0.70, save hidden states (`brain_inspired_hidden.npy`).  
   - **Baseline**: pass through quantized TinyBERT (pre‑trained on same ROCStories), save hidden states (`baseline_transformer_hidden.npy`).  

4. **Pre‑training Representation Save** (`sparse_autoencoder.py`)  
   - During SAE pre‑training on ROCStories, record hidden‑state vectors for each story event and serialize to `pretrain_sae_hidden.pt`.  

5. **RSA Computation** (`rsa_computation.py`)  
   - Load neural ROI `.npy` and model hidden states (test set only).  
   - Reduce both to 50 principal components (PCA) and align with Procrustes.  
   - Compute RDMs (1 – Pearson) and 1 – Spearman; correlate neural‑model RDMs **per subject**, then average across subjects. Export symmetric CSV matrices.  

6. **Permutation Test** (`permutation_test.py`)  
   - Shuffle story labels, recompute RSA difference, repeat **10 000** permutations (fixed).  
   - Record max statistic across ROIs for each permutation; compute p‑value; apply variance convergence check.  

7. **Mixed‑Effects Analysis** (`mixed_effects.py`)  
   - Fit linear mixed‑effects model (`RSA_distance ~ Model_Type + (1|Subject)`) using `pingouin`.  

8. **Power Analysis** (`power_analysis.py`)  
   - Monte‑Carlo simulation (1 000 runs) assuming medium effect size (d = 0.5), using actual subject count (≈ a moderate number of participants) and story count (several); report estimated power.  

9. **Visualization** (`visualization.py`)  
   - Heatmaps of RSA matrices (seaborn) and bar plot of RSA distances with 95 % CI and significance stars.  

10. **Metadata Generation**  
    - Write `rsa_output_metadata.json` containing `rsa_matrix` metadata (model_type, roi, similarity_metric, shape) and `permutation_result` fields to satisfy `rsa-output.schema.yaml`.  

---



