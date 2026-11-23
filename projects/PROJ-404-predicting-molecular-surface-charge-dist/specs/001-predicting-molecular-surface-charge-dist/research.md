# Research: Predicting Molecular Surface Charge Distribution from Quantum Chemical Calculations

## Problem Statement

Can a Geometric Message Passing Neural Network (GNN) trained on 3D molecular coordinates and connectivity predict atomic partial charges (Merz-Kollman) with higher accuracy than a connectivity-only baseline?

**Hypothesis**: 3D geometry encodes electronic environment information that 2D graphs miss, enabling the model to achieve a Mean Absolute Error (MAE) ≤ 0.05 e on **unseen molecular scaffolds**.

**Non-Triviality Note**: The ground truth (Merz-Kollman charges) is deterministically derived from 3D geometry. Therefore, the comparison is not a tautology but a test of **approximation efficiency** and **generalization**. Specifically, we ask: *Does explicit 3D geometry provide additional predictive signal beyond the topological constraints that already determine the charge distribution, particularly for scaffolds not seen during training?* If the 3D model fails to outperform the 2D baseline on unseen scaffolds, it implies that 2D topology contains sufficient information to approximate the 3D-dependent charge distribution for those specific chemical families.

## Charge Model Justification

The choice of **Merz-Kollman** charges as the ground truth is driven by the QM9 dataset's standard release, which provides these values derived from DFT calculations. While ESP-derived charges (including RESP, CHelpG, and Merz-Kollman) are approximations of the electron density and inherently ambiguous (i.e., they are not unique physical observables), they serve as the consistent proxy for "surface charge distribution" in this study.

**Limitation Acknowledgement**: The model is trained to predict *this specific charge definition*, not an absolute physical charge. If the Merz-Kollman scheme is highly sensitive to 3D geometry in a way that 2D topology cannot capture, the 3D GNN will naturally outperform the 2D baseline. However, if the 2D topology already constrains the electron density sufficiently for this specific charge model, the 3D model may not show a significant advantage. This study explicitly tests the *mapping* from geometry to this charge proxy, acknowledging that the "ground truth" is a model-dependent construct.

## Dataset Strategy

The primary dataset is **QM9**, specifically the subset containing pre-computed Merz-Kollman charges. Since the spec requires a CPU-first approach and the full dataset may exceed memory, the strategy involves streaming or sampling the data.

### Verified Datasets

The following sources have been verified for reachability and format. Only these will be used.

| Dataset Name | Source URL | Relevance | Usage Strategy |
|:--- |:--- |:--- |:--- |
| **QM9 (Parquet)** | ` | Contains atomic coordinates, connectivity, and Merz-Kollman charges. | Primary source. Will be loaded via `datasets.load_dataset` in **streaming mode** to guarantee < 7 GB RAM usage. |
| **QM9 (Enthalpy subset)** | ` | Contains QM9-like data. | Fallback if the primary QM9 link lacks Merz-Kollman charges (to be verified during data loading). |
| **QM9 (Gaps subset)** | ` | Contains QM9-like data. | Fallback if primary lacks required charge columns. |
| **DFT (Parquet)** | ` | Contains DFT-derived properties. | Secondary verification if Merz-Kollman charges are missing in QM9 subsets. |

**Critical Data Verification**:
- The plan **MUST** verify that the primary dataset contains the column `charges_merkollman` (or equivalent) before proceeding.
- **Contingency**: If the verified source lacks these columns, the project will **halt** and report "Data Unavailable" rather than fabricating data or using an invalid source. This is a fatal feasibility flaw if the ground truth is missing.

**Data Access Method**:
- Use `datasets.load_dataset("parquet", data_files=[URL], streaming=True)` for memory-mapped streaming. This prevents loading the entire file into memory before filtering.
- **Sampling**: To guarantee < 7 GB RAM usage, if the full stream is too large, the loader will iterate and take the first N rows (e.g., a representative sample) with a fixed seed (42). **Crucially**, sampling (if required) must be performed **before** the scaffold split, or the split must be performed on the full dataset to ensure the test set scaffolds are truly "unseen" and not just "unseen in the sample".

