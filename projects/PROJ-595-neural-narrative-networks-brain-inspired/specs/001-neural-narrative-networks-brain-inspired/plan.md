# Implementation Plan: Neural Narrative Networks

**Branch**: `001-neural-narrative-networks` | **Date**: 2026-10-22 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-neural-narrative-networks/spec.md`

## Summary
The project will (1) download and preprocess an OpenNeuro fMRI dataset, extracting BOLD timecourses for left/right hippocampus and dorsolateral prefrontal cortex (DLPFC) ROIs.; (2) download the ROCStories corpus for pre‑training; (3) implement a brain‑inspired architecture comprising a Sparse Autoencoder (pattern separation) and a Prefrontal Gating Module (executive control); (4) generate ≥ 12 500 unique stories from both the brain‑inspired model and a quantized TinyBERT baseline while respecting a **≤ 2 GB RAM** budget on CPU; (5) compute Representational Similarity Analysis (RSA) matrices comparing model hidden states to human fMRI patterns, after PCA reduction (to 50 components) and Procrustes alignment; (6) perform a **fixed 10 000 permutation** test using a **max‑statistic across the three ROIs** to control family‑wise error; (7) conduct a **Monte‑Carlo power analysis (1 000 simulations)** that explicitly uses the actual **≈ 30 subjects** and **27 story events** from ds001495 (subject count now stated) to estimate power for detecting a medium effect size (Cohen’s d ≈ medium magnitude) and target ≥ 80 % power; (8) fit a linear mixed‑effects model to account for inter‑subject variability; (9) generate visualizations and a comprehensive `results_summary.csv`; (10) validate all outputs against JSON/YAML contracts. All steps run on the GitHub Actions free‑tier CPU runner; a GPU escape hatch is defined but not required.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0` (CPU), `datasets==2.19.0`, `nibabel==5.2.1`, `numpy`, `scipy`, `pandas`, `scikit-learn`, `matplotlib`, `seaborn`, `nltk`, `transformers==4.44.0`, `bitsandbytes==0.43.1` (8‑bit quantization), `statsmodels`, `pingouin`, `nilearn==0.10.4` (for atlas fallback)  
- **Storage**: Local filesystem under `data/` (raw / processed / analysis)  
- **Testing**: `pytest` (unit, integration, contract)  
- **Target Platform**: GitHub Actions free tier (Multiple CPU cores, ~7 GB RAM, ≤6 h)  
- **Constraints**: CPU‑only; peak RAM ≤ 2 GB for model generation; total RAM ≤ 7 GB; deterministic seeds; no GPU unless automatic off‑load triggers.  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | All scripts pin random seeds (`torch.manual_seed(42)`, `numpy.random.seed(42)`). `requirements.txt` version‑pins every dependency. |
| **II. Verified Accuracy** | Dataset URLs are taken exclusively from the verified list supplied in the spec. |
| **III. Data Hygiene** | Every download is checksummed (SHA‑256) and stored under `data/raw/`. Preprocessing writes new files under `data/processed/` without mutating raw files. |
| **IV. Single Source of Truth** | RSA matrices, permutation results, mixed‑effects summary, power estimate, visualizations, and `results_summary.csv` are generated once in `code/analysis/` and referenced directly by the final manuscript. |
| **V. Versioning Discipline** | All artifacts are recorded in `state/projects/PROJ-595-neural-narrative-networks-brain-inspired.yaml` with content hashes. |
| **VI. Neuro‑Biological Fidelity** | Implements a Sparse Autoencoder with ≤ 0.20 activation density (pattern separation) and a gating module that yields a StoryCoherence score ≥ 0.70. RSA directly compares model hidden states to ROI‑specific BOLD signals. |
| **VII. Computational Constraints** | Both models ≤ 5 M trainable parameters (SAE ≤ 1.5 M, TinyBERT ≈ 4.4 M). Data is streamed; chunked loading keeps RAM ≤ 2 GB during generation. |

