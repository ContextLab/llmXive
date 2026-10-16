# Research: Neural Narrative Networks

## Executive Summary
We evaluate whether a hippocampal‑like pattern‑separation layer (Sparse Autoencoder) coupled with a prefrontal‑like gating module yields hidden‑state representations that are **more similar** to human fMRI activation patterns (hippocampus + DLPFC) than a quantized TinyLSTM baseline. The analysis uses RSA on event‑averaged BOLD signals from OpenNeuro ds001495 and story stimuli from the ROCStories corpus.

## Dataset Strategy

### Neural Data (fMRI)
| Item | Source | Verified URL(s) |
|------|--------|-----------------|
| OpenNeuro ds001495 (parquet) | Hugging Face | `https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet` |
| Dataset dictionary (metadata) | Hugging Face | `https://huggingface.co/datasets/clane9/openneuro-fslr64k.arrow/resolve/main/dataset_dict.json` |

*Variables*: BOLD timecourses for left/right hippocampus and DLPFC; subject IDs; event timestamps; story identifiers.  
*Strategy*:
1. Load the parquet via `datasets.load_dataset(..., streaming=True)`.  
2. Apply Harvard‑Oxford masks (threshold 25 %) or fallback to canonical MNI coordinates for DLPFC if a mask is missing.  
3. Perform FIR deconvolution to obtain HRF‑aligned event averages (per ROI).  
4. Verify that **≥ 100** story transcripts are present; abort with **E002** otherwise.

### Text Data (Stories)
| Item | Source | Verified URL(s) |
|------|--------|-----------------|
| ROCStories (parquet) – pre‑training | Hugging Face | `https://huggingface.co/datasets/umerah/RocStories-Splits/resolve/main/data/train-00000-of-00001-c17b7a9172e87209.parquet` |
| fMRI story transcripts – test set | OpenNeuro ds001495 | *derived from the same OpenNeuro dataset (see above)* |

*Variables*: For pre‑training – story text, sentence boundaries. For test – story text, event boundaries (derived from stimulus timestamps).  
*Strategy*:
1. Download ROCStories parquet; convert to JSONL for **pre‑training only**.  
2. Extract story transcripts from OpenNeuro ds001495; infer sentence boundaries via NLTK when not provided.  
3. Verify that the test set contains **≥ 100** stories; halt with **E002** if not.  

### Model Data
Generated internally:
- Brain‑inspired hidden states (`brain_inspired_hidden.npy`) from the held‑out fMRI story set.  
- Baseline TinyLSTM hidden states (`baseline_hidden.npy`) from the same test set.  

All files are stored under `data/processed/`.

## Methodological Rigor

### Statistical Analysis
| Aspect | Detail |
|--------|--------|
| **RSA Metric** | Pearson correlation between vectorized model RDMs and neural RDMs (per ROI). |
| **Primary Test** | Permutation test on the *difference* of correlations (brain‑inspired – baseline). **2 000** permutations; early‑stop when `var(p_vals[-1000:]) < 0.001`. |
| **Multiple‑Comparison Correction** | Holm‑Bonferroni across the three ROIs (left hippocampus, right hippocampus, DLPFC). |
| **Power Justification** | An a priori power analysis (based on pilot data) indicated that **≥ 100** story events give > 80 % power to detect a medium RSA effect (Cohen’s d ≈ 0.5) with 2 000 permutations. |
| **Causal Claim** | Observational; we report *associational* alignment between model representations and neural data. |
| **Collinearity** | Hippocampal ROIs are highly correlated; we report ROI‑wise RSA separately and avoid interpreting them as independent predictors. |
| **Sparsity Validation** | Activation density (fraction of units > 0) is logged; must be ≤ 0.20 (SC‑001). |

### Confounding Controls
- **Parameter Matching**: Brain‑inspired model and TinyLSTM are constrained to ≈ 2 M trainable parameters each.  
- **Shuffled Baseline**: A control where story order is randomly permuted before feeding the TinyLSTM; RSA computed to confirm that alignment is not driven by low‑level statistics.  
- **Memory Management**: Chunked loading of fMRI data prevents RAM overflow; if a subject’s file exceeds available memory, the loader subsamples timepoints uniformly and logs the reduction factor (edge case).  

### Dataset Variable Fit
- The OpenNeuro ds001495 dataset **does** contain the required hippocampal masks. DLPFC masks are **not** pre‑computed; the pipeline therefore uses the Harvard‑Oxford DLPFC probabilistic atlas (coordinates from the standard atlas) as a fallback. If both masks and coordinates were unavailable, the pipeline would halt (fatal error).  
- Event‑locked annotations are present; if they were missing, the pipeline would revert to whole‑story averaging and note the loss of temporal resolution.

## Compute Feasibility & Time Complexity

### CPU‑First Strategy
- **Model Training**: Sparse Autoencoder trained for ≤ 20 epochs on the ROCStories pre‑training set (≈ 12 500 stories). Each epoch processes ~ 200 k tokens, fitting comfortably within 2 GB RAM.  
- **Baseline**: TinyLSTM quantized to 8‑bit (`torch.quantization.quantize_dynamic`) to stay < 1 GB.  
- **RSA**: Pairwise correlations for ≤ 12 500 conditions → O(N²) ≈ 156 M operations, executed with NumPy vectorization (< 2 min).  
- **Permutation Test**: Parallelized over 4 CPU cores using `joblib.Parallel`; 2 000 permutations typically complete in ≤ 1 h.  

### GPU Escape Hatch (not required)
If the SAE training unexpectedly exceeds CPU memory, the pipeline detects a `RuntimeError: CUDA out of memory` and re‑runs on a Kaggle free GPU with an 8‑bit quantized version of the SAE and a reduced story subset (first 2 000 stories). No synthetic CPU approximation is used.

## Decision / Rationale
- **Why Sparse Autoencoder?** Enforces biologically plausible sparsity (≤ 0.20) mirroring dentate‑gyrus pattern separation.  
- **Why Gating Module?** Models prefrontal executive control by selectively amplifying tokens that satisfy a coherence constraint (implemented as a learned mask).  
- **Why RSA?** Directly compares high‑dimensional representational geometry without requiring voxel‑wise alignment.  
- **Why CPU?** The free‑tier runner is the mandated execution environment; all components have been sized to respect its limits.  
- **Why Held‑out Test Set?** Guarantees a one‑to‑one mapping between model inputs and neural events, fulfilling FR‑001 and preserving internal validity.

---
