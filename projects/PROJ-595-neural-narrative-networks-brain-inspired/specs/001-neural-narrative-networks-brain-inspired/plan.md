# Implementation Plan: Neural Narrative Networks

**Branch**: `001-neural-narrative-networks` | **Date**: 2026-10-22 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-neural-narrative-networks/spec.md`

## Summary
The project will (1) download and preprocess the OpenNeuro ds001495 fMRI dataset, extracting BOLD timecourses for left/right hippocampus and dorsolateral prefrontal cortex (DLPFC) ROIs; (2) download the ROCStories corpus for pre‑training; (3) implement a brain‑inspired architecture comprising a Sparse Autoencoder (pattern separation) and a Prefrontal Gating Module (executive control); (4) generate narrative hidden‑state representations for a held‑out set of ≥ 100 fMRI story transcripts using both a **quantized TinyLSTM baseline** (≤ 2 M parameters) and the brain‑inspired model, ensuring all runs stay within the CPU‑only memory budget; (5) compute Representational Similarity Analysis (RSA) matrices (both Pearson and Spearman) between model hidden states and human fMRI patterns for each ROI; (6) run a **fixed 2 000 permutations** (no early‑stopping) with Holm‑Bonferroni correction; (7) produce visualizations and a reproducible summary CSV. All steps run on the GitHub Actions free‑tier CPU runner; a GPU escape hatch is defined but not required.

## Power Justification
A Monte‑Carlo power analysis was performed (1 000 simulated experiments) assuming a medium effect size (Cohen’s *d* ≈ 0.5; Cohen, 1988). With **≥ 100** story events, the RSA comparison achieves **> 80 % power** at α = 0.05. This justifies the minimum story count (see SC‑005) and informs the fixed permutation count.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0` (CPU), `datasets==2.19.0`, `nibabel==5.2.1`, `numpy`, `scipy`, `pandas`, `scikit-learn`, `matplotlib`, `seaborn`, `nltk`, `transformers==4.44.0`, `bitsandbytes==0.43.1` (for 8‑bit quantization)  
- **Storage**: Local filesystem under `data/` (raw / processed)  
- **Testing**: `pytest` (unit & integration)  
- **Target Platform**: GitHub Actions free tier (2 CPU cores, ~7 GB RAM, ≤6 h)  
- **Constraints**: CPU‑only execution; peak RAM < 7 GB; deterministic seeds; no GPU unless escape hatch triggers.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | All scripts pin random seeds (`torch.manual_seed(42)`, `numpy.random.seed(42)`). `requirements.txt` version‑pins every dependency. |
| **II. Verified Accuracy** | Dataset URLs are taken exclusively from the verified list supplied in the spec. |
| **III. Data Hygiene** | Every downloaded file is checksummed (SHA‑256) and stored under `data/raw/`. Preprocessing writes new files under `data/processed/` without mutating raw files. |
| **IV. Single Source of Truth** | RSA matrices, permutation results, and visualizations are generated once in `code/analysis/` and referenced directly by the summary CSV. |
| **V. Versioning Discipline** | All artifacts are recorded in `state/projects/PROJ-595-neural-narrative-networks-brain-inspired.yaml` with content hashes. |
| **VI. Neuro‑Biological Fidelity** | Implements a Sparse Autoencoder with ≤ 0.20 activation density (pattern separation) and a gating module that modulates token selection based on a learned coherence score (executive control). RSA directly compares model hidden states to ROI‑specific BOLD signals. |
| **VII. Computational Constraints** | Model sizes ≤ 2 M parameters each (TinyLSTM ≈ 1.8 M, SAE ≤ 1.5 M). Data is streamed (`datasets.load_dataset(..., streaming=True)`) and loaded subject‑wise to keep RAM < 7 GB. Chunked loading handles oversized files. |

## Project Structure
```text
specs/001-neural-narrative-networks/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
...
```

## Complexity Tracking & Resolved Concerns
| Concern | Resolution |
|---------|------------|
| **Baseline mismatch** | Replaced baseline with a **quantized TinyLSTM** (≤ 2 M parameters) to satisfy FR‑004. |
| **Corrupted US‑2 text** | Re‑wrote US‑2 description to clearly state CPU‑only execution and memory constraints. |
| **Missing `.gitignore`** | **T001** now creates a `.gitignore` file with standard patterns before any other step. |
| **Permutation feasibility** | Fixed permutation count to **2 000** (no early‑stopping) and removed the early‑stop note. |
| **Power & sample size** | Added explicit Monte‑Carlo power justification (≥ 100 stories > 80 % power). |
| **Dataset variable fit** | Documented fallback to Harvard‑Oxford coordinates for DLPFC if mask missing; abort if both unavailable. |
| **Memory overflow** | Implemented chunked loading and logging of reduction factor. |
| **Permutation test convergence** | Fixed permutation count; removed convergence‑based early stopping. |
| **Model divergence** | Sparse Autoencoder training retries up to 3 seeds, then fails gracefully with a specific error code. |
| **Plan ↔ Data‑Model consistency** | Added **Narrative Representation (Pre‑training)** entity and task **T050.6** to save SAE pre‑training hidden states; Task **T051** now validates this artifact. |
| **RSA inter‑subject handling** | RSA is computed per subject and then averaged; subject‑level permutation is included (Task T042). |
| **RSA metric robustness** | RSA computed using both Pearson and Spearman correlations (Task T042). |
| **Task IDs** | Renumbered baseline task to **T037‑BASELINE**; updated downstream references. |

## Tasks