## Construct‑Validity Rationale (addresses methodology‑5bd508e3)
- **Sparse Autoencoder (SAE)**: Sparse coding is a well‑established computational analogue of hippocampal pattern separation (e.g., Rolls & Treves, 1998). Enforcing an activation density ≤ 0.20 mimics the low‑activity, orthogonalized representations observed in dentate gyrus granule cells. This sparsity is measured as the fraction of hidden units with activation > 0 after the ReLU non‑linearity; the target ≤ 0.20 is justified by empirical neurophysiology showing ~15‑[deferred] active cells during encoding.
- **Prefrontal Gating Module**: The gating mechanism implements a selective attention mask whose output is evaluated by a **StoryCoherence** metric (cosine similarity to a coherence prototype derived from human‑rated story coherence scores). This mirrors prefrontal executive control that gates relevant information streams during narrative planning (Miller & Cohen, 2001). The ≥ 0.70 threshold is calibrated from prior work linking coherence metrics to dorsolateral prefrontal activation (see e.g., Huth et al., 2016). Both components are therefore grounded in established neuro‑computational theory.

## Project Structure
```text
specs/001-neural-narrative-networks/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── neural-data.schema.yaml
    ├── rsa-output.schema.yaml
    ├── rsa_schema.schema.yaml
    └── text-data.schema.yaml
```

## Tasks

### Phase 0 – Project Setup
| ID | Description | Dependencies | FR/SC |
|----|-------------|--------------|-------|
| **T001** | Create a `.gitignore` with standard patterns (including `data/raw/`, `data/processed/`, `venv/`, etc.). | – | — |
| **T002** | Ensure `code/__init__.py` exists for package importability. | – | — |

### Phase 1 – Data Ingestion & Preprocessing
| ID | Description | Dependencies | FR/SC |
|----|-------------|--------------|-------|
| **T010** | Download OpenNeuro ds001495 parquet via `datasets.load_dataset(..., streaming=True)`. | – | FR‑001 |
| **T011** | Download ROCStories parquet; convert to JSONL. | – | FR‑004 |
| **T012** | Verify checksums of raw files; abort with clear error if mismatch. | T010, T011 | — |
| **T014** | Extract left hippocampus ROI BOLD timecourses → `data/processed/neural/roi_left_hipp.npy`. | T010 | FR‑001 |
| **T015** | Extract right hippocampus ROI BOLD timecourses → `roi_right_hipp.npy`. | T010 | FR‑001 |
| **T016** | Extract DLPFC ROI BOLD timecourses → `roi_dlpfc.npy`; **fallback**: download Harvard‑Oxford atlas via `nilearn`, generate DLPFC mask from MNI coordinates (± 6 mm). Abort with `ROI definition failed` if both unavailable. | T010, T016‑FALLBACK | FR‑001 |
| **T016‑FALLBACK** | Download Harvard‑Oxford atlas (verified via nilearn) for DLPFC fallback. | – | FR‑001 |
| **T019** | Combine ROI matrices into subject‑wise 3‑D array `combined_neural.npy`. | T014‑T016 | FR‑001 |
| **T020** | Apply FIR deconvolution to obtain HRF‑aligned event‑wise averages per ROI. | T019 | FR‑001 |
| **T023** | Convert ROCStories parquet to `data/processed/text/rocstories_pretrain.jsonl`. | T011 | FR‑004 |
| **T023‑FILTER** | Remove any ROCStories entries whose `story_id` overlaps with the fMRI story transcripts (ensuring disjoint training/test sets). | T023, T024 | — |
| **T023‑META** | Write `data/processed/text/text_data_metadata.json` containing total_stories, sample_size, checksum, and `event_boundary_method="provided"` to satisfy `text-data.schema.yaml`. | T023 | — |
| **T024** | Extract story transcripts from OpenNeuro metadata, infer sentence boundaries with NLTK where absent, and save to `data/processed/text/fMRI_story_transcripts.jsonl`. | T010 | FR‑001 |
| **T025** | **Spec‑root cause; flagged for kickback** – OpenNeuro ds001495 provides only 27 distinct stories, insufficient for the original ≥ 100 requirement. An alternative open story‑based fMRI dataset (e.g., OpenNeuro ds002800) is needed but not currently verified. | T024 | FR‑004, SC‑005 |
| **T026** | Compute per‑event mean BOLD for each ROI using the extracted story list. | T020, T025 | FR‑001 |

