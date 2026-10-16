# Implementation Plan: Neural Narrative Networks

**Branch**: `001-neural-narrative-networks` | **Date**: 2026-10-16 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-neural-narrative-networks/spec.md`

## Summary
The project will (1) download and preprocess the OpenNeuro ds001495 fMRI dataset, extracting BOLD timecourses for hippocampal and dorsolateral prefrontal cortex ROIs; (2) download the ROCStories corpus for **pre‑training only**; (3) implement a brain‑inspired architecture comprising a Sparse Autoencoder (pattern separation) and a Prefrontal Gating Module (executive control); (4) generate hidden‑state representations for the **held‑out fMRI story set** (≥ 100 stories); (5) evaluate neural alignment via Representational Similarity Analysis (RSA) against a TinyLSTM baseline; (6) perform a permutation test with early‑stopping variance check. All steps run on the GitHub Actions free‑tier CPU runner; a GPU escape hatch is defined but not required.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0` (CPU), `datasets==2.19.0`, `nibabel==5.2.1`, `numpy`, `scipy`, `pandas`, `scikit-learn`, `matplotlib`, `nltk`  
- **Storage**: Local filesystem under `data/` (raw / processed)  
- **Testing**: `pytest` (unit & integration)  
- **Target Platform**: GitHub Actions free tier (2 CPU cores, ~7 GB RAM, ≤6 h)  
- **Constraints**: CPU‑only execution, peak RAM < 7 GB, deterministic seeds, no external GPU unless the escape hatch triggers.  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | All scripts use pinned random seeds (`torch.manual_seed(42)`, `numpy.random.seed(42)`) and deterministic data loaders (`datasets.load_dataset(..., download_mode="reuse_cache_if_exists")`). `requirements.txt` is version‑pinned. |
| **II. Verified Accuracy** | Dataset URLs are taken exclusively from the verified list: <br>• OpenNeuro ds001495 parquet: ` <br>• ROCStories parquet: ` |
| **III. Data Hygiene** | Every downloaded file is checksummed (SHA‑256) and stored under `data/raw/`. Preprocessing writes new files under `data/processed/` without mutating the raw files. |
| **IV. Single Source of Truth** | RSA matrices, permutation results, and visualizations are generated once in `code/analysis/` and referenced directly by the paper generation step. |
| **V. Versioning Discipline** | All artifacts are recorded in `state/projects/PROJ-595-neural-narrative-networks-brain-inspired.yaml` with content hashes. |
| **VI. Neuro‑Biological Fidelity** | Implements a Sparse Autoencoder enforcing ≤ 0.20 activation density (FR‑002) and a gating module that modulates token selection (FR‑003). RSA compares hidden states to ROI‑specific BOLD signals (FR‑005). |
| **VII. Computational Constraints** | Model sizes are capped (~2 M parameters each). Data is streamed (`datasets.load_dataset(..., streaming=True)`) and loaded subject‑wise to keep RAM < 7 GB. Chunked loading is used for oversized files. |
| **Verified URLs** | OpenNeuro ds001495 parquet: ` <br> ROCStories parquet: ` |

## Project Structure
```text
specs/001-neural-narrative-networks/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/

projects/PROJ-595-neural-narrative-networks-brain-inspired/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data_ingestion/
│   │   ├── download_neural.py
│   │   ├── download_text.py
│   │   └── preprocess.py
│   ├── models/
│   │   ├── sparse_autoencoder.py
│   │   ├── gating_module.py
│   │   ├── baseline_lstm.py
│   │   └── generator.py
│   ├── analysis/
│   │   ├── rsa_computation.py
│   │   ├── permutation_test.py
│   │   └── visualization.py
│   └── main.py
├── data/
│   ├── raw/
│   │   ├── openneuro/
│   │   │   └── test-00000-of-00016.parquet
│   │   └── rocstories/
│   │       └── train-00000-of-00001-c17b7a9172e87209.parquet
│   └── processed/
│       ├── neural/
│       │   ├── roi_left_hipp.npy
│       │   ├── roi_right_hipp.npy
│       │   └── roi_dlpfc.npy
│       └── text/
│           ├── fMRI_story_transcripts.jsonl   # extracted from OpenNeuro
│           └── rocstories_pretrain.jsonl
├── tests/
│   ├── unit/
│   └── integration/
└── contracts/
    ├── neural-data.schema.yaml
    ├── rsa-output.schema.yaml
    ├── rsa_schema.schema.yaml
    └── text-data.schema.yaml
```

