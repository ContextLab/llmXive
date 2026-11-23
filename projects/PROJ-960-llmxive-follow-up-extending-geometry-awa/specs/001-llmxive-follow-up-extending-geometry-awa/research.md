# Research: Geometry-Aware Representation Denoising for Robust Multi-view 3D Reconstruction

**Feature**: `001-geometry-aware-denoising`  
**Date**: 2026-10-22  
**Status**: Phase 0 (Methodology & Hypothesis)

## Research Question
1. **Primary**: Can a lightweight, deterministic graph Laplacian filter that preserves low‑frequency structural signatures (Laplacian eigenmodes & curvature) recover **≥ 85 %** of the robustness gap closed by a diffusion‑based denoising baseline, while achieving **≥ 100×** CPU speedup?
2. **Secondary**: Which specific eigenmodes or curvature patterns correlate with low reconstruction error in clean data, and do these correlations persist under noise? Does causal removal of those eigenmodes degrade performance?

## Hypotheses
- **H1 (Structural)**: The top‑k Laplacian eigenmodes and curvature estimates encode the geometric robustness of GARD features; high‑frequency components correspond to noise.
- **H2 (Efficiency)**: Removing high‑frequency components via a deterministic filter yields Chamfer Distance within the gap‑closing bound defined in SC‑002 and reduces CPU inference time by at least two orders of magnitude.
- **H0 (Null)**: No eigenmode‑robustness correlation survives Bonferroni correction; in this case we still report the null result (FR‑010).

## Methodology

### 1. Data Strategy
| Dataset | Source (verified) | Purpose | Size / Access |
|---------|-------------------|---------|----------------|
| **Depth Anything 3 (DA3)** | <https://huggingface.co/datasets/carnival13/massive_5_lang_DA3_tokenized/resolve/main/data/train-00000-of-00001-7b1a3de50dd6a782.parquet> (train split) and <https://huggingface.co/datasets/carnival13/massive_val_DA3_tokenized/resolve/main/data/train-00000-of-00001-a1868e09683ad573.parquet> (val) | Multi‑view RGB‑D scenes, ground‑truth 3‑D meshes, synthetic degradation scripts | Programmatic download via `datasets.load_dataset(..., streaming=True)`; streamed in batches of 5 scenes to stay within RAM limits. |
| **GARD pretrained encoder/decoder** | <https://huggingface.co/datasets/suanlixianren/GardenSchool_test/resolve/main/EXAM.zip> | Frozen feature extractor and decoder for reconstruction | Direct zip download; ~100 MB total, loads on CPU (float32). |

**Preparation**
- Split DA3 into 20 training, 10 validation, **50 test** scenes (seed = 42).  
- For each scene, generate a *noisy* version using the GARD degradation script (deterministic noise seed).  
- Store raw DA3 files under `data/raw/da3_benchmark/` (checksummed).  
- Extract GARD features (Task 01) → `data/processed/feature_maps/`.  

### 2. Graph Construction (FR‑001, FR‑008, FR‑009)
- Build deterministic k‑NN graphs (k ∈ {5,10,15}) on flattened feature vectors.  
- Edge weight: `w_ij = exp(-d_ij^2 / σ^2)`, where `σ` = median pairwise distance (deterministic).  
- Detect disconnected components; apply Gaussian blur (σ=1.0) or increase k up to 20 until connectivity, logging the fallback (`fallback_applied` flag).  
- Scenes with < 3 views are either skipped (logged) or interpolated using GARD’s view‑interpolation routine if available.

### 3. Spectral Analysis (FR‑002, FR‑010, SC‑005)
- Compute normalized Laplacian `L = I - D^{-1/2} A D^{-1/2}`.  
- Eigendecompose L → top‑10 eigenvalues/eigenvectors (`eigsh` with `which='SM'`).  
- Estimate discrete Gaussian curvature per node via the cotangent formula on the feature graph.  
- **Normalized eigenmode energy** is defined as  
  `E_i = Σ_node (v_i·f)² / Σ_node ‖f‖²`, controlling for graph size and feature magnitude.  
