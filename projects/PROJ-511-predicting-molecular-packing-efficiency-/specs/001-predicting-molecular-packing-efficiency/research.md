# Research: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

## Scientific Rationale
The central question is whether **molecular topology**, captured by canonical SMILES strings, carries predictive information about a crystal’s **raw packing coefficient (PC_raw)**. SMILES encodes 2‑D connectivity but not 3‑D packing forces; therefore we compare a **SMILES‑only** regression model against a **Full** model that also receives geometry‑derived descriptors (radius of gyration, asphericity, principal moments). Demonstrating a statistically significant advantage for the SMILES‑only model would support the hypothesis that topology alone holds signal beyond pure geometry.

To avoid circularity, the target is defined as  

\[
\text{PC}_{\text{raw}} = \frac{\text{Unit‑cell volume}}{\displaystyle\sum_i V_{\text{vdW},i}}
\]

where the denominator uses **Bondi** van der Waals volumes (FR‑017). Atom‑count features are deliberately **excluded** from the primary predictor set (FR‑021) and only examined in a post‑hoc residual analysis (FR‑014).

A **Geometry‑Only** baseline quantifies the maximal predictive power achievable from the crystal coordinates themselves, providing a reference for the incremental contribution of SMILES embeddings.

## Dataset Strategy
| Dataset | Purpose | Verified URL / Loader | Notes |
|---------|---------|-----------------------|-------|
| **COD (Crystallography Open Database)** | Source of CIFs, unit‑cell volumes, lattice metadata, solvent flags | *No verified URL is present in the “Verified datasets” block.* | Required fields (`_cell_volume`, `_symmetry_space_group_name_H-M`, `_chemical_structure_SMILES`) are verified in the COD schema. Because a verified download link is missing, the pipeline cannot currently fetch COD data on CI. This constitutes a **data‑availability violation** (Principle VI). |
| **SMILES‑Transformer weights** | Frozen encoder for SMILES strings | `transformers` library (weights cached from HuggingFace) | Downloaded automatically; CPU‑compatible. |
| **Bondi radii constants** | Atomic vdW volumes for PC_raw calculation | Implemented via `rdkit.Chem.rdMolDescriptors.GetAtomicVdWVolume` (no external URL) | Cited as FR‑017. |

**Variable Fit Verification**  
Before any analysis, the pipeline runs a **Schema Validation Step** (Phase 1) that checks the presence of all required variables:

- `unit_cell_volume` (mandatory) → abort if missing.  
- `temperature_K`, `has_solvent`, `lattice_system` (optional) → set to `null`/`False` if absent, flagged in the VIF report.  
- SMILES string (`_chemical_structure_SMILES`) → if absent, RDKit generates a canonical SMILES from the 3‑D geometry (FR‑002).  

If any of the mandatory fields are absent from the verified COD source, the pipeline aborts and reports the mismatch.

**Data Volume & Feasibility**  
The COD archive contains > 100 k entries. After filtering for organic molecules with ≤ 50 non‑hydrogen atoms, we expect > 500 valid records (SC‑001). The JSONL is streamed; no full‑dataset materialization occurs in memory. Embeddings are written to disk in batches (≤ 64 per batch) to respect the 7 GB RAM limit.

## Methodological Rigor
| Aspect | Implementation |
|--------|----------------|
| **Multiple‑Comparison Correction** | Bonferroni correction applied to the three high‑packing thresholds (α_adj = 0.05 / 3 ≈ 0.0167) (FR‑008). |
| **Power Justification** | With N ≥ 500, a bootstrap‑based power analysis (FR‑019) shows > 90 % power to detect a Spearman ρ ≥ 0.3 at α = 0.05. If the final N falls below 500, the pipeline aborts with a warning (SC‑001). |
| **Causal Framing** | The study is **observational**; all claims are framed as “predictive association” (Principle VII). |
| **Measurement Validity** | PC_raw uses Bondi radii (FR‑017); SMILES embeddings come from a peer‑reviewed transformer model (citation in code). |
| **Collinearity & VIF** | VIF diagnostics run on the *full* feature matrix (fingerprints + 3‑D descriptors) (FR‑009). Features with VIF > 5 are flagged; if any primary predictor is highly collinear, it is reported but not removed (to preserve reproducibility). |
| **Permutation Test** | Two‑sided permutation test with 10 000 shuffles (FR‑015). Parallelized via `joblib`. Hard timeout of 2 h; if exceeded, actual shuffle count is recorded, and the deviation is logged (SC‑006). |
| **Residual Analysis** | Correlate model residuals with atom‑type counts to quantify unexplained compositional effects (FR‑014, FR‑021). |
| **Normality Checks** | Shapiro‑Wilk test on residuals; Pearson r reported only if p > 0.05 (FR‑014). |

## Decision Rationale
- **CPU‑first**: All core components (RDKit, PyTorch‑CPU, scikit‑learn) run comfortably within the CI memory/CPU budget.  
- **GPU Escape Hatch**: Reserved only for transformer inference if OOM persists; execution will automatically off‑load to a Kaggle free GPU. No fabricated CPU approximation is used.  
- **Dataset Choice**: COD is the only source that provides the required crystallographic metadata. Since a verified download URL is missing, we **cannot** proceed without either (a) a verified COD mirror or (b) a scope revision to a different open crystallographic dataset. This is explicitly documented to satisfy the Constitution and to avoid hidden data‑access assumptions.  
- **Statistical Controls**: Bonferroni correction, VIF, permutation testing, and power analysis collectively address the methodology‑panel’s checklist for quantitative rigor.  

---
