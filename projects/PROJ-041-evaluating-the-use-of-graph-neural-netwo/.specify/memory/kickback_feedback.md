# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan specifies paired t‑tests on F1‑score vectors for (1) GCN vs. RF, (2) GCN vs. XGB, and (3‑7) each of the top‑5 structural features vs. the null baseline. It is unclear how a ‘structural feature’ alone constitutes a model to generate F1‑scores; the description lacks a concrete modeling pipeline (e.g., a classifier using only that feature) and thus the hypothesis test may not be well‑defined, threatening construct validity and the ability to answer FR‑006.
- The plan conditionally selects the dataset (CTU‑13 if a public mirror is available, otherwise `keys-i/netFlow`). This violates Constitution Principle I (Reproducibility) because the source of raw data may change between runs, leading to non‑deterministic results. A single, fixed dataset source must be used for all runs, or the fallback must be explicitly version‑pinned and documented as part of the reproducibility guarantee.
- The plan tests the top‑5 structural features (identified via Random Forest importance on the full training data) against the null baseline using paired t‑tests on the same hold‑out split. Selecting features on the same data that is later used for hypothesis testing introduces circular validation / data‑leakage, making the significance results invalid. A proper nested‑cross‑validation or separate feature‑selection set is required.
