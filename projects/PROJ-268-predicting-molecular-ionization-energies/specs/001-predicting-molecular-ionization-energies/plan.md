# Implementation Plan: Predicting Molecular Ionization Energies with Graph Neural Networks

**Branch**: `001-predicting-ionization-energies` | **Date**: 2026-07-05 | **Spec**: `specs/001-predicting-molecular-ionization-energies/spec.md`

## Summary
This plan implements a CPU-tractable Message-Passing Neural Network (MPNN) to predict molecular ionization energies using the QM9 dataset. The system converts SMILES strings to 2D graph representations via RDKit, enforces a scaffold-based split to test generalization, and performs ablation studies by retraining with zeroed bond features. The implementation strictly adheres to the multi-core CPU / 7GB RAM constraints of the GitHub Actions free tier. The target variable is explicitly defined as `-HOMO` (Highest Occupied Molecular Orbital energy), used as a proxy for Ionization Energy via Koopmans' theorem, with documented approximation errors.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: PyTorch (CPU-only), PyTorch Geometric, RDKit, pandas, scikit-learn, numpy  
**Storage**: Local filesystem (CSV/Parquet/Checkpoint)  
**Testing**: pytest  
**Target Platform**: Linux (GitHub Actions Runner)  
**Project Type**: Data Science / Machine Learning Pipeline  
**Performance Goals**: Training completion ≤ 6 hours; End-to-end pipeline ≤ 12 hours; Memory ≤ 6 GB peak RSS  
**Constraints**: No GPU; No 3D coordinate generation for primary model; No large language models; Strict scaffold splitting  
**Scale/Scope**: Minimum N=20,000 molecules (fixed for power); Batch size ≤ 64  

> **Target Variable Validity Note**: The QM9 dataset does not contain a direct "ionization_energy" column. The study uses `-HOMO` (negative HOMO energy) as the target variable, approximating Ionization Energy via Koopmans' theorem (IE ≈ -HOMO). This is an approximation with known systematic errors (often > 1 eV) for organic molecules. The plan explicitly acknowledges this proxy nature. Phase 0 includes a validation step to document the correlation (R²) between -HOMO and experimental IE values from the NIST Webbook, and to quantify the systematic error margin. The dataset schema reflects this as a proxy variable.

## Constitution Check

| Principle | Status | Implementation Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | `random_seed` pinned in config; `requirements.txt` pins versions; dataset checksums recorded. |
| **II. Verified Accuracy** | **Compliant** | Phase 0 includes a **Verified Accuracy Pre-Check** (Step 1) that validates the dataset URL and column existence *before* any training. The validated URL is `https://huggingface.co/datasets/lisn519010/QM9/resolve/main/data/full-00000-of-00001-e217b6ecfbeb7149.parquet`. All dataset URLs sourced from the "Verified datasets" block; citations validated against primary sources. |
| **III. Data Hygiene** | **Compliant** | Raw data downloaded once; checksums computed; derived data (graphs) saved as new files; no in-place edits. |
| **IV. Single Source of Truth** | **Compliant** | Evaluation metrics derived strictly from `code/evaluation.py` output; model architecture defined in `data-model.md` (not `plan.md`); no hand-typed numbers in paper. |
| **V. Versioning Discipline** | **Compliant** | Artifacts hashed; `state.yaml` updated on change; content hashes tracked. |
| **VI. Structure-Only Graph Fidelity** | **Compliant** | Model input restricted to 2D atom/bond features; 3D conformers used *only* for the DFTB baseline comparison (FR-006) or fallback AM1. |
| **VII. Scaffold-Based Generalization** | **Compliant** | Split logic implemented using `scaffold_split` (80/10/10) ensuring disjoint chemical scaffolds between sets. |

## Project Structure

### Documentation (this feature)
```text
specs/001-predicting-ionization-energies/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (includes Model Architecture)
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── model_output.schema.yaml
    └── ablation_result.schema.yaml
```

### Source Code (repository root)
```text
code/
├── data/
│   ├── download.py          # Fetches QM9 parquet
│   ├── preprocess.py        # SMILES -> Graph (RDKit)
│   └── split.py             # Scaffold split logic
├── models/
│   ├── mpnn.py              # CPU MPNN implementation (defined in data-model.md)
│   └── baselines.py         # DFTB (via RDKit) & Linear Regression
├── experiments/
│   ├── train.py             # Training loop with timeout
│   ├── ablation.py          # Feature zeroing & retraining logic
│   └── evaluate.py          # Metrics & Attribution
├── utils/
│   ├── logger.py
│   └── config.py            # Seeds, paths, hyperparams
├── tests/
│   ├── test_data.py
│   ├── test_model.py
│   └── test_split.py
└── requirements.txt

data/
├── raw/                     # Downloaded parquet files
├── processed/               # Graph objects (pt/parquet)
└── splits/                  # Train/val/test indices
```

