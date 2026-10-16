# Research: Structure-Only Surrogate Model for 2D Material Elastic Moduli

## 1. Problem Definition

Predict Young's, Shear, and Poisson's ratios for 2D materials using a **Structure-Only Surrogate Model** — a machine-learning interpolator of pre-computed DFT results. It does not solve the Schrödinger equation; it learns statistical correlations between structural descriptors and DFT-derived elastic properties. All claims are associational and valid only within the training distribution.

## 2. Dataset Strategy

Only the verified, directly-downloadable parquet URLs below are used (single canonical source per run; no access-gated data):

| Dataset | Verified URL | Content | Role |
| :--- | :--- | :--- | :--- |
| DFT parquet (primary) | `https://huggingface.co/datasets/bio-datasets/dft23-full/resolve/main/data/test-00000-of-00001-a791a8874f9adf69.parquet` | DFT-computed records | **Primary canonical source** |
| DFT parquet (secondary, same-schema) | `https://huggingface.co/datasets/sdmattpotter/dftest61523/resolve/main/data/train-00000-of-00001-17dbf6e61ca73a23.parquet` | DFT-computed records | Alternate canonical source (if primary lacks required fields) |
| DFT parquet (secondary, same-schema) | `https://huggingface.co/datasets/sdmattpotter/dftest61623/resolve/main/data/train-00000-of-00001-17dbf6e61ca73a23.parquet` | DFT-computed records | Alternate canonical source |

**Note (dataset-variable fit)**: These are the only verified sources available. The loader MUST, at download time, validate that the chosen parquet actually contains the structure/CIF field and the 6-component elastic tensor required by FR-001 and Principle VI. If the primary source lacks a required field, the loader falls back to the same-schema alternates; if none contains the required fields, the pipeline exits with an explicit dataset-mismatch error rather than fabricating data. This validation is a hard gate in T013d1.

**Handling**: SHA-256 checksum recorded under `data/`; raw file preserved unchanged; row-count check against SC-001 (>1,000 valid 2D entries, or all available if fewer — logged honestly if fewer).

*(Correction from prior plan: `matbench/elasticity` was removed because it is not in the verified dataset list.)*

## 3. Methodology

### 3.1 Graph Construction
- **Nodes**: atoms; features = atomic number, electronegativity, covalent radius, group/period.
- **Edges**: PBC-aware neighbor connections via pymatgen; adaptive cutoff `r_A + r_B + 0.5 Å`.
- Edge features: bond distance, electronegativity difference.

### 3.2 Model
- Lightweight MPNN (2–3 message-passing layers, hidden dim ≤ 64), CPU-only `torch`.
- Weighted/normalized MSE loss (targets z-scored; Poisson's ratio weighted to match GPa-scale targets' contribution).

### 3.3 Split (FR-002, SC-002)
- **Family** = space group + cation-anion stoichiometry class (spec definition).
- Families assigned to train/validation/test with pinned seed; **no family spans splits** (leakage check in T017b).
- Baseline: composition-only linear regression (Magpie-style features) for the SC-002 ≥10% relative-MAPE-reduction comparison.

### 3.4 Statistical Rigor
- **Multiple comparisons**: feature-importance significance uses permutation tests with Holm–Bonferroni correction across descriptors.
- **Power**: test set of unseen families may be small; 95% CI for MAPE computed via bootstrap; limitation reported explicitly in `generalization_metrics.json` if n_test < 50.
- **Causal framing**: strictly associational; surrogate interpolation of DFT data.
- **Collinearity**: structural descriptors are correlated; SHAP magnitudes (not marginal p-values) plus permutation ablation deltas are used, and correlated descriptors are reported descriptively (FR-005, Principle VII).
- **Measurement validity**: ground truth is DFT-derived elastic tensors from the canonical source; moduli derived via standard continuum-mechanics relations in code (Principle VI).

## 4. Compute Feasibility

**CPU-first**: everything runs on 2 CPU / 7GB RAM / ≤6h. No GPU escape hatch needed — the GNN is small (≤64 hidden), batches are 16–32, ingestion streams parquet rows. `tracemalloc` enforces the 7GB budget (FR-003). Inference of a ≤64-dim GNN on ≤100-atom graphs is far below 100ms on CPU (SC-003).

## 5. Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| Verified parquet sources only | Only reachable, programmatic, non-gated data; CI-runnable (Principle I). |
| Lightweight MPNN on CPU | Faithful CPU-tractable form; fits memory/time budget. |
| Family-based split | SC-002 requires unseen-family generalization; prevents memorization. |
| Permutation + SHAP | FR-005/SC-005 require both; SHAP handles collinearity, permutation gives ablation deltas. |
| Bootstrap CI on MAPE | Honest uncertainty for small unseen-family test sets. |
| Hard gates with exit codes | Verifier-rejected tasks (T060c, T018b) showed gates must actually fail loudly and write artifacts. |
