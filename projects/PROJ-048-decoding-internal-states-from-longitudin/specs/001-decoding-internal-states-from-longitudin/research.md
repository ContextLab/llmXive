# Research: Decoding Internal States from Longitudinal Calcium Imaging Data

## 1. Problem Statement & Hypothesis
**Hypothesis**: Longitudinal calcium imaging data contains latent neural states (latent components) that are temporally structured and correlate significantly with external behavioral metrics (e.g., running speed, stimulus onset).
**Method**: Extract these states using Non-negative Matrix Factorization (NMF) with temporal regularization enforced during factorization, then validate via permutation-tested Spearman correlation on a held-out dataset.

## 2. Dataset Strategy

### Verified Sources
The following datasets are available and verified for this project. **Note**: The specific "Allen Brain Atlas Visual Coding" subset mentioned in the spec must be mapped to one of these verified sources or a gap must be reported.

| Dataset Name | Verified URL | Relevance to Spec | Status |
|:--- |:--- |:--- |:--- |
| **NMFS-OSI Benthic Cover** | ` | *Not a match.* Contains benthic cover, not neural imaging. | **Incompatible** |
| **Chaymaa ROI Donut** | ` | *Partial Match.* Contains ROI data, but lacks behavioral metadata. | **Incompatible (No Behavior)** |
| **Chaymaa ROI Counters** | ` | *Partial Match.* ROI counters, likely not raw fluorescence traces. | **Incompatible** |
| **Dragos RoITD** | ` | *Partial Match.* ROI data, but format (CSV) and content (cleaned) may lack raw traces. | **Incompatible** |
| **NMFS NMF Data** | ` | *Not a match.* Irrelevant domain. | **Incompatible** |

### Gap Analysis & Decision
**Critical Gap**: The "Verified datasets" block **does not contain** a verified URL for the "Allen Brain Atlas Visual Coding" dataset subset required by **FR-001**.
* **Impact**: The spec assumes a specific dataset exists and is accessible. The verified list contains only benthic cover and generic ROI counters.
* **Decision**:
 1. The implementation **MUST** attempt to download the Allen dataset via a standard public API (e.g., `requests` to the Allen Brain Atlas API) if it is publicly accessible without authentication, as per the "Assumptions" in the spec.
 2. **Blocking Condition**: If the Allen dataset cannot be reached or requires complex auth, the pipeline **MUST HALT** immediately.
 3. **No Fallback Permitted**: The fallback to `Chaymaa/roi_donut` or other verified datasets is **NOT PERMITTED** because they lack the required behavioral metadata (running speed, stimulus) to test the hypothesis. Using such a dataset would render the core hypothesis untestable.
 4. If the Allen dataset is unavailable, the project status must be updated to reflect a **Blocking Data Gap** and no further analysis steps (NMF, correlation) will be executed.

## 3. Methodology & Statistical Rigor

### Preprocessing (FR-002, FR-011)
* **dF/F Normalization**: $ \frac{F(t) - F_0}{F_0} $. $F_0$ calculated as the 10th percentile of the fluorescence trace over a sliding window.
* **Detrending**: Low-pass filter (e.g., Savitzky-Golay) to remove slow drifts.
* **Deconvolution**: Use **OASIS** (Online Active Subspace Estimation) algorithm to estimate spike rates from calcium traces. This is critical for **FR-011**.
 * *Constraint*: Must run on CPU. `caiman` or a pure Python/NumPy implementation of OASIS will be used.
* **Missing Data**: Linear interpolation if missing rate ≤ 5% (FR-002). Otherwise, raise `DataQualityError`.

### Latent State Extraction (FR-003, FR-010)
* **Algorithm**: Non-negative Matrix Factorization (NMF).
* **Input**: Matrix $V$ (Time × ROI).
* **Output**: $W$ (Time × k) and $H$ (k × ROI).
* **Temporal Regularization (FR-010)**: Standard `sklearn.NMF` does not support temporal smoothness.
 * *Approach*: Implement a **custom solver** using `scipy.optimize` that minimizes the standard NMF objective ($||V - WH||^2$) plus a **temporal difference penalty term** ($\lambda ||\Delta W||^2$) on the activation matrix $W$. This ensures temporal smoothness is enforced *during* factorization.
 * *Rejection of Post-Hoc Smoothing*: Post-hoc smoothing of the output $W$ is **methodologically invalid** for the claim of "biologically plausible dynamics" because it does not influence the decomposition objective. It is not a valid fallback.
* **k Selection**: Sweep $k \in [10, 50]$. Stability measured by cosine similarity (SC-004).

### Statistical Validation (FR-005, FR-006, FR-009)
* **Correlation**: Spearman rank correlation between $W$ (component weights) and behavioral metrics.
* **Permutation Test**:
 * **Iterations**: Exactly 1000 (FR-005).
 * **Null Hypothesis**: No association between component weights and behavior.
 * **Procedure**: **Shuffle the time indices** of the behavioral metadata (or component weights) 1000 times, recompute correlation, build null distribution. This destroys temporal structure while preserving marginal distribution.
 * **p-value**: Proportion of null correlations ≥ observed correlation.
* **Multiple Comparison Correction**: Since multiple components (k) and multiple behaviors are tested, apply **Benjamini-Hochberg (FDR)** correction to control False Discovery Rate. Significance is determined by $p_{corrected} < 0.05$.
* **Null Model (FR-009)**: Compare NMF results against a **Time-Shuffled Null Model** where the temporal structure of behavior is destroyed. If NMF correlations are not significantly better than this null, the states are trivial. The "linear mixing" model is rejected as a category error.

### Compute Feasibility (FR-007, SC-002)
* **Environment**: CPU-only (2 cores, 7GB RAM).
* **Optimization**:
 * **Data Subsetting**: Load only one session (time window) that fits in memory.
 * **Chunking**: Process NMF in chunks if $V$ is too large.
 * **Library**: `scikit-learn` (CPU wheels), `numpy`, `scipy`. No `torch`/CUDA.
 * **Timeout**: 6 hours. Permutation test (1000 iters) is the bottleneck. If $k=50$, this is $50 \times 1000$ correlations. Must be optimized (vectorized).

### Validation Strategy (FR-008)
* **Time-Based Split**: Data will be split into Training ([deferred]) and Testing ([deferred]) sets based on **time** (chronological order) to preserve temporal integrity.
* **NMF Fitting**: NMF is fitted **only** on the Training set.
* **Validation**: Correlation and permutation tests are performed **only** on the held-out Testing set. This prevents circular validation and ensures the states generalize to unseen data.

## 4. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|:--- |:--- |:--- |:--- |
| **Dataset Mismatch** | High | Critical | Verify variables in `research.md` phase. If Allen data is missing, **HALT** with clear error. No fallback. |
| **NMF Convergence Failure** | Medium | Medium | Retry with different init (max 3). Log failure. Skip k-value if persistent. |
| **Memory Overflow** | Medium | Critical | Enforce strict 5GB check. Load data in chunks. Abort if exceeded. |
| **Permutation Test Timeout** | Medium | Medium | Vectorize correlation calculation. Reduce iterations to 500 if 1000 exceeds 6h (documented). |
| **Temporal Regularization Absence** | High | Medium | Custom solver is mandatory. If it fails, the project halts; post-hoc smoothing is not a valid alternative. |

## 5. Success Metrics
* **SC-001**: Memory ≤ 5GB.
* **SC-002**: Runtime ≤ 6h.
* **SC-003**: $p_{corrected} < 0.05$ for at least one component-behavior pair on the held-out set.
* **SC-004**: Component stability (cosine similarity) ≥ 0.95 across seeds.
* **SC-005**: Alignment error ≤ 1 frame.

