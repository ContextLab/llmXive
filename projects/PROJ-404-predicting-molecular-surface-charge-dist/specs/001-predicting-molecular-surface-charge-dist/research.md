# Research: Predicting Molecular Surface Charge Distribution from Quantum Chemical Calculations

## Research Question
Can a Geometric Graph Neural Network (GNN) trained on 3D molecular coordinates and connectivity predict atomic Merz-Kollman partial charges with sufficient accuracy (MAE ≤ 0.05 e) to outperform a connectivity-only (2D) GNN baseline, thereby demonstrating that 3D geometry encodes essential electronic structure information beyond topology?

## Dataset Strategy

### Primary Dataset: QM9
**Source**: Hugging Face `lisn519010/QM9` (Parquet).
**Verified URL**: https://huggingface.co/datasets/lisn519010/QM9/resolve/main/data/full-00000-of-00001-e217b6ecfbeb7149.parquet
**Rationale**: QM9 is the standard benchmark for small organic molecules with DFT-computed properties. The verified source provides the necessary atomic coordinates, bond connectivity, and pre-computed Merz-Kollman charges (ESP-derived) required for the regression task.
**Feasibility**: The dataset is large (~133k molecules). To fit the 7 GB RAM constraint, the plan utilizes the `datasets` library with `streaming=True` to iterate over the parquet file without loading the entire table into memory. A fixed random seed (42) ensures reproducible sampling if full processing is infeasible within 6 hours.

### ESP-Derived Charges
**Status**: NO verified source found for a separate ESP-derived dataset.
**Strategy**: The QM9 dataset source listed above contains the `charge` column (Merz-Kollman). This is the ground truth. No external ESP dataset is needed or available; the ground truth is intrinsic to the QM9 release.

### Data Preprocessing
1.  **Filtering**: Remove molecules with missing coordinates or undefined bond orders (as per Edge Case handling in spec).
2.  **Normalization**: Translate atomic coordinates to center-of-mass origin (Constitution Principle VI).
3.  **Splitting**: Apply Bemis-Murcko scaffold extraction (RDKit) to partition data into Train/Val/Test sets. This ensures the test set contains scaffolds not seen during training (Constitution Principle VII).

### Computational Feasibility (CPU vs GPU)
- **CPU-First**: The training of a small SchNet/DimeNet model on a sampled subset of QM9 is feasible on the 2 vCPU / 7 GB RAM GitHub Actions runner. PyTorch Geometric supports CPU training.
- **GPU Escape Hatch**: If the model fails to converge or requires more complex architectures (e.g., larger DimeNet variants), the execution stage will auto-offload to a Kaggle GPU (16 GB VRAM) with a scaled-down epoch count or batch size. The plan explicitly uses `device="cpu"` in the code but structures the runner to detect CUDA requirements if `torch` detects a GPU environment (though the primary plan is CPU).

## Methodological Rigor

### Statistical & Model Rigor
- **Multiple Comparisons**: Not applicable as the primary metric is a single MAE value against a baseline. However, if multiple architectures (SchNet vs DimeNet) are tested, a Bonferroni correction or similar adjustment will be applied to the significance threshold for the MAE difference.
- **Sample Size / Power**: The QM9 dataset is large (~130k). A sample of ~10k-20k molecules for training is expected to provide sufficient power to detect the difference between 2D and 3D models. Power analysis is deferred to the implementation phase (`[deferred]`), but the large dataset size mitigates under-powering risks.
- **Causal Inference**: This is an **observational** study (predictive modeling). Claims will be framed as "associational" or "predictive" rather than causal. The model learns the mapping $f(geometry, connectivity) \rightarrow charge$, which is a deterministic function in the DFT framework, but the neural network approximates this function.
- **Measurement Validity**: Merz-Kollman charges are a standard, validated method for deriving partial charges from the electrostatic potential. The QM9 dataset provides these as ground truth.
- **Collinearity**: Atomic coordinates and bond connectivity are related (geometry determines connectivity), but they are not definitionally redundant. The 3D coordinates provide information (bond angles, dihedrals) that 2D connectivity does not. The model architecture (SchNet) is designed to handle this by using distance-based kernels.

### Addressing Spec Concerns
- **Dataset Fit**: The QM9 dataset *contains* the required variables (coordinates, connectivity, Merz-Kollman charges). No mismatch exists.
- **Constraint Adherence**: No new constraints (RAM, time, thresholds) are invented. The 0.05 e MAE threshold and 7 GB RAM limit are strictly from the spec.
- **Missing Data**: The plan includes a filtering step for molecules with null charges or coordinates, as required by the edge cases.

## Risk Assessment
- **Risk**: OOM on CPU due to large QM9 subset.
  - **Mitigation**: Use streaming loading; if OOM occurs, reduce the sample size (first-N rows) and report the power limitation.
- **Risk**: Model fails to converge (loss plateaus).
  - **Mitigation**: Implement early stopping (patience=10) and log failure code `EXIT_CODE_BASELINE_LOSS` if the 3D model does not beat the 2D baseline.
- **Risk**: No open source for ESP data.
  - **Mitigation**: Use the verified QM9 source which includes Merz-Kollman charges. No external ESP data is needed.
