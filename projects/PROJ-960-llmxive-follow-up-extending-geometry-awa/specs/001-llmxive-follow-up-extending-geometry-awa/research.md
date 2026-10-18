# Research: Geometry-Aware Representation Denoising for Robust Multi-view 3D Reconstruction

**Feature**: `001-geometry-aware-denoising`  
**Date**: 2026-09-20  
**Status**: Phase 0 (Methodology & Hypothesis)

## Research Question

**Primary**: Can a lightweight, deterministic graph Laplacian filter that preserves static geometric structural properties (Laplacian eigenmodes, curvature constraints) recover ≥85% of the robustness achieved by expensive diffusion-based denoising, while achieving ≥100× speedup on CPU hardware?

**Secondary**: Which specific structural signatures (eigenmodes, curvature patterns) in the GARD feature manifold correlate with robustness in clean data, and do these correlations persist under noise corruption?

## Hypothesis

The GARD encoder's feature maps encode robust geometric structure that can be isolated and preserved through deterministic spectral filtering. Specifically:

1. **Structural Hypothesis**: The top-k Laplacian eigenmodes and curvature estimates of the k-NN feature graph are sufficient to characterize robustness; noise manifests as high-frequency spectral content and local curvature anomalies.
2. **Efficiency Hypothesis**: A deterministic filter that dampens high-frequency components while preserving low-frequency (robust) modes will recover most of the diffusion baseline's accuracy with orders-of-magnitude lower latency.
3. **Null Case**: If spectral analysis reveals no significant correlation between any eigenmode and robustness (Section 3.2), the hypothesis is unsupported; the null result is recorded and the study pivots to post-hoc analysis of why structure alone is insufficient.

## Methodology

### 1. Data Strategy

#### Dataset Selection

