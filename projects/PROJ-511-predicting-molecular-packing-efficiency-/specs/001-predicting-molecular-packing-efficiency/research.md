# Research: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

## Scientific Rationale
The central hypothesis is that **molecular topology**, captured by canonical SMILES strings, contains predictive information about a crystal’s **packing coefficient (PC_raw)**. PC_raw is defined as  

\[
\text{PC}_{\text{raw}} = \frac{\displaystyle\sum_{i}{V_{\text{vdW},i}}}{\text{Unit‑cell volume}}
\]

where \(V_{\text{vdW},i}\) are atomic van der Waals volumes taken from the standard Bondi radii (Bondi, 1964, DOI:10.1021/j100785a001). By training a lightweight SMILES‑only regression model (Primary Model) and comparing it to a Geometry‑Only baseline (Full Model), we can assess whether topology alone explains packing efficiency.

## Dataset Strategy
| Dataset | Purpose | Verified URL / Loader | Notes |
|---------|---------|-----------------------|-------|
| **COD (Crystallography Open Database)** | Source of CIFs, unit‑cell volumes, lattice metadata, solvent flags, optional SMILES tags | *No verified URL is present in the “Verified datasets” block.* | Required for FR‑001–FR‑003. Because no verified download link exists, the pipeline cannot currently fetch COD on CI. This is a **Principle VI violation** that must be resolved (see Plan). |
| **SMILES‑Transformer weights** | Frozen encoder for SMILES strings (FR‑004) | Downloaded automatically via `transformers` from HuggingFace (weights cached locally) | CPU‑compatible; streaming inference enforced (FR‑020). |
| **Bondi radii constants** | Atomic vdW volumes for PC calculation (FR‑017) | Implemented via `rdkit.Chem.rdMolDescriptors.GetAtomicVdWVolume` (no external URL) | Cited in FR‑017; satisfies Principle II. |

**Variable Fit Verification**  
Before any analysis, the pipeline validates that each record contains:

- `unit_cell_volume` (mandatory) – abort if missing.  
- `smiles` (extracted or generated) – generated when `_chemical_structure_SMILES` absent (FR‑002).  
- `atom_type_counts` and `atom_count` – used for confounder VIF diagnostics (FR‑009).  

If any mandatory field is absent, the pipeline logs the deficiency and aborts, ensuring data‑hygiene (Principle III).

**Data Volume & Feasibility**  
The COD archive holds > 100 k entries. After filtering for organic molecules with ≤ 50 non‑hydrogen atoms we anticipate > 500 valid rows (SC‑001). Records are streamed; no full dataset resides in memory. SMILES embeddings are written to disk in batches (≤ 64 per batch) to respect the 7 GB RAM limit.

## Methodological Rigor
| Aspect | Implementation |
|--------|----------------|
| **Multiple‑Comparison Correction** | Bonferroni correction applied to the three high‑packing thresholds (α_adj ≈ 0.0167) (FR‑008). |
| **Power Justification** | Bootstrap‑based power analysis (FR‑019) on the empirical PC distribution; with N ≥ 500 the power to detect ρ ≥ 0.3 exceeds 90 %. If N < 500, the pipeline aborts and logs a power warning (SC‑001). |
| **Causal Framing** | Observational study; all claims are framed as “predictive association,” not causal inference. |
| **Measurement Validity** | PC_raw uses Bondi radii (FR‑017); SMILES embeddings come from a peer‑reviewed transformer model (citation recorded). |
| **Collinearity & VIF** | Fingerprint vectors are first reduced via PCA to ≤ 20 orthogonal components; VIF diagnostics are then run on this reduced set plus the 3‑D descriptors and confounders (FR‑009). Features with VIF > 5 are flagged but retained for reproducibility. |
| **Permutation Test** | Two‑sided permutation test with **exactly 10 000** shuffles (FR‑015), parallelized via `joblib`. No timeout; full shuffles are guaranteed. |
| **Residual Analysis** | Correlate model residuals with atom‑type composition to quantify unexplained compositional effects (FR‑014, FR‑021). |
| **Normality Checks** | Shapiro‑Wilk test on residuals; Pearson r is reported regardless of normality to quantify linear association, while Spearman ρ is used for monotonic association (FR‑006). |
| **Feature Ablation** | Compare Primary vs Full model performance to quantify the contribution of 3‑D descriptors (FR‑013). |
| **Sensitivity Analysis** | Sweep high‑packing thresholds {0.5, 0.6, 0.7}, compute Spearman ρ, MAE, and permutation p‑values; apply Bonferroni correction (FR‑007, FR‑008). |

## Decision Rationale
- **CPU‑first**: All core components (RDKit, PyTorch‑CPU, scikit‑learn) comfortably fit within the CI runner’s resources. No GPU fallback is used to preserve deterministic embeddings.  
- **Dataset Choice**: COD is the only source that provides the required crystallographic metadata. Because a verified download URL is missing, the plan **flags this as a blocking issue** rather than fabricating a source.  
- **Statistical Controls**: Bonferroni correction, VIF after PCA, permutation testing, and power analysis collectively address the methodology‑panel checklist for quantitative rigor.  

---