**Missing Data Handling**:
- If a molecule lacks coordinates or connectivity, it will be filtered out immediately.
- If a molecule lacks a Merz-Kollman charge for an atom, the entire molecule will be dropped (imputation is not appropriate for physical ground truths).

## Model Architecture & Methodology

### Primary Model: SchNet (Geometric GNN)
- **Architecture**: Continuous-filter Convolutional Neural Network.
- **Input**: Atomic numbers (one-hot), 3D Cartesian coordinates.
- **Output**: Scalar charge prediction for each atom.
- **Rationale**: SchNet is designed for 3D molecular properties and is available in `torch-geometric`. It runs efficiently on CPU.
- **CPU Feasibility**: SchNet operations are matrix multiplications and radial basis function expansions. These are fully supported by PyTorch CPU backends.
- **Parameters**: Cutoff radius = 5.0 Å; Batch size = 32. (These are chosen to balance O(N^2) complexity and memory usage).

### Baseline Models
1. **Connectivity-Only GNN (2D)**: Standard Message Passing Neural Network (MPNN) using only bond connectivity (2D graph). Input: Atomic numbers, bond types. Output: Scalar charge prediction. This satisfies FR-006.
2. **Atom-Type Average**: The average charge for each atomic type (e.g., all Carbons get the same value). This represents the statistical limit of "2D connectivity" without geometric context.

### Training Strategy
- **Optimizer**: Adam (lr=1e-3).
- **Loss**: Mean Squared Error (MSE) or MAE (L1) on charges.
- **Early Stopping**: Patience=10 epochs based on validation MAE.
- **Split**: Bemis-Murcko scaffold split (80/10/10). This ensures the test set contains scaffolds not seen in training.

## Statistical Rigor & Feasibility

- **Multiple Comparisons**: Only two models are compared (3D GNN vs 2D GNN).
- **Statistical Test**: A **Wilcoxon signed-rank test** (or bootstrap confidence interval) will be used to compare the distribution of per-molecule MAE errors between the 3D and 2D models. A paired t-test is rejected because MAE is non-negative and often skewed, violating normality assumptions.
- **Power Limitation**: The sample size is large enough for GNN training. However, the scaffold split reduces the effective test set size. If the test set contains < 100 molecules, the MAE estimate may have high variance. The plan will **log a warning** and report this limitation, but will **not** switch to a random split (to maintain the integrity of the "unseen scaffold" claim).
- **Causal Inference**: This is a predictive modeling task (regression), not a causal inference study. Claims will be framed as "predictive accuracy" and "generalization to unseen scaffolds," not causal effects.
- **Collinearity**: Atomic number and connectivity are highly correlated with charge. The 3D model is expected to learn the *residual* variation explained by geometry. The plan will not claim "independent effects" of geometry if it is definitionally derived from the same DFT calculation, but rather that geometry provides *additional* predictive signal.

## Compute Feasibility Analysis

- **CPU-First**: The plan uses SchNet, which is CPU-tractable for < 100k molecules with batch size=32.
- **Memory**: Limited RAM is tight for full QM9. The plan mitigates this by:
 1. Streaming data (`streaming=True`) to avoid full file load.
 2. Using `float32` precision.
 3. Explicitly measuring peak memory usage during loading and training.
- **Time**: A duration of several hours is sufficient for multiple epochs on 50k molecules with a small GNN.
- **GPU Escape Hatch**: Not planned initially. If the CPU run fails due to time constraints (e.g., > 6h), the execution stage will auto-offload to Kaggle GPU. The code will support `device="cuda"` if detected, but the default plan is CPU.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Missing Merz-Kollman columns** | Fatal | T001 verifies schema. If missing, pipeline halts with "Data Unavailable" error. |
| **OOM on Data Loading** | High | Streaming loader and memory estimation mitigate this. |
| **Model Convergence Failure** | Medium | Early stopping and logging. If loss does not decrease, report failure code. |
| **Scaffold Split Imbalance** | Medium | If test set < 100 molecules, report high variance limitation (no fallback to random split). |
| **Runtime > 6h** | High | Monitor training time; if approaching limit, reduce epochs or sample size (pre-defined). |