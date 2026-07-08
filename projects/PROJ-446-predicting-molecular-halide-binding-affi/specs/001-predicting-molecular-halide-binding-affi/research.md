# Research: Predicting Molecular Halide Binding Affinities with Machine Learning

## Dataset Strategy

### Verified Data Availability
The primary data sources are NIST Chemistry WebBook and PubChem. However, the **Verified datasets** block provided in the prompt does not contain a direct URL for NIST halide binding constants or PubChem halide-specific affinity data. The available datasets are:

- **NIST**: `nisten/opus-doctor-patient-conversations-all-human-diseases` (medical conversations, irrelevant)
- **PubChem**: `sagawa/pubchem-10m-canonicalized` (molecular structures, no binding constants), `zpn/pubchem_selfies` (SMILES, no binding data)
- **RDKit**: `fabikru/chembl-2025-randomized-smiles-cleaned-rdkit-descriptors` (descriptors only, no halide binding)

**Conclusion**: **No verified dataset in the provided list contains the required variables:** `host SMILES`, `halide identity (F⁻/Cl⁻/Br⁻/I⁻)`, `binding constant (log K or ΔG)`, and `solvent`.

**Decision**: The pipeline will attempt to scrape NIST/PubChem as per FR-001. However, given the lack of verified URLs with binding data, it is **highly probable that FR-011 (Insufficient Data) will trigger**. The system will log the warning, identify the most abundant halide (likely Cl⁻ or Br⁻ based on general literature), and generate a simulated dataset using the physics-constrained formula:  
`log K_sim = 0.5 * charge_density + 0.3 * cavity_volume + N(0, 0.2)`  
where `charge_density` = sum of Gasteiger charges, `cavity_volume` = RDKit molecular volume (Å³).

**Critical Note on Simulated Data**: The simulated data generation formula **bakes in** the exact causal relationship the model is supposed to discover. Training a model on this data and then 'verifying' the sign of the coefficient (FR-013) is a **tautology**, not a validation of the model's ability to learn from real chemistry. **Therefore, in Simulated Data Mode, the comparative analysis (US-4) is strictly aborted.** The pipeline runs only to validate the code infrastructure, not to produce scientific results.

| Dataset | URL | Variables Present | Variables Missing | Status |
|---------|-----|-------------------|-------------------|--------|
| NIST (General) | N/A (Scrape) | SMILES (if available) | Halide ID, Binding Constant, Solvent | **Unverified**; scraping attempted |
| PubChem (Structures) | `sagawa/pubchem-10m-canonicalized` | SMILES, InChI | Halide ID, Binding Constant, Solvent | **Verified URL, Missing Variables** |
| RDKit Descriptors | `fabikru/chembl-2025-randomized-smiles-cleaned-rdkit-descriptors` | Descriptors, SMILES | Halide ID, Binding Constant, Solvent | **Verified URL, Missing Variables** |

**Fallback Plan**: If scraping yields <50 hosts with ≥3 halides each, switch to simulated data mode (FR-011). All outputs will be marked "Simulated Data Mode" and the comparative analysis (US-4) will be **aborted**.

## Model Strategy

### Algorithm Selection
- **Random Forest (RF)**: Robust to non-linear relationships, handles high-dimensional descriptors (ECFP4), provides feature importance.
- **Gradient Boosting (GB)**: Higher predictive accuracy for structured data, captures complex interactions.
- **Excluded**: Neural networks (GPU required, overkill for tabular data), linear regression (assumes linearity, fails on complex structure-affinity relationships).

### Training Protocol
- **Cross-Validation**: 5-fold, split by **host molecule identity** (not measurement) to prevent leakage (FR-004).
- **Hyperparameters**: Default scikit-learn settings (RF: `n_estimators=100`, GB: `n_estimators=100`, `learning_rate=0.1`) to ensure CPU feasibility and reproducibility.
- **Metrics**: R², RMSE per fold; mean/std across folds.
- **Compute Constraints**: Training on ≤7 GB RAM; data subset if necessary; no GPU/CUDA.

