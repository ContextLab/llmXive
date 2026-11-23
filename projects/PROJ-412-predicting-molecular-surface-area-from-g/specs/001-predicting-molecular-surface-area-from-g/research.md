# Research: Predicting Molecular Surface Area from Graph Convolutional Networks

## 1. Research Question
Can a Graph Convolutional Network (GCN) trained solely on 2D topological features (SMILES) predict molecular surface area (SA) with accuracy comparable to a baseline method that utilizes 3D conformer geometry?

## 2. Dataset Strategy

We will use verified, open-source datasets available via HuggingFace. No access-gated or fabricated data will be used.

| Dataset Role | Source Name | Verified URL | Access Method | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Source** | ZINC15 | `https://huggingface.co/datasets/jonghyunlee/ZINC15/resolve/main/zinc_processed.parquet` | `datasets.load_dataset(..., streaming=True)` | Contains SMILES. 3D labels generated in situ. |
| **Fallback Source** | QM9 | `https://huggingface.co/datasets/ncbi/qm9/resolve/main/qm9.parquet` | `datasets.load_dataset(..., streaming=True)` | Pre-computed 3D properties (SA, volume, etc.). Used if ZINC15 fails pilot. |
| **Descriptor Source** | RDKit Chemical | `https://huggingface.co/datasets/nglebm19/rdkit_chemical/resolve/main/data/train-00000-of-00001.parquet` | `datasets.load_dataset(..., streaming=True)` | Used for validation of RDKit descriptor generation logic. |

**Dataset Fit Verification**:
- The ZINC15 dataset contains SMILES strings but lacks pre-computed 3D surface area.
- **Resolution**: For ZINC15, we will generate 3D SA labels dynamically using RDKit's `CalcTPSA()` or `CalcSurfaceArea()` on 3D conformers generated *in situ*.
- **Fallback**: If the ZINC15 pilot phase indicates that generating 1000 3D conformers will exceed the 4-hour runtime budget, the pipeline switches to QM9, which provides pre-computed 3D properties (including SA) to ensure the study remains statistically valid within the CI limits.
- **Constraint**: We must ensure the subset of molecules for which 3D conformers can be successfully generated is large enough (N >= 1000) for training. If >10% fail (Edge Case), the pipeline halts or switches to QM9.

## 3. Methodology

### 3.1 Data Ingestion & Preprocessing
1.  **Pilot Phase**: Run a 10-molecule pilot on ZINC15 to estimate conformer generation time. If `1000 * pilot_time > 4 hours`, switch to QM9.
2.  **Ingest**: Stream SMILES from the verified ZINC15 URL (or load QM9 if switched).
3.  **Sanitize**: Use RDKit to validate SMILES. Discard invalid strings (Log warning).
4.  **2D Graph Construction**: Convert valid SMILES to molecular graphs. Extract node features (atom type, hybridization, charge) and edge features (bond type).
5.  **3D Label Generation (Seed A)**:
    - Generate 3D conformers using RDKit (`EmbedMultipleConfs`) with **Seed A** (e.g., `seed=42`).
    - Minimize energy (MMFF94).
    - Compute Topological Polar Surface Area (TPSA) or Total Surface Area.
    - **Log**: Record conformer generation parameters (attempts, minimization steps) and **Seed A** to satisfy Constitution Principle VII.
    - **Exclude**: Molecules failing conformer generation are excluded.
6.  **Baseline Feature Extraction (Seed B)**:
    - **CRITICAL STEP**: Generate a *second* set of 3D conformers for the *same* molecules using **Seed B** (e.g., `seed=123`), where Seed B != Seed A.
    - Minimize energy (MMFF94).
    - Compute 3D Geometric Descriptors (Volume, Radius of Gyration, Shape Invariants) from this *distinct* conformer set.
    - **Rationale**: This separation ensures the baseline model learns the generalizable relationship between 3D geometry and SA, rather than overfitting to the specific noise of the label's conformer generation.
7.  **Splitting**:
    - Stratify by Molecular Weight.
    - Perform Kolmogorov-Smirnov (KS) test.
    - **Threshold**: p-value > 0.05 (per Spec US-1.3 and Verified Fact: KS threshold = 0.05).
    - If p < 0.05, adjust split or re-sample until condition met.

### 3.2 Model Architecture

#### A. 2D-Only GCN (Experimental Model)
- **Input**: 2D Graph (Node/Edge features).
- **Architecture**: 2-3 GCN layers, ReLU activation, Global Mean Pooling, Dense output layer.
- **Hardware**: CPU-only (PyTorch CPU).
- **Training**:
    - Loss: Mean Squared Error (MSE).
    - Optimizer: Adam.
    - Epochs: Max 50.
    - Early Stopping: Patience = 5.
    - Batch Size: Small (e.g., 32) to fit RAM.

#### B. Geometry-Based Baseline (Predictive Model)
- **Input**: 3D Geometric Descriptors derived from **Seed B** conformers (distinct from the label generation Seed A).
- **Architecture**: Ridge Regression or shallow MLP (2 hidden layers).
- **Rationale**: This baseline is a *predictive model* trained to map 3D descriptors to SASA. By using a different conformer seed than the label generation, we ensure the baseline has non-zero error (it cannot simply recall the label's noise), making the comparison with the 2D GCN scientifically valid and avoiding circularity in the t-test.
- **Training**: Same hyperparameters as 2D GCN (epochs, early stopping).

### 3.3 Evaluation & Statistical Analysis

1.  **Metrics**: MAE, RMSE, R².
2.  **Comparison**: Paired t-test on prediction errors (2D GCN vs. Geometry-Based Baseline) on the test set.
    - **Null Hypothesis**: No difference in MAE.
    - **Effect Size**: Cohen's d.
3.  **Sensitivity Analysis**:
    - Sweep thresholds: {0.01, 0.05, 0.1} Å².
    - Calculate "Success Rate" (MAE < threshold) for each.
    - **Correction**: Apply McNemar's test to compare success rates, followed by Bonferroni correction for multiple comparisons (FR-007).
4.  **Feasibility**: Log total runtime.

## 4. Statistical Rigor & Assumptions

- **Causal Claims**: None. This is an associative study. We claim "2D topology predicts SA" only in the sense of correlation/prediction, not causation.
- **Multiple Comparisons**: Addressed via McNemar's test + Bonferroni in the sensitivity analysis (FR-007).
- **Sample Size/Power**: Target N=1000 successful 3D conformers. The pilot phase ensures this is achievable. If the pilot fails, the dataset is switched to QM9 to guarantee N=1000.
- **Collinearity**: 2D descriptors and 3D SA are inherently correlated. The baseline uses 3D geometry directly; the 2D GCN uses 2D. We acknowledge that 2D features are proxies for 3D structure.
- **Measurement Validity**: "Ground truth" is RDKit-computed SA. This is a heuristic value, not experimental. This is explicitly stated in Assumption 5.
- **Baseline Validity**: The Geometry-Based Baseline is a predictive model using 3D descriptors from a *distinct* conformer generation process (Seed B) compared to the label (Seed A). This ensures the baseline has non-zero error, making the comparison scientifically valid.

## 5. Decision Rationale: Compute Strategy

- **CPU-First**: The GCNs are lightweight. Running on CPU avoids the need for a GPU escape hatch, simplifying the CI pipeline.
- **Data Streaming**: Essential to fit the dataset within 7 GB RAM.
- **Pilot Phase**: Ensures that the N=1000 target is met within the time budget, either by ZINC15 or by switching to QM9.
- **No Synthetic Data**: All results will be derived from real model runs on real (or streamed) data. No placeholder metrics will be used.