# Research: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

## Summary

This research investigates the feasibility of replacing the learned causal predictor in a Geometric Action Model (GAM) with a differentiable symbolic solver. The core hypothesis is that a symbolic solver operating in the 3D latent space of a frozen Geometric Foundation Model (GFM) will generalize zero-shot to novel kinematic chains and deformable materials, outperforming the baseline neural predictor in topology-shift scenarios. The study utilizes a synthetic test set generated via PyBullet, ensuring strict isolation from the training distribution.

## Dataset Strategy

### Verified Datasets

The following datasets are verified for use in this project. All downloads will be performed programmatically using the specified URLs or loaders.

| Dataset Name | Source Type | Verified URL / Loader | Usage |
| :--- | :--- | :--- | :--- |
| **PyBullet Physics Engine** | Local Library | `pip install pybullet` | Physics simulation for test set generation and validation. No external dataset download required. |
| **GFM (Geometric Foundation Model)** | Local / User Provided | `data/raw/gfm_weights` (to be populated by user) | Source for frozen GFM encoder/decoder weights and latent space calibration. *Note: No public 3D GFM dataset exists; weights must be provided by the user.* |
| **Baseline GAM** | Local Implementation | `code/models/baseline_gam.py` | Baseline comparison for neural predictor performance (implemented locally). |
| **Training Topology Manifest** | Local / User Provided | `data/raw/training-topology-manifest.json` (to be populated by user) | Reference for zero-overlap verification (FR-001). *Note: No public source exists; must be provided by user.* |

**Note**: The "CPU-based" dataset mentioned in the spec has **NO verified source**. The research plan relies on **PyBullet** (verified above) for synthetic generation, which runs on CPU and does not require a pre-existing dataset of novel topologies.

### Data Availability & Feasibility

- **Synthetic Generation (FR-001)**: The primary data source for the test set is **generated** via PyBullet. This avoids the need for a pre-existing dataset of "novel kinematic chains," which does not exist in public repositories. The generation script will use the verified PyBullet physics engine to create 300 unique topologies (variable hinge counts, soft ropes) strictly absent from the `training-topology-manifest.json` (derived from the GFM training data).
- **Streaming Strategy**: The generated test set is expected to be < 2 GB (300 trials, ~10 steps, sparse state vectors). It will be stored locally in `data/generated/`. No streaming is required for the test set itself, but the GFM weights (from verified URLs) will be downloaded once and cached.
- **Access Control**: All verified datasets are local or user-provided. No credentials or data-use agreements are required.

## Methodological Rigor

### Statistical Power & Sample Size

- **Power Analysis**: The study targets a sample size of **300 trials** per condition (Symbolic vs. Baseline). This is calculated to detect a moderate effect size (Cohen's h ≈ 0.5) in success rates with a power of ≥ 0.8 at α=0.05 (two-tailed), accounting for the expected low baseline success rate (e.g., [deferred]) which reduces the number of discordant pairs in McNemar's test. A sensitivity analysis will be performed if the baseline success rate is near 0 or 1.
- **Statistical Tests**:
  - **Success Rate**: McNemar's test for paired binary outcomes (`task_success` vs `task_success`).
  - **Latency**: **Wilcoxon Signed-Rank test** is pre-registered as the primary test due to expected skew in robotics latency data. A sensitivity analysis will be performed if normality is suspected. **Note**: The plan explicitly rejects the flawed two-step testing (Shapiro-Wilk then test) described in FR-006/US-3 of the spec. This is a **Spec Kickback** item; the implementation will use Wilcoxon regardless of normality.
  - **Multiple Comparisons**: Not applicable for the primary binary outcome (single test). If multiple topology types are analyzed separately, Bonferroni correction will be applied.

### Causal Inference & Assumptions

- **Design**: Controlled A/B test on identical synthetic test sets.
- **Assumption**: The frozen GFM encoder produces valid latent representations for novel topologies (latent drift is monitored via Mahalanobis distance).
- **Assumption**: The symbolic solver's constraint satisfaction is mathematically guaranteed in 3D space (verified via PyBullet physics engine).
- **Limitation**: The study is observational regarding the "novelty" of topologies (generated, not real-world). Claims are framed as "zero-shot generalization to *synthetic* topology shifts."

### Computational Feasibility

- **CPU-First**: The entire pipeline (GFM inference, symbolic solving, PyBullet simulation) is designed to run on a standard multi-core x86_64 CPU.
  - **GFM**: Uses `torch` with `device="cpu"` and default precision (no 8-bit quantization needed for inference-only).
  - **Solver**: DiffTaichi is optimized for CPU and can solve small-scale convex problems (< 300s per step) efficiently. For non-convex soft-body dynamics, a projected gradient descent fallback is used.
  - **Simulation**: PyBullet is CPU-native.
- **GPU Escape Hatch**: Not required for this project. The plan explicitly avoids methods that *need* a GPU (e.g., large transformer fine-tuning). If the solver exceeds the 300s timeout, the trial is recorded as a "timeout failure" (Edge Case), not offloaded to GPU.

### Validation Protocol

- **External Outcome**: `task_success` is determined by PyBullet's target check (object within 5cm of goal for 1s), **not** by the solver's internal `solver_feasibility` flag. This ensures the validation is not circular.
- **Decoder Control**: A separate metric `decoder_reconstruction_error` is recorded to ensure the decoder does not fail on novel topologies, decoupling solver failure from decoder failure.
- **Latent Drift**: Mahalanobis distance is calculated against the training distribution reference (Phase 0.2).
- **Ground Truth**: A subset of tasks will have ground-truth 3D trajectories generated via PyBullet to validate the decoder's output against physical reality (Phase 0.4).

### Hybrid Solver Strategy

- **Convex vs. Non-Convex**: The plan acknowledges that soft-body dynamics are non-convex. DiffTaichi will be used for rigid-body constraints (convex), while a projected gradient descent fallback will be used for non-convex soft-body constraints. This addresses the risk of DiffTaichi failing on non-convex problems.

## Decision Rationale

- **Why DiffTaichi?** It provides a differentiable interface for convex optimization, allowing gradients to flow from constraint violations to the solver parameters while keeping the GFM frozen. This satisfies Constitution VI (Latent-Space Symbolic Fidelity).
- **Why PyBullet?** It is the only verified physics engine capable of modeling both rigid-body (kinematic chains) and soft-body (deformable materials) dynamics required for the topology-shift test set.
- **Why Synthetic Test Set?** No public dataset contains the specific "novel kinematic chains" required. Generating them ensures strict topology isolation and reproducibility (Constitution I).
- **Why 300 Trials?** To ensure sufficient discordant pairs for McNemar's test given a potential low baseline success rate, addressing the power analysis concern.
- **Why Wilcoxon Signed-Rank?** Latency data in robotics is typically skewed; pre-registering this test avoids the flawed two-step testing (Shapiro-Wilk then test) that inflates Type I errors.