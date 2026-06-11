# Downstream review concerns (address in this revision)

A downstream convergence panel kicked this project back to the idea stage. You MUST revise the idea — especially the `Methodology sketch` — to RESOLVE each concern below, not merely re-state the idea.

**Why it was kicked back**: 9 concern(s) remained unresolved after 3 round(s) at stage 'clarified'; worst unresolved severity = 'methodology'. Routing to 'flesh_out_in_progress' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- FR-005 (visualization generation) has no corresponding Success Criterion; add an SC that measures visual output quality or presence (e.g., SC‑XXX: visualizations include recession shading and are reproducibly generated).
- FR-008 (handling incomplete FRED data) is not referenced by any Success Criterion; introduce an SC that verifies flagged periods and interpolation/exclusion logic meet a completeness threshold.
- FR-009 (detecting remaining non‑stationarity after differencing) lacks an SC; add a criterion that logs are produced and reviewed, or that a fallback transformation is applied when diagnostics trigger.
- FR-010 (low‑confidence sentiment volume flagging) is not linked to any SC; create an SC that ensures flagged periods are reported and do not exceed a configurable proportion of the dataset.
- SC-004 describes bootstrap confidence‑interval robustness, but no functional requirement explicitly mandates bootstrap computation; either extend FR‑006 to include bootstrap validation or add a new FR (e.g., FR‑011) that specifies the bootstrap procedure.
- Success Criterion SC-004 states "Robustness is measured against the consistency of results across bootstrap confidence intervals on configurable iterations" but does not define a quantitative threshold or concrete metric for "consistency". Without a numeric definition (e.g., width of confidence interval ≤ X% of point estimate, overlap ≥ Y%, or variance reduction ≤ Z), this criterion cannot be objectively verified.
- Success Criterion SC-002 mentions "Data completeness is measured against the requirement for continuous monthly time-series alignment without manual intervention" but does not specify a measurable threshold (e.g., ≤ 0 % missing months, ≤ 1 % interpolation rate). The lack of a concrete metric makes this criterion untestable.
- The specification omits a functional requirement that documents the NLP sentiment extraction pipeline (model, tokenizer, scoring thresholds, and validation on a held‑out sample). Constitution Principle VII mandates Sentiment Methodology Transparency, which is not reflected in any FR (e.g., missing FR‑011).
- The acceptance scenario validates linear interpolation of missing values by requiring the Pearson correlation between the original (incomplete) series and the interpolated series to be ≥ 0.95. This validation is ill‑defined because the “original” series contains missing entries, making a Pearson correlation undefined or based on a reduced set of points. Moreover, a high correlation does not guarantee that interpolation will not introduce spurious autocorrelation or bias downstream Granger‑causality tests. The methodology should instead assess the impact of interpolation on stationarity and causality results (e.g., via simulation or sensitivity analysis) or adopt imputation methods that preserve statistical properties.