**Structure Decision**: Single `code/` directory with modular sub-packages. This minimizes overhead for the CPU runner and keeps the dependency graph simple for `pip install`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Scaffold Split** | Required by Constitution Principle VII and Spec FR-004 to ensure true OOD generalization. | Random split would allow scaffold leakage, inflating metrics and failing the research question. |
| **Ablation Study (Retraining)** | Required by Spec FR-005/US-2 to quantify feature importance. Inference-time noise measures robustness, not predictive contribution. Retraining with zeroed features measures true contribution. | Inference-time noise conflates robustness with feature importance; does not validate if the model *learned* the feature. |
| **DFTB Baseline** | Required by Spec FR-006/US-3 to compare against semi-empirical physics methods. | Using only a linear baseline would not validate the GNN's ability to capture non-linear quantum effects. |
| **Proxy Target (-HOMO)** | Required because QM9 lacks direct IE. Koopmans' theorem is the only scientific bridge available. | Dropping the study or using a different dataset would fail the research question; using a proxy is the only feasible path. |

## Phase Plan

### Phase 0: Research & Data Verification
*Addresses: FR-001, SC-001, Dataset Fit, Target Validity*
1.  **Verified Accuracy Pre-Check**: Validate the QM9 dataset URL (`https://huggingface.co/datasets/lisn519010/QM9/resolve/main/data/full-00000-of-00001-e217b6ecfbeb7149.parquet`) and confirm the existence of the `HOMO` column. If missing, the project is **blocked immediately**. This satisfies Constitution Principle II before any implementation begins.
2.  **Target Validity Validation**: Compute the R² correlation between `-HOMO` and experimental Ionization Energy values from the **NIST Webbook** (for a subset of molecules in QM9). Document the systematic error margin (e.g., "Koopmans' theorem introduces a bias of X eV"). This establishes the construct validity of the proxy.
3.  **Resource Profiling**: Run a small batch (N=1000) of SMILES -> Graph conversion to measure peak RAM and time.
4.  **Baseline Feasibility**: Verify `rdkit.Chem.DFTB` (or equivalent 3D conformer generation + energy calculation) is computable on CPU. If DFTB is too slow, the fallback is to use **AM1** (if available in RDKit) or a **Linear Regression** baseline with a clear note on the limitation. The validation logic for "2D sufficiency" will be adapted (see Phase 3).

### Phase 1: Data Model & Contracts
*Addresses: FR-002, FR-004, Data Hygiene, Single Source of Truth*
1.  **Schema Definition**: Define `MoleculeGraph` schema (nodes: atom type, charge; edges: bond type, conjugation).
2.  **Model Architecture Definition**: Define the exact MPNN architecture (Multi-layer GCN with a fixed-dimensional hidden layer.) in `data-model.md` to serve as the Single Source of Truth.
3.  **Scaffold Split Implementation**: Implement `scaffold_split` using RDKit Murcko scaffolds. Ensure a balanced 1:1 ratio..
4.  **Contract Generation**: Create YAML contracts for input data (noting proxy target), model output, and ablation results.

### Phase 2: Implementation (MPNN & Training)
*Addresses: FR-003, FR-008, SC-003, SC-005, Power Analysis*
1.  **MPNN Architecture**: Implement the **3-layer GCN** defined in `data-model.md` using `torch_geometric`. Ensure all operations are CPU-compatible.
2.  **Training Loop**: Implement with early stopping, gradient clipping, and a hard timeout of several hours.
3.  **Memory Monitoring**: Integrate `psutil` to log Peak RSS. Abort if > 6 GB.
4.  **Sample Size Enforcement**: **Strict Rule**: Training must use a minimum of **N=20,000 molecules**. If 20k exceeds the 6-hour limit even after reducing epochs/dimensions, the study is declared "underpowered" and the limitation documented; N is **NOT** reduced below [deferred].

### Phase 3: Ablation & Evaluation
*Addresses: FR-005, FR-006, FR-007, SC-002, SC-004, Scientific Soundness*
1.  **Ablation Execution (Retraining)**:
    -   Train **5 independent baseline models** (with full features) using different random seeds.
    -   Train **5 independent ablation models** (with bond features zeroed out) using the same seeds.
    -   For each seed pair, compute the per-molecule error vector (Baseline Error - Ablation Error).
    -   Compare the mean of these error differences using a **paired t-test** (p < 0.05, Bonferroni corrected) across the 5 pairs.