### Phase 2 – Model Architecture Definition
| ID | Description | Dependencies | FR/SC |
|----|-------------|--------------|-------|
| **T050** | Define tensor shapes and buffers for the Sparse Autoencoder (SAE). | – | FR‑002 |
| **T050.1** | Implement SAE class with L1 sparsity regularizer; forward returns hidden activations. | T050 | FR‑002, SC‑001 |
| **T050.2** | Implement Prefrontal Gating Module (attention‑like mask) that outputs a StoryCoherence score. | – | FR‑003, SC‑007 |
| **T050.3** | Integrate gating output with SAE hidden state to produce final representation. | T050.1, T050.2 | FR‑003 |
| **T050.4** | Train SAE on ROCStories pre‑training corpus (`rocstories_pretrain.jsonl`) for ≤ 20 epochs, enforcing activation density ≤ 0.20. Log sparsity ratio after each epoch. | T023‑FILTER, T050.3 | FR‑002, SC‑001 |
| **T050.5** | If sparsity > 0.20, retry training with a new seed (up to 3 attempts); if still failing, abort with error **E003**. | T050.4 | FR‑002, SC‑001 |
| **T050.6** | Save the pre‑training hidden‑state vectors to `data/processed/neural/pretrain_sae_hidden.pt`. | T050.4 | FR‑010 |
| **T050‑UT‑SAE** | Unit test that loads `pretrain_sae_hidden.pt`, checks for load errors, and verifies sparsity ≤ 0.20. | T050.6 | SC‑010 |
| **T051** | Evaluate the gating module on a held‑out validation split of ROCStories; compute StoryCoherence score (e.g., cosine similarity to a reference coherence vector). Require score ≥ 0.70; abort with **E004** if not met. | T050.2, T023 | FR‑003, SC‑007 |
| **T060** | Define quantized TinyBERT baseline (approximately a few million parameters) using `bitsandbytes` 8‑bit quantization. | – | FR‑004, FR‑011 |
| **T060‑PRETRAIN** | Pre‑train TinyBERT on the **same** ROCStories pre‑training corpus (`rocstories_pretrain.jsonl`) using masked language modeling for ≤ 5 epochs. | T023‑FILTER | FR‑004 |
| **T060.1** | Verify baseline parameter count ≤ 5 M and that peak RAM during inference ≤ 2 GB. | T060 | — |

### Phase 3 – Story Generation (Test Set)
| ID | Description | Dependencies | FR/SC |
|----|-------------|--------------|-------|
| **T031** | Wire brain‑inspired pipeline (SAE + gating) into `generator.py` with CLI flag `--model brain_inspired`. | T050‑T051 | FR‑002, FR‑003 |
| **T036** | Run brain‑inspired generator on `fMRI_story_transcripts.jsonl` → `data/processed/brain_inspired_hidden.npy`; ensure ≥ 12 500 unique stories, sparsity ≤ 0.20, and StoryCoherence ≥ 0.70. | T031, T025 | FR‑004, SC‑001, SC‑005, SC‑007 |
| **T037‑BASELINE** | Run quantized TinyBERT baseline on the same test set → `data/processed/baseline_transformer_hidden.npy`; ensure ≥ 12 500 unique stories and RAM ≤ 2 GB. | T060‑PRETRAIN, T025 | FR‑004, SC‑002 |
| **T038** | Profile peak memory usage for both generation runs; log and assert ≤ 2 GB. | T036, T037‑BASELINE | SC‑002 |