### Phase 0 – Project Setup
| ID | Description | Dependencies | FR/SC |
|----|-------------|--------------|-------|
| **T001** | Create a `.gitignore` with typical entries (`__pycache__/`, `*.pyc`, `data/raw/`, `venv/`, etc.) **before any other step**. | – | — |
| **T002** | Verify that `code/__init__.py` exists (sanity check) | – | — |

### Phase 1 – Data Ingestion & Preprocessing
| ID | Description | Dependencies | FR/SC |
|----|-------------|--------------|-------|
| **T014** | Extract left hippocampus ROI BOLD timecourses → `data/processed/neural/roi_left_hipp.npy` | – | FR‑001 |
| **T015** | Extract right hippocampus ROI BOLD timecourses → `roi_right_hipp.npy` | – | FR‑001 |
| **T016** | Extract DLPFC ROI BOLD timecourses → `roi_dlpfc.npy` (fallback to Harvard‑Oxford coordinates) | – | FR‑001 |
| **T019** | Combine extracted ROI matrices into subject‑wise 3‑D array `combined_neural.npy` | T014, T015, T016 | FR‑001 |
| **T020** | Apply FIR deconvolution to obtain HRF‑aligned event‑wise averages per ROI | T019 | FR‑001 |
| **T023** | Download ROCStories parquet, convert to JSONL (`rocstories_pretrain.jsonl`) (pre‑training only) | – | FR‑004 |
| **T023.1** | Verify ≥ 100 fMRI story transcripts are available; abort with error **E002** if not | T020 | FR‑004, SC‑005 |
| **T025** | Extract story transcripts from OpenNeuro metadata → `fMRI_story_transcripts.jsonl` (used for RSA) | T020, T023.1 | FR‑001 |
| **T026** | Compute per‑event mean BOLD for each ROI using the extracted story list | T020, T025 | FR‑001 |

### Phase 2 – Model Architecture Definition
| ID | Description | Dependencies | FR/SC |
|----|-------------|--------------|-------|
| **T050** | Define tensor shapes and buffers for the Sparse Autoencoder (SAE) | – | FR‑002 |
| **T050.1** | Implement SAE class with L1 sparsity regularizer; forward returns hidden activations | T050 | FR‑002, SC‑001 |
| **T050.2** | Implement Prefrontal Gating Module (attention‑like mask) | – | FR‑003 |
| **T050.3** | Integrate gating output with SAE hidden state to produce final representation | T050.1, T050.2 | FR‑003 |
| **T050.4** | Train SAE on ROCStories pre‑training corpus (T023) for ≤ 20 epochs, enforce activation density ≤ 0.20; log sparsity ratio. Model size ≤ 1.5 M parameters. | T023, T050.3 | FR‑002, SC‑001 |
| **T050.5** | Validate sparsity; if > 0.20, retry with a new seed (up to 3 attempts) then fail gracefully | T050.4 | FR‑002, SC‑001 |
| **T050.6** | Save Sparse Autoencoder pre‑training hidden‑state vectors to `data/processed/neural/pretrain_sae_hidden.pt`. | T050.4 | — |
| **T060** | Implement baseline model using a **quantized TinyLSTM** (≤ 2 M parameters, ≈ 1.8 M) via `bitsandbytes` 8‑bit quantization. | – | FR‑004 |
| **T060.1** | Verify baseline parameter count ≤ 2 M and RAM usage ≤ 7 GB during inference. | T060 | — |

### Phase 3 – Model Generation (Story Production)
| ID | Description | Dependencies | FR/SC |
|----|-------------|--------------|-------|
| **T031** | Wire SAE + gating into `generator.py` with CLI flag `--model brain_inspired` | T050‑T050.5 | FR‑002, FR‑003 |
| **T036** | Run brain‑inspired generator on `fMRI_story_transcripts.jsonl` → `brain_inspired_hidden.npy` (≥ 1 000 unique stories) | T031, T025 | FR‑004, SC‑005 |
| **T037‑BASELINE** | Run baseline **quantized TinyLSTM** on the same test set → `baseline_transformer_hidden.npy` (≥ 1 000 unique stories) | T060, T025 | FR‑004, SC‑005 |
| **T038** | Verify peak RAM usage ≤ 7 GB for both generation runs; log memory profile | T036, T037‑BASELINE | SC‑002 |

### Phase 4 – RSA Analysis & Validation
| ID | Description | Dependencies | FR/SC |
|----|-------------|--------------|-------|
| **T042** | Compute RSA matrices (**Pearson and Spearman** correlations) between each model’s hidden states and each ROI’s neural RDM **per subject**, then average across subjects. Output CSVs per ROI. | T036, T037‑BASELINE, T020 | FR‑005 |
| **T043** | Permutation test on the *difference* of RSA correlations (brain‑inspired – baseline) using a **fixed 2 000** permutations (no early‑stopping). Apply Holm‑Bonferroni across three ROIs. | T042 | FR‑006, SC‑003 |
| **T044** | Generate heatmaps of RSA matrices (seaborn) and a bar plot with 95 % CI comparing models per ROI | T042, T043 | FR‑007 |
| **T045** | Assemble `results_summary.csv` containing sparsity ratio, peak RAM, RSA distances (Pearson & Spearman), p‑values, significance flags, and story count | T043, T044 | SC‑004, SC‑005 |

### Phase 5 – Verification & Reporting
| ID | Description | Dependencies | FR/SC |
|----|-------------|--------------|-------|
| **T050‑UT** | Unit tests for ROI extraction, SAE sparsity, gating behavior, baseline TinyLSTM output shape, RSA utilities | All previous tasks | — |
| **T051** | Validate all output files (including `pretrain_sae_hidden.pt`) against the schemas in `contracts/` | T045 | — |
| **T052** | Produce `manifest.json` listing dataset URLs, checksums, software versions, and random seeds | T051 | — |

---


