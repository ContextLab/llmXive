# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 7 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The target variable (segregation energy) is generated solely with an empirical EAM potential and validated against a tiny DFT subset using a MAE ≤ 0.1 eV threshold. This validation may be insufficient to ensure the physical fidelity of the energy labels, threatening construct validity of the outcome variable.
- A fixed MAE ≤ 0.1 eV cutoff is imposed without justification; segregation energies often vary by < 0.1 eV, so this tolerance could allow systematic bias that undermines the credibility of the regression analysis.
- PCA is applied to orthogonalize the three clustering descriptors, yet VIF diagnostics (FR‑007) are still computed on the original descriptors. After PCA the original VIFs become meaningless, creating an inconsistency between collinearity control and the reported diagnostics.
- The power analysis assumes an effect size f² = 0.15 (medium) without empirical justification. Given the novel domain and simulated target, this arbitrary choice may lead to under‑powered or over‑powered designs, compromising the ability to detect true relationships.
- Linear regression is selected solely because it provides p‑values, but no justification is given that the relationship between clustering descriptors and segregation energy is linear. If the true relationship is non‑linear, the chosen model may be misspecified, limiting predictive performance and interpretability.
- Success Criterion SC-004 (multiple‑comparison correction measurement) lacks an explicit mapping in the plan.
- Phase 5 (Potential Validation via `validate_potential.py`) is not required by any functional requirement or success criterion in the spec; it constitutes over‑reach.