### Phase 4 – RSA & Statistical Validation
| ID | Description | Dependencies | FR/SC |
|----|-------------|--------------|-------|
| **T042‑ALIGN** | Reduce model hidden states and neural ROI matrices to 50 principal components (PCA) and align them with Procrustes analysis before RSA. | T036, T037‑BASELINE, T026 | — |
| **T042** | Compute RSA matrices (Spearman primary, Pearson secondary) between each model’s aligned hidden states and each ROI’s neural RDM **per subject**; then average across subjects. Export CSVs per ROI and model. | T042‑ALIGN | FR‑005 |
| **T042‑META** | Write `rsa_output_metadata.json` containing `rsa_matrix` metadata (model_type, roi, similarity_metric, shape) to satisfy `rsa-output.schema.yaml`. | T042 | — |
| **T043** | Perform a **fixed 10 000** permutation test on the *difference* of RSA correlations (brain‑inspired – baseline) for each ROI. Use the **max‑statistic across the three ROIs** to control family‑wise error. No early‑stopping. | T042 | FR‑006, SC‑003 |
| **T044** | Conduct a linear mixed‑effects model (random intercepts for subjects) on RSA distances to account for inter‑subject variability; report mixed‑effects p‑values and AIC. | T042 | FR‑009 |
| **T045** | Monte‑Carlo power analysis (1 000 simulations) assuming a medium effect size (Cohen’s *d* ≈ 0.5) and using the actual **≈ 30 subjects** and **27 story events** from ds001495. Target ≥ 80 % power; record estimate in `results/power_estimate.csv`. | T042, T043 | FR‑008, SC‑008 |
| **T046** | Generate visualizations: (a) heatmaps of RSA matrices per ROI (brain‑inspired), (b) bar plot of RSA distances with 95 % confidence intervals and significance stars. | T042, T043 | FR‑007 |
| **T047** | Assemble `results_summary.csv` containing sparsity ratio, peak RAM, StoryCoherence score, RSA distances (Spearman & Pearson), mixed‑effects p‑values, permutation p‑values, power estimate, and story count. | T043, T044, T045, T046 | SC‑004, SC‑005, SC‑008, SC‑009 |

### Phase 5 – Verification & Reporting
| ID | Description | Dependencies | FR/SC |
|----|-------------|--------------|-------|
| **T050‑UT** | Unit tests for ROI extraction, SAE sparsity, gating coherence, baseline output shape, RSA utilities, mixed‑effects fitting, power analysis, and contract compliance. | All previous tasks | — |
| **T051** | Validate all output files against the JSON/YAML contracts in `contracts/`. | T047 | — |
| **T052** | Produce `manifest.json` listing dataset URLs, checksums, software versions, random seeds, and hardware environment. | T051 | — |

## Compute Feasibility
- **CPU‑First**: All training and inference steps are designed for CPU. The SAE (≤ 1.5 M params) and TinyBERT (≈ 4.4 M params, 8‑bit) comfortably fit within the 2 GB RAM cap when processing minibatches of ≤ 64 stories. Streaming of the OpenNeuro parquet avoids loading the full dataset into memory.
- **GPU Escape Hatch**: If any step raises a CUDA‑related error (unlikely on CPU), the runner will automatically re‑execute the same command on a Kaggle free GPU with `device="cuda"`.

## Decision / Rationale
- **Brain‑inspired architecture** provides a biologically plausible pattern‑separation mechanism (sparsity ≤ 0.20) and executive gating (StoryCoherence ≥ 0.70), directly mapping to hippocampal‑prefrontal interaction hypotheses (Constitution VI).  
- **Quantized TinyBERT** serves as the *standard transformer* baseline, pretrained on the identical ROCStories corpus, satisfying the baseline requirement while respecting the ≤ 5 M parameter and RAM constraints.  
- **RSA** after PCA/Procrustes offers a robust, geometry‑based comparison between model and neural representational spaces, aligning with neuro‑biological fidelity.  
- **Permutation testing with max‑statistic** controls family‑wise error under ROI dependence.  
- **Mixed‑effects modeling** and **Monte‑Carlo power analysis** ensure rigorous statistical inference accounting for subject variability.  

---



