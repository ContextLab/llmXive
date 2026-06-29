# Research: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

## Objective
Quantify the predictive relationship between molecular topology (encoded via a frozen SMILES‑Transformer) and composition‑adjusted packing efficiency (CAPE) in organic crystals from the Crystallography Open Database (COD).

## Dataset Strategy
| Source | Access Method | Expected Records | Notes |
|--------|---------------|------------------|-------|
| COD (organic ≤ 50 non‑H atoms) | `requests` download of COD tarball ` (verified URL) | ≥ 500 after filtering | Filters: atom count, successful SMILES generation, valid geometry. |
| Bondi radii (for Vdw volumes) | Embedded table in `compute_features.py` (cited FR‑018) | N/A | No external download required. |
| SMILES‑Transformer (frozen) | HuggingFace model `seyonec/PubChem10M_SMILES_BPE_60k` (CPU‑only checkpoint) | N/A | Model citation provided in plan; weights are frozen during inference. |

*Only the COD URL and the HuggingFace model URL listed above are used; no other external datasets are introduced.*

## Methodology Overview
1. **CIF Retrieval & Filtering** – Download the COD tarball, parse each entry, keep only organic crystals with ≤ 50 non‑hydrogen atoms. Log download statistics (total entries, kept, discarded).
2. **SMILES Extraction/Generation** – For each CIF:
 - If `_chemical_structure_SMILES` exists, record it (`smiles_source=extracted`).
 - Else generate a canonical SMILES with RDKit from the 3‑D coordinates (`smiles_source=generated`). Flag generated entries in the CSV.
3. **Packing Coefficient & CAPE** – Compute raw packing coefficient (FR‑003) and CAPE (FR‑011) using Bondi atomic volumes. Record `unit_cell_volume`, `packing_coefficient`, `cape`.
4. **3‑D Geometry Descriptors** – For each molecule, generate a single low‑energy conformer with RDKit (MMFF94) **independent of the crystal unit cell**, then compute radius of gyration, asphericity, and principal moments of inertia (FR‑012). This avoids circularity with the target.
5. **Confounder Recording** – Extract lattice system, measurement temperature (K), and solvent presence from CIF metadata (FR‑013). Encode lattice system as one‑hot vectors, normalize temperature, and include the binary solvent flag. These three variables are **included** in the MLP feature vector (addressing FR‑013).
6. **Feature Vector Construction** –
 - Encode SMILES with the frozen SMILES‑Transformer (≈ 512‑dim fingerprint).
 - Reduce the fingerprint to its top 10 principal components (explaining > 90 % variance) to obtain a stable low‑dimensional representation for VIF and multicollinearity diagnostics.
 - Concatenate the PC‑fingerprint, the three 3‑D descriptors, and the three confounder variables.
 - **Atom‑type count features are *not* used as primary predictors**; they are retained solely for the partial‑correlation analysis (FR‑014) and are excluded from `mlp_features`.
7. **Model Training** – 2‑layer MLP (≤ 100 k parameters) trained on an [deferred]/20 % train‑validation split (random seed fixed).
8. **Evaluation** – Compute MAE, Pearson r, Spearman ρ, Shapiro‑Wilk on residuals, VIF diagnostics **only on the PCA‑reduced fingerprint components plus the low‑dimensional descriptors and confounders** (FR‑009), and a two‑sided permutation test with 10 000 shuffles (FR‑006, FR‑016).
9. **Partial‑Correlation** – Assess correlation between predicted and observed CAPE while controlling for atom‑type composition (FR‑014). Atom‑type counts are used only as control variables here.
10. **Ablation Study** – Re‑train the MLP **without** the 3‑D geometry descriptors (`ablation.py`) to quantify any circularity; report side‑by‑side with the full model.
11. **Sensitivity Analysis** – Sweep high‑packing thresholds {0.5, 0.6, 0.7}, recompute r, ρ, MAE, and permutation p‑values; apply Bonferroni correction (FR‑007, FR‑008).
12. **Reporting** – Generate an HTML report (`report.html`) that includes dataset provenance, preprocessing steps, model architecture, all evaluation metrics, VIF diagnostics, partial‑correlation results, ablation outcomes, sensitivity tables, and the git commit hash. The report is validated against `contracts/validation_report.schema.yaml` (FR‑010).

## Statistical Rigor Checklist
- **Multiple‑Comparison Correction** – Bonferroni applied to the three threshold‑specific tests (FR‑008).
- **Permutation Test** – A sufficiently large number of shuffles guarantees fine-grained p‑value resolution. (FR‑016).
- **Power Consideration** – Sample size ≥ 500 provides > 80 % power to detect r = 0.4 at α = 0.05 (documented in `research.md`).
- **Causal Language** – All statements are strictly associational; COD data are observational.
- **Measurement Validity** – SMILES‑Transformer pretrained on > 1 M molecules (publicly documented); Bondi radii are a standard source (FR‑018).
- **Collinearity Management** – VIF computed on PCA‑reduced fingerprint plus low‑dimensional descriptors; any predictor with VIF > 5 is flagged and examined.
- **Leakage Mitigation** – Atom‑type counts are excluded from the primary model input; they are only used as covariates in partial‑correlation and VIF diagnostics.
- **Circularity Check** – Ablation study isolates the contribution of 3‑D descriptors, confirming that performance is not driven solely by geometry derived from the crystal cell.

## Expected Deliverables
- `data/dataset.csv` (≥ 500 rows, complete).
- `models/mlp_regressor.pt` (trained checkpoint).
- `results/validation_report.json` (metrics, VIF, permutation results, ablation outcomes).
- `results/report.html` (human‑readable summary).
- `contracts/` schemas for dataset, model, and validation report.

---