| Dataset | Source | Purpose | Size | Access | Rationale |
|---------|--------|---------|------|--------|-----------|
| **Depth Anything 3 (DA3)** | [HuggingFace (carnival13)](https://huggingface.co/datasets/carnival13/massive_5_lang_DA3_tokenized) | Multi-view 3D scenes, ground-truth reconstructions, noise-corruption framework | ~50 test scenes (subset selected for feasibility) | Public, programmatic download via `datasets.load_dataset()` | DA3 is the benchmark used in GARD paper; provides clean scenes + synthetic noise injection via GARD's degradation scripts |
| **GARD Pretrained Models** | [HuggingFace (suanlixianren)](https://huggingface.co/datasets/suanlixianren/GardenSchool_test) | Frozen GARD encoder/decoder for feature extraction and reconstruction | Encoder: ~50 MB, Decoder: ~50 MB | Public, direct download | Official GARD checkpoint; ensures reproducibility and fair comparison with diffusion baseline |

**Data Feasibility**: DA3 is verified as a public, directly-downloadable dataset via HuggingFace `datasets` library with streaming support. GARD models are publicly available. Both fit within the ~7 GB RAM and ~14 GB disk budget when processed in batches of 5–10 scenes.

**Null Case**: If DA3 becomes unavailable or GARD models cannot be loaded on CPU, the study cannot proceed; no synthetic substitute is acceptable (per Constitution Principle III).

#### Data Preparation

1. **Feature Extraction** (Task 00):
   - Load DA3 scenes in batches (5 scenes/batch to fit ~7 GB RAM).
   - Pass clean scenes through frozen GARD encoder → extract feature maps (shape: batch × views × channels × spatial_dims).
   - Save feature maps as numpy arrays (one file per scene).
   - Repeat for degraded scenes (DA3 provides synthetic noise injection; if not available, use GARD's degradation scripts).

2. **Train/Validation/Test Split**:
   - 50 scenes total: 20 training (parameter optimization), 10 validation (filter tuning), 20 test (final evaluation).
   - Fixed random seed (42) for reproducibility.

3. **Intermediate Storage**:
   - All feature maps checksummed and stored in `data/processed/feature_maps/`.
   - Lineage recorded in `data/metadata/derivation_log.txt`: "feature_maps/scene_001_clean.npy ← DA3 scene 001 + GARD encoder (commit SHA: [hash])".

### 2. Core Methodology

#### 2.1 Graph Construction (FR-001)

**Deterministic k-NN Graph**:

- For each scene's feature maps (across all views), flatten spatial dimensions → N feature vectors (N ≈ 1000–5000 depending on resolution).
- Compute pairwise Euclidean distances in feature space.
- For each node, select k nearest neighbors (k ∈ {5, 10, 15}; tested in sensitivity analysis, SC-004).
- Edge weights: $w_{ij} = \exp(-d_{ij}^2 / \sigma^2)$, where $\sigma$ is the median pairwise distance (scale-invariant, deterministic).
- **No stochasticity**: Same graph constructed on every run for the same feature maps (Constitution Principle VI).
- **Handling disconnected graphs** (FR-008): If the graph is disconnected, apply a local smoothing kernel (Gaussian blur) to the feature maps before graph construction, or fall back to k-NN with k increased to ensure connectivity. Document the fallback in the report.

**Output**: Adjacency matrix (sparse, CSR format) + node features (feature vectors).

#### 2.2 Spectral Analysis (FR-002)

**Laplacian Eigendecomposition**:

- Compute graph Laplacian: $L = D - A$, where D is the degree matrix and A is the adjacency matrix.
- Eigendecompose L → eigenvalues $\lambda_1 \leq \lambda_2 \leq \ldots \leq \lambda_N$ and eigenvectors $v_1, v_2, \ldots, v_N$.
- Extract top-k eigenmodes (k = 10 for analysis; the "robust modes" hypothesis).
- Compute curvature estimates: For each node, estimate discrete Gaussian curvature from the local neighborhood (using the discrete Laplacian operator on the feature graph).

**Correlation Analysis** (FR-002, US-2):

- For each of the 20 training scenes, compute Chamfer Distance (CD) of the raw noisy reconstruction against ground truth.
- For each eigenmode $v_i$, compute Pearson correlation coefficient between the eigenmode's energy (sum of squared components) and the scene's CD.
- Apply Bonferroni correction: threshold = 0.05 / 10 = 0.005 (for ~10 eigenmodes).
- **Null Case** (FR-010): If no eigenmode meets the corrected threshold, flag the hypothesis as unsupported and record this in the final report. The study continues to Phase 2 (filter optimization) but acknowledges the lack of spectral justification.

**Output**: Eigenvalues, eigenvectors, curvature estimates (numpy arrays); correlation table (CSV with p-values, Bonferroni-corrected).

#### 2.3 Deterministic Graph Laplacian Filter (FR-003)

**Filter Design**:

- Parameterized by a frequency cutoff $\lambda_c$ (or equivalently, the number of "robust" modes to preserve).
- For a given feature vector $f$, project onto the eigenbasis: $\hat{f} = V^T f$, where V is the matrix of eigenvectors.
- Apply a frequency-dependent damping function: $\hat{f}_{\text{filtered}} = D(\lambda) \odot \hat{f}$, where $D(\lambda_i) = 1$ if $\lambda_i < \lambda_c$ else $\exp(-\alpha(\lambda_i - \lambda_c))$ (smooth exponential decay for high frequencies).
- Reconstruct: $f_{\text{filtered}} = V \hat{f}_{\text{filtered}}$.
- **Optimization** (Task 03): On the 10 validation scenes, sweep $\lambda_c$ and $\alpha$ to minimize Chamfer Distance; record the optimal parameters.
- **Deterministic**: Same parameters applied to all test scenes; no per-scene adaptation (Constitution Principle VI).

**Output**: Filtered feature maps (same shape as input); parameter log (optimal $\lambda_c$, $\alpha$).

#### 2.4 Reconstruction & Metrics (FR-004, FR-005, FR-006)

**Reconstruction**:

- Pass filtered feature maps through the frozen GARD decoder → 3D point clouds.
- Compute Chamfer Distance (CD) against ground truth: $\text{CD} = \frac{1}{|P|} \sum_{p \in P} \min_{g \in G} ||p - g||_2 + \frac{1}{|G|} \sum_{g \in G} \min_{p \in P} ||p - g||_2$.
- Compute F-score: $F = 2 \cdot \frac{\text{precision} \times \text{recall}}{\text{precision} + \text{recall}}$ at a fixed distance threshold (e.g., 0.01 units).

**Latency & Memory** (FR-005):

- Measure wall-clock time for feature extraction, graph construction, filtering, and reconstruction on a single CPU core.
- Measure peak RSS memory during each phase.
- Record for both deterministic filter and diffusion baseline (if available).
- **Target**: Deterministic filter ≤1% of diffusion baseline latency (SC-003).

**Statistical Testing** (FR-006):

- On the 20 test scenes, compute reconstruction errors (CD) for both deterministic filter and diffusion baseline.
- Perform Wilcoxon signed-rank test (non-parametric, two-tailed, α=0.05) to test the null hypothesis that the two methods produce the same error distribution.
- Report test statistic, p-value, and effect size (rank-biserial correlation).
- **Interpretation**: If p < 0.05, the methods differ significantly; if p ≥ 0.05, no significant difference detected (but this does not imply equivalence).

#### 2.5 Sensitivity Analysis (FR-007, SC-004)

**Parameter Sweep**:

- Vary k ∈ {5, 10, 15} (number of nearest neighbors).
- For each k, retrain the filter on the validation set and evaluate on the test set.
- Report Chamfer Distance and MSE for each k; compute the coefficient of variation (CV = std / mean) to quantify robustness to the parameter choice.
- **Acceptance**: CV < 0.1 (results are not sensitive artifacts of a single threshold).

**Output**: Sensitivity table (k, CD_mean, CD_std, MSE_mean, MSE_std, CV).

### 3. Handling Edge Cases

#### 3.1 Disconnected Graphs (FR-008)

**Detection**: Check if the graph has >1 connected component after k-NN construction.

**Fallback Strategy**:
1. If disconnected, apply a Gaussian blur to the feature maps (kernel size = 3, sigma = 1.0) to smooth local variations.
2. Reconstruct the k-NN graph from the blurred features.
3. If still disconnected, increase k to the smallest value that ensures a single connected component (up to k=20).
4. Document the fallback in the report: "Scene XXX required fallback strategy due to disconnected graph at k=10; re-ran with k=15."

#### 3.2 Incomplete Multi-view Sequences (FR-009)

**Detection**: Check if a scene has fewer views than expected (e.g., <3 views for stereo reconstruction).

**Fallback Strategy**:
1. Skip the scene and record it in the report: "Scene XXX skipped: insufficient views (N=2 < 3)."
2. If view-interpolation is available in the GARD repo, apply it to synthesize missing views.
3. Continue with the interpolated sequence.
4. Report the number of scenes skipped and the reason.

**Impact**: If >10% of scenes are skipped, the study is underpowered; flag this as a limitation in the final report.

#### 3.3 Null Spectral Correlation (FR-010, SC-005)

**Scenario**: Spectral analysis reveals no eigenmode–robustness correlation meeting the Bonferroni-corrected threshold (p < 0.005).

**Action**:
1. Flag the hypothesis as unsupported: "Spectral analysis found no significant correlation between any eigenmode and reconstruction robustness (all p > 0.005 after Bonferroni correction)."
2. Continue to Phase 2 (filter optimization) using data-driven parameter tuning instead of spectral guidance.
3. In the final report, include a post-hoc analysis: Do the optimized filter parameters align with low-frequency preservation? If not, discuss why structural properties alone may be insufficient.
4. **This is NOT a failure**: Null results are scientifically valid and expected outcomes per the Constitution.

### 4. Success Criteria Mapping

| SC | Measurement | Method | Reference |
|----|-------------|--------|-----------|
| **SC-001** | CD(deterministic filter) < CD(raw noisy input) on test set | Chamfer Distance computation | Held-out test scenes (ground truth) |
| **SC-002** | CD(det) ≤ CD(noisy) + 0.15 × (CD(diffusion) − CD(noisy)) | Interpolation-based criterion | Test scenes: noisy baseline, diffusion baseline, deterministic filter |
| **SC-003** | Wilcoxon signed-rank test, two-tailed, α=0.05 | Non-parametric hypothesis test | 20 test scenes, paired error measurements |
| **SC-004** | CV(k ∈ {5, 10, 15}) < 0.1 for CD and MSE | Sensitivity sweep + coefficient of variation | Validation set, three k values |
| **SC-005** | Pearson r with Bonferroni correction (p < 0.005) for eigenmode–CD correlation | Correlation + multiple-comparison correction | 20 training scenes, ~10 eigenmodes |

### 5. Compute Feasibility

**CPU-Centric**: All methods run on GitHub Actions free-tier (2 CPU, ~7 GB RAM, ~14 GB disk).

- **Feature extraction**: ~5 min/scene (GARD encoder in float32, CPU-only PyTorch wheels).
- **Graph construction**: ~1 min/scene (sparse matrix operations, networkx).
- **Spectral analysis**: ~2 min/scene (scipy eigendecomposition, small graphs).
- **Filtering**: <1 sec/scene (matrix multiplication).
- **Total for 50 scenes**: ~8 hours (within 6-hour limit if parallelized by batch; otherwise, use a subset of 20 scenes for demonstration).

**If timeout occurs**: Reduce test set to 20 scenes (instead of 50); report the power limitation explicitly.

**GPU Escape Hatch**: Diffusion baseline may require GPU if not available as a pre-computed reference. If needed, plan to offload to Kaggle (1 free GPU, ~16 GB VRAM): run diffusion on a 10-scene subset in 8-bit quantization, compute baseline metrics, and scale results via extrapolation.

### 6. Data Availability

- **DA3**: Verified public dataset via HuggingFace; programmatic download supported.
- **GARD Models**: Verified public checkpoints via HuggingFace; direct download.
- **Diffusion Baseline**: If available as a pre-computed reference in the GARD repo, use it directly. If not, the baseline must be computed (GPU escape hatch above).

**No gated data**: All inputs are open-source; no credentials, registrations, or data-use agreements required.

---
