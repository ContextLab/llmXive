# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 7 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan states that if the estimated wall‑clock exceeds 4 h, the ablation job will automatically switch to a 5 000‑molecule training subset, claiming it still meets the ≥ 0.8 power requirement. However, the original a‑priori power analysis was performed for a 10 000‑molecule subset (ΔMAE = 0.1 eV, σ≈0.3 eV). No recalculation or justification is provided to show that 5 k molecules retain the required power, so the fallback could invalidate the statistical conclusions of the ablation study.
- Attribution maps are validated by correlating atom‑level Integrated Gradients scores with Hammett σ constants. Most QM9 molecules lack experimentally measured σ values, and the plan does not describe how missing σ data will be handled or whether a representative subset can be constructed without bias. Without a clear strategy, the attribution validation may suffer from selection bias and lack construct validity.
- When the DFTB baseline cannot be run on the full QM9 set, the plan falls back to a stratified 5 k‑molecule subset for residual‑correlation analysis. The protocol does not specify how stratification will be performed (e.g., by scaffold, molecular size, or property distribution). An unrepresentative subset could bias the Pearson correlation between GNN and DFTB residuals, undermining the claim that low |ρ| ≤ 0.2 supports 2D‑sufficiency.
- Functional Requirement FR-024 (fallback to proxy only after construct‑validity checks) is not referenced in any phase of the implementation plan.
- Functional Requirement FR-025 (orchestrate workflow as separate CI jobs respecting per‑job timeout) is not addressed in any listed phase.
- Principle II (Verified Accuracy) is marked ✅, but the plan does not include any explicit step that verifies external citations/URLs (e.g., QM9, NIST WebBook) against primary sources. A verification step is required to satisfy the constitution.
- The `IonizationEnergyTarget` entity in data-model.md defines a field `value`, while the `dataset.schema.yaml` expects a field `negative_homo_proxy`. This naming mismatch creates inconsistency between the data model and the dataset contract.
