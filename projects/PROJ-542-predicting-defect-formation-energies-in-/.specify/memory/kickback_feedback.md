# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The acceptance criteria (RMSE ≤ 0.5 eV and R² ≥ 70 %) are introduced without any justification or power analysis; they appear arbitrary and may be unattainable given the expected data distribution, risking a false‑negative conclusion.
- The plan validates that the feature matrix contains **≥ 50** rows before CV, yet the success criterion (SC‑005) requires **≥ 500** valid compositions. No statistical power calculation is provided to show that 50 (or even 500) samples are sufficient to detect the targeted effect size.
- Potential confounding factors (e.g., DFT functional, calculation settings, temperature, pressure) are not modeled or controlled, yet they may systematically affect defect formation energies and thus bias the learned relationships.
