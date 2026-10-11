# Research: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

## Scientific Rationale
The central hypothesis is that **molecular topology**, encoded as canonical SMILES strings, carries predictive information about a crystal’s **raw packing coefficient (PC_raw)**. SMILES captures 2‑D connectivity without explicit 3‑D geometry, so we compare a **SMILES‑only** regression model (Primary Model) against a **Full Model** that also receives geometry‑derived descriptors (radius of gyration, asphericity, principal moments). Demonstrating a statistically significant correlation for the Primary Model would support the claim that topology alone contributes to packing efficiency.

The target variable is defined as  

\[
\text{PC}_{\text{raw}} = \frac{\displaystyle\sum_{i}{V_{\text{vdW},i}}}{\text{Unit‑cell volume}}
\]

using Bondi van der Waals volumes (FR‑017). Atom‑type count features are **excluded** from the Primary Model (FR‑021) and examined only in post‑hoc residual analysis (FR‑014).

A **Geometry‑Only** baseline quantifies the maximal predictive power achievable from crystal coordinates, providing a reference for the incremental contribution of SMILES embeddings.

## Dataset Strategy
| Dataset | Purpose | Verified URL / Loader | Notes |
|---------|---------|-----------------------|-------|
| **COD (Crystallography Open Database)** | Source of CIFs, unit‑cell volumes, lattice metadata, solvent flags, and optional SMILES tags | *No verified URL is present in the “Verified datasets” block.* | Required for FR‑001‑FR‑003. Because no verified download link exists, the pipeline cannot currently fetch COD on CI. This is a **Principle VI violation** that must be resolved (see Plan). |
| **SMILES‑Transformer weights** | Frozen encoder for SMILES strings (FR‑004) | Downloaded automatically via the `transformers` library from HuggingFace (weights cached locally) | CPU‑compatible; streaming inference enforced (FR‑020). |
| **Bondi radii constants** | Atomic vdW volumes for PC calculation (FR‑017) | Implemented via `rdkit.Chem.rdMolDescriptors.GetAtomicVdWVolume` (no external URL) | Cited in FR‑017; satisfies Principle II. |

**Variable Fit Verification**  
Before any analysis, the pipeline validates that each record contains:

- `unit_cell_volume` (mandatory) – abort if missing.  
- `smiles` (extracted or generated) – generated when `_chemical_structure_SMILES` absent (FR‑002).  
- `atom_type_counts` and `atom_count` – used for confounder VIF diagnostics (FR‑012, FR‑021).  

If any mandatory field is absent, the pipeline logs the deficiency and aborts, ensuring data‑hygiene (Principle III).

**Data Volume & Feasibility**  
The COD archive holds > 100 k entries. After filtering for organic molecules with ≤ 50 non‑hydrogen atoms, we anticipate > 500 valid rows (SC‑001). Records are streamed; no full dataset is held in memory. SMILES embeddings are written to disk in batches (≤ 64 per batch) to respect the 7 GB RAM limit.

## Methodological Rigor
| Aspect | Implementation |
|--------|----------------|
| **Multiple‑Comparison Correction** | Bonferroni correction applied to the three high‑packing thresholds (α_adj = 0.05 / 3 ≈ 0.0167) (FR‑008). |
| **Power Justification** | Bootstrap‑based power analysis (FR‑019) on the empirical PC distribution; with N ≥ 500 the power to detect ρ ≥ 0.3 exceeds 90 %. If N < 500, the pipeline aborts and logs a power warning (SC‑001). |
| **Causal Framing** | Observational study; all claims are framed as “predictive association,” not causal inference. |
| **Measurement Validity** | PC_raw uses Bondi radii (FR‑017); SMILES embeddings come from a peer‑reviewed transformer model (citation recorded). |
| **Collinearity & VIF** | VIF diagnostics on the full feature matrix (fingerprint dimensions + 3‑D descriptors + confounders) (FR‑009). Features with VIF > 5 are flagged but retained for reproducibility. |
| **Permutation Test** | Two‑sided permutation test with 10 000 shuffles (FR‑015), parallelized via `joblib`. A hard timeout of 2 h; if exceeded, the actual number of shuffles performed is recorded and the deviation logged (SC‑006). |
| **Residual Analysis** | Correlate model residuals with atom‑type composition to quantify unexplained compositional effects (FR‑014, FR‑021). |
| **Normality Checks** | Shapiro‑Wilk test on residuals; Pearson r reported only if p > 0.05 (FR‑014). |
| **Feature Ablation** | Compare Primary vs Full model performance to quantify the contribution of 3‑D descriptors (FR‑013). |
| **Sensitivity Analysis** | Sweep high‑packing thresholds {0.5, 0.6, 0.7}, compute Spearman ρ, MAE, and permutation p‑values; apply Bonferroni correction (FR‑007, FR‑008). |

## Decision Rationale
- **CPU‑first**: All core components (RDKit, PyTorch‑CPU, scikit‑learn) comfortably fit within the CI runner’s resources.  
- **GPU Escape Hatch**: Reserved only for transformer inference if OOM occurs; the pipeline will automatically off‑load to a Kaggle free GPU, preserving methodological integrity.  
- **Dataset Choice**: COD is the only source that provides the required crystallographic metadata. Because a verified download URL is missing, the plan **flags this as a blocking issue** rather than fabricating a source.  
- **Statistical Controls**: Bonferroni correction, VIF, permutation testing, and power analysis collectively address the methodology‑panel checklist for quantitative rigor.  

---
