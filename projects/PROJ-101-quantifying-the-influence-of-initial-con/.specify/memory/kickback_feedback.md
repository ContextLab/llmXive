# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The baseline is computed from a single noise‑free trajectory per system dimension (N). This provides no estimate of baseline variability, yet Δλ is defined as the difference from this single value. If the baseline itself fluctuates across runs, the deviation metric will inherit that noise, potentially biasing regression results. A more robust approach would compute multiple baselines per N (e.g., several long clean trajectories) and propagate their variance into Δλ.
- The mixed‑effects model includes a random intercept per trajectory but treats each sliding‑window FTLE estimate as an independent observation. Overlapping windows from the same trajectory are highly correlated, violating the independence assumption and inflating effective sample size. Consider adding random slopes for window size or explicitly modeling the within‑trajectory autocorrelation structure.
- The power analysis assumes 1 080 independent observations, yet the dependence described above (overlapping windows, shared baselines) reduces the effective sample size. Consequently, the claimed ≥ 80 % power to detect a small‑to‑medium effect may be optimistic. Re‑estimate power using the actual hierarchical design (e.g., simulation with the proposed random‑effects structure).