- Correlate each eigenmode’s normalized energy with the scene’s Chamfer Distance (clean reconstruction).  
- Pearson *r* + Bonferroni correction (≈ 10 tests ⇒ α_corr = 0.005).  
- Record `is_significant` per eigenmode; if none meet the corrected threshold, trigger FR‑010 (null hypothesis flag).

#### 3b. Eigenmode Ablation Study (Causal Evidence)
- For each of the top‑k eigenmodes, zero‑out its coefficient in the feature representation, reconstruct the point cloud, and compute Chamfer Distance.  
- Compare the CD increase to the baseline (no ablation). Significant degradation indicates a causal role of that eigenmode in robustness.

### 4. Deterministic Laplacian Filter (FR‑003, FR‑007)
- Parameterize filter by cutoff λ_c (selected eigenvalue) and decay α.  
- For a feature vector `f`:  
  1. Project onto eigenbasis: `c = V^T f`.  
  2. Apply damping: `c_i' = c_i` if `λ_i < λ_c`; else `c_i' = c_i * exp(-α (λ_i - λ_c))`.  
  3. Reconstruct: `f' = V c'`.  
- Optimize (λ_c, α) on the 10‑scene validation set (grid search).  
- Sensitivity sweep over k ∈ {5,10,15} (FR‑007) records CD & MSE per k.

### 5. Reconstruction & Metrics (FR‑004, FR‑005, FR‑006, SC‑001‑004)
- Pass filtered features through the frozen GARD decoder → point cloud.  
- Compute **Chamfer Distance** (exact formulation) and **F‑score** (threshold = 0.01).  
- Measure wall‑clock inference time and peak RSS memory on a single CPU core (using `time` and `psutil`).  
- Run the same pipeline for the diffusion baseline (GPU off‑load) on the **full 50‑scene test set** and record latency & accuracy.  
- Perform **Wilcoxon signed‑rank test** (two‑tailed, α = 0.05) on paired CD values across the 50 test scenes.  
- **Power analysis**: assuming a medium effect size (d≈0.5), 50 paired samples give > 80 % power at α = 0.05 (validated with `statsmodels.stats.power`).

### 6. Success‑Criteria Mapping (re‑stated)
| SC | Measurement | Target |
|----|-------------|--------|
| **SC‑001** | CD(det) < CD(noisy) | Verified per scene |
| **SC‑002** | Gap‑closing: `CD_det ≤ CD_noisy - 0.85 × (CD_noisy − CD_diffusion)` | ≥ 85 % of diffusion robustness recovered |
| **SC‑003** | Wilcoxon p < 0.05 (power‑analysis justified) | Significant difference (or equivalence) confirmed |
| **SC‑004** | CV(k) < 0.1 for CD & MSE across k ∈ {5,10,15} | Demonstrates robustness to hyper‑parameter choice |
| **SC‑005** | Pearson r with Bonferroni‑corrected p < 0.005 for any eigenmode (or null result) | Identifies structural signatures; null acceptable |

### 7. Compute Feasibility
- **CPU‑first**: All stages except diffusion baseline run on the CI runner; Peak RAM ≈ several GB per batch.  
- **GPU escape hatch**: Diffusion baseline executed on a free Kaggle GPU (8‑bit quantized, ≤ 200 scenes). The CI job automatically re‑runs the diffusion script with `device="cuda"`; no CPU approximation is fabricated.

### 8. Edge‑Case Protocols
| Situation | Action |
|-----------|--------|
| Disconnected graph | Apply Gaussian blur, then increase k; set `fallback_applied = true`. |
| Incomplete view set | Skip scene (log) or invoke GARD view‑interpolation if present. |
| No significant eigenmode correlation | Record null result, flag FR‑010, continue with data‑driven filter tuning. |
| Ablation shows no effect | Document as evidence that the eigenmode is not causal; still report overall filter performance. |

### 9. Reproducibility & Versioning
- Random seeds: `np.random.seed(42); torch.manual_seed(42)`.  
- All scripts are deterministic given identical inputs.  
- `requirements.txt` pins exact library versions.  
- Checksums for raw DA3 parquet files and GARD zip stored in `data/metadata/checksums.yaml`.  
- Every derived artifact includes a provenance entry in `data/metadata/derivation_log.txt`.

---

