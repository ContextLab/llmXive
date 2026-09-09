# Research: Assessing Uncertainty Quantification Techniques for Machine‑Learning Predicted Material Properties

## Dataset Strategy

| Dataset | Source URL | Variables Required | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **OQMD (Open Quantum Materials Database)** | **NO VERIFIED URL IN BLOCK** | Formation Energy, Bulk Modulus, Band Gap, Composition, Structure | **BLOCKED** | The Spec requires numeric material properties. The provided "Verified datasets" block contains only a text-only dataset (`MixSub`) and weights. **No verified numeric source is available.** |
| **MixSub-LLaMA** | `https://huggingface.co/datasets/AdityaMayukhSom/MixSub-LLaMA-3.2-Text-Only-Overlap-CPU-Score/resolve/main/data/train-00000-of-00001.parquet` | Text-only (no numeric properties) | **Available** | **Unsuitable** for this project. Contains text, not numeric material properties (formation energy, etc.). |
| **MC-Dropout Weights** | `https://huggingface.co/datasets/NoahSizemore/mc_dropout_weights/resolve/main/qualitative_samples_mc_dropout_l1.npz` | Pre-trained weights | **Available** | **Unsuitable** for training; only for qualitative inspection if needed. |

**Feasibility Conclusion**: The project **cannot** be executed as specified because the required numeric dataset is not in the verified list. The plan **does not define** a methodology for a dataset that does not exist. **Action Required**: Add a verified numeric materials dataset URL to the "Verified datasets" block before implementation.

**Methodology Status**: **UNDEFINED**. No methodology is defined for this project due to the missing numeric dataset. All references to training, inference, calibration, and screening are **unimplemented** and **not part of the plan**.

## Decision Rationale

- **Data Blocker**: The plan documents the missing numeric dataset. The implementation logic is **not defined** because the primary data source is missing.
- **CPU-First**: Not applicable. No methods are defined.
- **PCA for GP**: Not applicable. No methods are defined.
- **Seed Robustness**: Not applicable. No methods are defined.

**Fatal Methodology Flaw**: The research design relies on a hypothetical dataset that is not verified. The 'Decision Rationale' section is **not applicable** because no methodology is defined.

## References

- **GPyTorch**: `https://github.com/cornellius-gp/gpytorch` (Verified: Open source, CPU-compatible).
- **OQMD**: `http://oqmd.org/` (Open source, but **no verified URL in provided block**).
- **Materials Project**: `https://materialsproject.org/` (Access-gated, **not** in verified block).