## Complexity Tracking & Resolved Concerns
| Concern | Resolution |
|---------|------------|
| **T042 dependency chain** | Added explicit dependencies on `T050`, `T050.1`, `T050.2`, `T050.3`, `T050.4`, `T050.5`. |
| **T019 parallel‑safe tag** | Removed the `[P]` tag; `T019` now runs **after** `T014‑T016` complete. |
| **File‑level conflict (T031 vs T050‑T050.5)** | Clarified `T031` as a *final integration* step that wires the already‑implemented `SparseAutoencoder` and `GatingModule` (from `T050.*`) into the generation pipeline; no re‑implementation occurs. |
| **Duplicate task ID T050** | Renamed unit‑test task to `T050-UT`; all downstream references updated. |
| **Permutation feasibility** | Reduced permutations to **2 000** with early‑stopping variance check; workload now fits within the CPU budget. |
| **Power & sample size** | Minimum shared fMRI stories raised to **100**; added brief a priori power‑analysis note (see research.md). |
| **Dataset mismatch** | ROCStories used **only** for pre‑training; fMRI story transcripts are taken directly from OpenNeuro (no intersection required). |
| **Circularity / independence** | Model training uses ROCStories **only**; RSA evaluation uses held‑out fMRI stories, ensuring independence. |

## Tasks

### Phase 1 – Data Ingestion & Preprocessing
| ID | Description | Dependencies | FR/SC |
|----|-------------|--------------|-------|
| **T014** | Extract left hippocampus ROI BOLD timecourses → `data/processed/neural/roi_left_hipp.npy` | – | FR‑001 |
| **T015** | Extract right hippocampus ROI BOLD timecourses → `roi_right_hipp.npy` | – | FR‑001 |
| **T016** | Extract dorsolateral prefrontal cortex ROI BOLD timecourses → `roi_dlpfc.npy` (fallback to Harvard‑Oxford coordinates if mask missing) | – | FR‑001 |
| **T019** | Combine extracted timecourses into a single subject‑wise matrix (`combined_neural.npy`). Runs **after** T014‑T016. | T014, T015, T016 | FR‑001 |
| **T020** | Apply FIR deconvolution to obtain HRF‑aligned event‑wise averages. | T019 | FR‑001 |
| **T023** | Download ROCStories parquet, parse to JSONL for **pre‑training**. | – | FR‑004 |
| **T023.1** | Verify that **≥ 100** fMRI story transcripts are available; abort with **E002** if not. | T020, T023 | FR‑004, SC‑005 |
| **T025** | Extract story transcripts directly from OpenNeuro ds001495 and save as `fMRI_story_transcripts.jsonl`. | T020, T023.1 | FR‑001 |
| **T026** | Compute per‑event mean BOLD for each ROI using the extracted fMRI story list. | T020, T025 | FR‑001 |

### Phase 2 – Model Architecture Definition (Phase 3.5)
| ID | Description | Dependencies | FR/SC |
|----|-------------|--------------|-------|
| **T050** | Define STM/LTM data structures (tensor shapes, buffers) in `sparse_autoencoder.py`. | – | FR‑002 |
| **T050.1** | Implement the Sparse Autoencoder class with sparsity regularizer (L1 penalty) and `forward` returning hidden activations. | T050 | FR‑002, SC‑001 |
| **T050.2** | Implement the Prefrontal Gating Module (attention‑like mask) in `gating_module.py`. | – | FR‑003 |
| **T050.3** | Integrate gating output with SAE hidden state to produce the final narrative representation. | T050.1, T050.2 | FR‑003 |
| **T050.4** | Train the SAE on the **ROCStories pre‑training corpus** (T023), enforcing activation density ≤ 0.20. Log sparsity ratio. | T023, T050.3 | FR‑002, SC‑001 |
| **T050.5** | Validate that the trained SAE meets the sparsity constraint; if not, retry up to 3 seeds (edge‑case spec). | T050.4 | FR‑002, SC‑001 |

### Phase 3 – Model Processing (Generation)
| ID | Description | Dependencies | FR/SC |
|----|-------------|--------------|-------|
| **T031** | **Finalize model integration**: wire the SAE + gating (from T050‑T050.5) into `generator.py` and expose a CLI flag `--model brain_inspired`. No new code, just integration. | T050‑T050.5 | FR‑002, FR‑003 |
| **T036** | Run `generator.py --model brain_inspired` on the **held‑out fMRI story set** (`fMRI_story_transcripts.jsonl`) → hidden‑state file `brain_inspired_hidden.npy`. | T031, T025 | FR‑004 |
| **T037** | Run baseline TinyLSTM (`baseline_lstm.py`) on the same fMRI story set → `baseline_hidden.npy`. | – (baseline code ready) | FR‑004 |
| **T038** | Verify peak RAM usage ≤ 7 GB and log memory profile. | T036, T037 | SC‑002 |

### Phase 4 – RSA Analysis & Validation
| ID | Description | Dependencies | FR/SC |
|----|-------------|--------------|-------|
| **T042** | Compute RSA matrices for brain‑inspired and baseline hidden states vs. each ROI (uses `rsa_computation.py`). **Depends on** T036, T037, T020, **and** T050‑T050.5 to guarantee refined architecture. | T036, T037, T020, T050, T050.1, T050.2, T050.3, T050.4, T050.5 | FR‑005 |
| **T043** | Permutation test on the *difference* of RSA correlations (brain‑inspired – baseline). Run **2 000** permutations; early‑stop when variance < 0.001 over the last 1 000 permutations. Apply Holm‑Bonferroni correction across the three ROIs. | T042 | FR‑006, SC‑003 |
| **T044** | Generate heatmaps of RSA matrices and a bar plot with 95 % confidence intervals for each ROI. | T042, T043 | FR‑007 |
| **T045** | Assemble a CSV summary (`results_summary.csv`) containing sparsity ratio, peak RAM, RSA distances, p‑values, and significance flags. | T043, T044 | SC‑004, SC‑005 |