### Statistical Rigor & Underpowered Analysis Gate
- **Bootstrap CIs**: A large number of resamples for pairwise comparisons of R²/RMSE across halide ions (FR-009).
- **Measurement-Level Bootstrap**: To avoid degenerate distributions from 5 folds, we use a measurement-level bootstrap stratified by halide and host.
- **Underpowered Analysis Gate**: **If any halide group has <10 measurements, the pairwise comparison for that group is explicitly aborted.** The report will state the analysis is "underpowered" and report only descriptive statistics (mean, range) with a 95% CI width flag as "wide". No significance testing is performed.
- **No Causal Claims**: All findings framed as associational (FR-008); no randomization or identification strategy available.
- **Collinearity**: Variance Inflation Factor (VIF) calculated for predictors; joint relationships reported descriptively.

## Feature Engineering Strategy

### Molecular Descriptors
- **ECFP4 Fingerprints**: Circular fingerprints (radius=2) capturing local substructures; binary vectors (1024 bits).
- **RDKit Descriptors**: 
  - `charge_density`: Sum of Gasteiger charges (electrostatic component).
  - `cavity_volume`: Molecular volume (Å³) via RDKit.
  - `hbd_count`, `hba_count`: Hydrogen bond donor/acceptor counts.
  - `logP`: Lipophilicity.
  - `num_rotatable_bonds`: Flexibility.
- **Halide Encoding**: One-hot encoding for F⁻, Cl⁻, Br⁻, I⁻ (if multi-halide prediction) or target variable for single-halide mode.

### Physical Plausibility Check (FR-013) - Clarified
- **Real Data Mode**: Verify that the coefficient for `charge_density` is positive (higher positive charge → higher anion affinity) per Coulombic attraction. This is a consistency check, not a causal validation.
- **Simulated Data Mode**: The model will mathematically be forced to recover the positive coefficient for `charge_density` because the target `log K_sim` is DEFINITIONALLY constructed as a linear function of `charge_density`. This is a **trivial confirmation** of the data generation script, not an empirical validation of the model's ability to learn structure-affinity relationships. **Comparative analysis is prohibited in this mode.**
- **Unstable Features**: Flag features with CV ≥ 0.3 across 10 bootstrap resamples.

## Edge Case Handling

| Edge Case | Handling Strategy |
|-----------|-------------------|
| **Inconsistent Units (log K vs ΔG)** | Exclude records with ambiguous units; standardize to log K if conversion possible (ΔG = -RT ln K). |
| **Ambiguous Halide Labels** | Exclude records where halide identity is not explicitly F⁻, Cl⁻, Br⁻, or I⁻. |
| **<50 Host Molecules** | Trigger FR-011: log warning, switch to simulated data, **abort comparative analysis**. |
| **Duplicate Records** | Keep record with most complete metadata; if conflicting binding constants, average and log warning. |
| **Missing SMILES/InChI** | Exclude record; log exclusion count (FR-010). |
| **N < 10 per Halide** | **Abort pairwise comparison** for that halide; report only descriptive statistics. |

## Assumptions & Risks

- **Assumption**: NIST/PubChem scraping will yield ≥50 hosts with ≥3 halides each. **Risk**: High probability of failure; fallback to simulation is critical. **Note**: If simulation is used, comparative analysis is aborted.
- **Assumption**: Molecular descriptors (ECFP, RDKit) capture relevant structural features. **Risk**: May miss subtle electronic effects; physical plausibility check mitigates this.
- **Assumption**: CPU-only training completes within 6 hours. **Risk**: Large descriptor sets may slow training; data subsampling if needed.
- **Risk**: Simulated data may not reflect real chemistry; outputs will be explicitly labeled as "Simulated Data Mode" and not used for comparative analysis.
- **Risk**: Small sample sizes (N < 10 per halide) will lead to underpowered analysis; comparative claims will be aborted.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| **Use Bootstrap CIs instead of Wilcoxon** | N=5 folds insufficient for Wilcoxon; bootstrap provides robust CI estimation (if powered). |
| **Host-Identity Splitting** | Prevents data leakage; essential for valid out-of-sample performance. |
| **Simulated Data Fallback** | Ensures pipeline completeness even if real data is insufficient; physics constraints maintain chemical relevance. **Comparative analysis aborted in this mode.** |
| **CPU-Only, Default Hyperparameters** | Ensures feasibility on GitHub Actions free-tier; avoids GPU/CUDA dependencies. |
| **Underpowered Analysis Gate** | Prevents meaningless statistics from small sample sizes; ensures scientific rigor. |
| **Causal Limitations** | Observational data cannot support causal claims; all findings are associational. |