2.  **Baseline Comparison**:
    -   Run DFTB (if feasible) or AM1/Linear Regression baseline.
    -   **Fallback Logic**: If DFTB is infeasible, compare GNN residuals against experimental IE trends (if available) or use AM1 as a proxy for 3D physics to test "2D sufficiency".
    -   **Validation Logic**: Analyze if GNN errors are uncorrelated with DFTB residuals (where 3D effects dominate) to validate the independence of the 2D signal.
3.  **Attribution**: Compute gradient-based attribution (**Integrated Gradients**, as defined in `data-model.md` and `model_output.schema.yaml`) for test molecules.
4.  **Chemical Validation**: Compare attribution scores against known chemical trends (e.g., correlation with **Hammett constants** for functional groups) to validate that the model learns chemically meaningful features, distinguishing model reliance from chemical reality.
5.  **Error Analysis**: Correlate error with molecule size/flexibility.

### Phase 4: Integration & Reporting
*Addresses: SC-001, SC-003, Reproducibility*
1.  **Pipeline Assembly**: Chain download -> preprocess -> train -> eval into a single script.
2.  **Artifact Generation**: Produce final metrics table and attribution visualizations.
3.  **Reproducibility Check**: Run full pipeline on a fresh environment to verify checksums and results match.

## Statistical Rigor & Methodological Notes
- **Multiple Comparisons**: Bonferroni correction applied when comparing >2 baselines or ablation conditions.
- **Power Analysis**: Minimum N=20,000 molecules is fixed to ensure power > 0.8 for effect sizes > 0.05 eV. If this N is computationally infeasible, the study is declared underpowered, not arbitrarily reduced.
- **Causal Claims**: No causal claims made. The study is observational/predictive. "Contribution" refers to predictive feature importance (measured via retraining).
- **Collinearity**: Atom types and bond types are definitionally related. The model architecture (MPNN) handles this via message passing; however, independent effect claims for specific bond types will be framed as "predictive contribution" acknowledging inherent correlations.
- **Statistical Test for Ablation**: The ablation study uses **5 paired runs** (baseline and perturbed) to generate 5 per-molecule error difference vectors. A **paired t-test** is performed on these vectors to determine if the perturbed model's errors are significantly higher.

## Compute Feasibility Plan
- **Hardware**: A modest computational configuration with a small number of vCPUs and moderate RAM capacity. (GitHub Actions Free).
- **Strategy**:
  - Use `torch` CPU backend (no CUDA).
  - Batch size capped at a moderate range (dynamic adjustment based on Phase 0 profiling).
  - **Sample Size**: Fixed minimum N=20,000 molecules. If 20k exceeds 6h:
    1.  Reduce model complexity (hidden dims from a higher dimension to a lower dimension, layers from a higher count to a lower count).
    2.  Reduce epochs (if early stopping allows).
    3.  If still infeasible, declare study "underpowered" and document the trade-off. N is NOT reduced below [deferred].
  - DFTB Baseline: If `rdkit`'s DFTB implementation is too slow, use **AM1** (if available) or a **Linear Regression** baseline with a clear note on the limitation. The validation logic for "2D sufficiency" will be adapted to compare against experimental trends or AM1 residuals.
  - Precision: Float32 (default). No 16-bit mixed precision (CPU overhead often negates benefit).

## Attribution Method Consistency
- The attribution method (**Integrated Gradients**) is defined in `data-model.md` and `model_output.schema.yaml`. The implementation in `code/experiments/evaluate.py` will strictly follow these definitions.
- The `AttributionMap` contract ensures consistency between the plan, data model, and output.

## Assumptions
- The QM9 dataset (`https://huggingface.co/datasets/lisn519010/QM9/resolve/main/data/full-00000-of-00001-e217b6ecfbeb7149.parquet`) contains all necessary variables (SMILES, `HOMO`) and is accessible without authentication.
- The "ionization energy" in QM9 corresponds to the vertical ionization energy, approximated by `-HOMO` via Koopmans' theorem, with documented systematic error.
- The 2D graph representation (atom/bond types) is sufficient to capture the majority of the predictive signal for ionization energy in small, rigid molecules, as hypothesized.
- The PyTorch Geometric library and RDKit are available and compatible with the free-tier GitHub Actions runner environment (CPU-only).
- The scaffold-based split successfully separates chemical space such that the test set represents a true out-of-distribution challenge for the model.
- The 6-hour time limit is sufficient for training a small MPNN on a subset of QM9 (or the full set with aggressive batching) on a 2-core CPU.
- No GPU acceleration is available or required; the model must converge using standard float32 precision on CPU.
- The DFTB baseline comparison acknowledges the confounding variable of conformer generation quality when comparing 2D-derived 3D structures against 2D-only GNNs.