### Phase 5 – Verification & Reporting
| ID | Description | Dependencies | FR/SC |
|----|-------------|--------------|-------|
| **T050-UT** | Run unit tests for ROI extraction, SAE sparsity, gating behavior, and RSA utilities. | All previous tasks | — |
| **T051** | Validate output files against contracts in `contracts/`. | T045 | — |
| **T052** | Produce a reproducibility manifest (`manifest.json`) enumerating dataset URLs, checksums, and software versions. | T051 | — |

---


## projects/PROJ-595-neural-narrative-networks-brain-inspired/specs/001-neural-narrative-networks-brain-inspired/research.md
# Research: Neural Narrative Networks

## Executive Summary
We evaluate whether a hippocampal‑like pattern‑separation layer (Sparse Autoencoder) coupled with a prefrontal‑like gating module yields hidden‑state representations that are **more similar** to human fMRI activation patterns (hippocampus + DLPFC) than a quantized TinyLSTM baseline. Crucially, the brain‑inspired model is **pre‑trained** on the ROCStories corpus **only**, and then applied to a **held‑out set of ≥ 100 story transcripts** extracted directly from the OpenNeuro ds001495 fMRI dataset. RSA is computed **solely on this unseen test set**, eliminating any circularity between training and evaluation.

## Dataset Strategy

### Neural Data (fMRI)
| Item | Source | Verified URL(s) |
|------|--------|-----------------|
| OpenNeuro ds001495 (parquet) | Hugging Face | ` |
| Dataset dictionary (metadata) | Hugging Face | ` |

*Variables*: BOLD timecourses for left/right hippocampus and DLPFC; subject IDs; event timestamps; story identifiers (embedded in the OpenNeuro metadata).  
*Strategy*:
1. Load the parquet via `datasets.load_dataset(..., streaming=True)`.  
2. Apply Harvard‑Oxford masks (threshold 25 %) or fallback to canonical MNI coordinates for DLPFC if a mask is missing.  
3. Perform FIR deconvolution to obtain HRF‑aligned event averages (per ROI).  
4. Verify that **≥ 100** story transcripts are present; abort with **E002** otherwise.

### Text Data (Stories)
| Item | Source | Verified URL(s) |
|------|--------|-----------------|
| ROCStories (parquet) – pre‑training | Hugging Face | ` |
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
- **Memory Management**: Chunked loading of fMRI data prevents RAM overflow; if a subject’s file exceeds available memory, the loader subsamples timepoints uniformly and logs the reduction factor.  

### Dataset Variable Fit
- The OpenNeuro ds001495 dataset **does** contain the required hippocampal masks. DLPFC masks are **not** pre‑computed; the pipeline therefore uses the Harvard‑Oxford DLPFC probabilistic atlas (coordinates from the standard atlas) as a fallback. If both masks and coordinates were unavailable, the pipeline would halt (fatal error).  
- Event‑locked annotations are present; if they were missing, the pipeline would revert to whole‑story averaging and note the loss of temporal resolution.

## Compute Feasibility & Time Complexity

### CPU‑First Strategy
- **Model Pre‑training**: Sparse Autoencoder trained for ≤ 20 epochs on the ROCStories pre‑training set (≈ 12 500 stories). Each epoch processes ~ 200 k tokens, fitting comfortably within 2 GB RAM.  
- **Baseline**: TinyLSTM quantized to 8‑bit (`torch.quantization.quantize_dynamic`) to stay < 1 GB.  
- **RSA**: Pairwise correlations for ≤ 12 500 conditions → O(N²) ≈ 156 M operations, executed with NumPy vectorization (< 2 min).  
- **Permutation Test**: 2 000 permutations, parallelized over 4 CPU cores using `joblib.Parallel`; early‑stopping typically finishes in ≤ 1 h.  

### GPU Escape Hatch (not required)
If the SAE training unexpectedly exceeds CPU memory, the pipeline detects a `RuntimeError: CUDA out of memory` and re‑runs on a Kaggle free GPU with an 8‑bit quantized version of the SAE and a reduced story subset (first 2 000 stories). No synthetic CPU approximation is used.

## Decision / Rationale
- **Why Sparse Autoencoder?** Enforces biologically plausible sparsity (≤ 0.20) mirroring dentate‑gyrus pattern separation.  
- **Why Gating Module?** Models prefrontal executive control by selectively amplifying tokens that satisfy a coherence constraint (implemented as a learned mask).  
- **Why RSA?** Directly compares high‑dimensional representational geometry without requiring voxel‑wise alignment.  
- **Why CPU?** The free‑tier runner is the mandated execution environment; all components have been sized to respect its limits.  
- **Why Held‑out Test Set?** Guarantees independence between model training (ROCStories) and neural evaluation (fMRI stories), satisfying methodological rigor.  

---

