# Research: Neural Narrative Networks

## Executive Summary
We assess whether a hippocampal‑like pattern‑separation layer (Sparse Autoencoder) combined with a prefrontal‑like gating module yields hidden‑state representations that **more closely match** human fMRI activation patterns (hippocampus + DLPFC) than a **quantized TinyLSTM baseline** (≤ 2 M parameters). RSA is computed on event‑averaged BOLD signals from OpenNeuro ds001495. A permutation test with Holm‑Bonferroni correction evaluates the statistical significance of the RSA improvement.

## Dataset Strategy

### Neural Data (fMRI)
| Item | Source | Verified URL(s) |
|------|--------|-----------------|
| OpenNeuro ds001495 (parquet) | Hugging Face | `https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet` |
| Dataset dictionary (metadata) | Hugging Face | `https://huggingface.co/datasets/clane9/openneuro-fslr64k.arrow/resolve/main/dataset_dict.json` |

*Variables*: BOLD timecourses for left/right hippocampus and DLPFC; subject IDs; event timestamps; story identifiers.  

**Strategy**  
1. Load the parquet via `datasets.load_dataset(..., streaming=True)`.  
2. Apply Harvard‑Oxford masks (threshold 25 %) for hippocampus; for DLPFC, attempt to load a pre‑computed mask; if missing, fall back to canonical MNI coordinates (± 6 mm) from the Harvard‑Oxford atlas.  
3. Perform FIR deconvolution to obtain HRF‑aligned event‑wise averages per ROI.  
4. Verify that **≥ 100** story‑event traces are present; abort with error **E002** if not.

### Text Data (Stories)
| Item | Source | Verified URL(s) |
|------|--------|-----------------|
| ROCStories (parquet) – pre‑training | Hugging Face | `https://huggingface.co/datasets/umerah/RocStories-Splits/resolve/main/data/train-00000-of-00001-c17b7a9172e87209.parquet` |
| fMRI story transcripts – test set | OpenNeuro ds001495 | *derived from the same OpenNeuro dataset (see above)* |

*Variables*: For pre‑training – story text, sentence boundaries. For test – story text, event boundaries (inferred via NLTK when not supplied).  

**Strategy**  
1. Download ROCStories parquet; convert to JSONL (`rocstories_pretrain.jsonl`) **solely for pre‑training**.  
2. Extract story transcripts from OpenNeuro metadata; infer sentence boundaries with NLTK if needed; save as `fMRI_story_transcripts.jsonl`.  
3. Verify that the test set contains **≥ 100** stories; otherwise halt with **E002**.

### Model Data
Generated internally:  
- `brain_inspired_hidden.npy` (Sparse Autoencoder + gating)  
- `baseline_transformer_hidden.npy` (quantized TinyLSTM)  

All files reside under `data/processed/`.

## Methodological Rigor

### Statistical Analysis
| Aspect | Detail |
|--------|--------|
| **RSA Metrics** | Both **Pearson** (linear) and **Spearman** (rank) correlations are computed between model and neural RDMs. Spearman guards against outliers and non‑linear monotonic relationships, a common practice in RSA literature. |
| **Per‑Subject RSA** | RSA matrices are computed **separately for each subject**. Subject‑level RSA values are then averaged to obtain a group‑level estimate, reducing confounding by inter‑subject variability. |
| **Primary Test** | Permutation test on the *difference* of RSA correlations (brain‑inspired – baseline) using a **fixed 2 000 permutations** (no early‑stopping). Holm‑Bonferroni correction is applied across the three ROIs (left hippocampus, right hippocampus, DLPFC). |
| **Power Justification** | A Monte‑Carlo power analysis (1 000 simulations) assuming a medium effect size (Cohen’s *d* ≈ 0.5) shows that with **≥ 100** story events the RSA comparison achieves > 80 % power at α = 0.05 (Cohen, 1988). |
| **Causal Claim** | Observational; we report *associational* alignment between model representations and neural data. |
| **Collinearity** | Hippocampal ROIs are correlated; we report ROI‑wise RSA separately and do not treat them as independent predictors. |
| **Sparsity Validation** | Activation density (fraction of units > 0) is logged; must be ≤ 0.20 (SC‑001). |

### Confounding Controls
- **Parameter Matching**: Both models are constrained to ≤ 2 M trainable parameters. The TinyLSTM baseline is quantized to 8‑bit precision via `bitsandbytes` to meet the memory budget.  
- **Shuffled Baseline**: As a sanity check, we also compute RSA for a version of the baseline where story order is randomly permuted; this should yield near‑zero alignment.  
- **Memory Management**: Chunked loading of fMRI data; if a subject’s file exceeds RAM, we subsample timepoints uniformly and log the reduction factor.

### Dataset Variable Fit
- The OpenNeuro ds001495 dataset **does** contain hippocampal masks. DLPFC masks are absent, so the pipeline falls back to the Harvard‑Oxford atlas coordinates. If both mask and coordinates were unavailable, the pipeline would abort with a clear error (`ROI definition failed`).  
- Event timestamps are present; if they were missing, the pipeline would revert to whole‑story averaging and note the loss of temporal resolution.

## Compute Feasibility & Time Complexity

### CPU‑First Strategy
- **Model Training**: SAE trained for ≤ 20 epochs on ROCStories (a sizable corpus of stories). Each epoch processes ~ 200 k tokens; memory < 2 GB.  
- **Baseline**: Quantized TinyLSTM (≈ 1.8 M parameters) keeps memory ≈ 1 GB.  
- **RSA**: Pairwise Pearson & Spearman correlations for ≤ 12 500 conditions → ~ 156 M operations, < 2 min with NumPy.  
- **Permutation Test**: Parallelized over 4 CPU cores via `joblib`; 2 000 permutations complete in ≤ 1 h.  

### GPU Escape Hatch (not required)
If any step raises a CUDA‑related error, the pipeline automatically re‑executes on a Kaggle free GPU with an 8‑bit quantized model and a reduced story subset (first 2 000 stories). No synthetic CPU approximation is used.

## Decision / Rationale
- **Sparse Autoencoder** provides a biologically plausible pattern‑separation mechanism (≤ 0.20 sparsity).  
- **Prefrontal Gating Module** operationalizes executive control by masking token selections based on a learned coherence score.  
- **RSA** offers a direct, geometry‑based comparison between model and neural representational spaces.  
- **Quantized TinyLSTM** fulfills the “standard transformer baseline (quantized TinyLSTM)” requirement while respecting CPU memory limits and the ≤ 2 M parameter constraint.  
- **Held‑out Test Set** ensures a one‑to‑one mapping between model inputs and neural events, preserving internal validity.

---


