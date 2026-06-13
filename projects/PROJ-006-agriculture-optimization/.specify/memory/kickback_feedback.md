# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 7 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Power analysis states '1000+ households across multiple regions' but does not provide exact N per region or total. With cluster-robust SEs, only 5 regions (clusters) is below recommended minimum of 10+ clusters for reliable inference. This affects causal validity of region-level conclusions.
- Yield data combines self-report, actual measurement, and remote sensing (measurement_method column in data-model.md). Analysis plan does not specify how measurement method heterogeneity will be controlled for in regression models, risking systematic bias in yield variance estimates.
- Power analysis references 'G*Power methodology' but does not report the actual calculated sample size number, only 'substantial number of households'. Replace with exact N and degrees of freedom used in the calculation for reproducibility.
- Validation subsample size for remote sensing yield estimation is marked '[deferred pending Phase 2 implementation]'. Without a minimum validation sample size, remote sensing yield estimates cannot be validated against ground truth, threatening construct validity of the primary outcome measure.
- Prior concern spec_coverage-3168d713 UNRESOLVED: spec.md still shows "_TODO: extracted from the background by the Specifier agent._". FRs exist in research.md but spec.md—the SSoT for spec coverage—remains empty. Plan coverage cannot be verified.
- Prior concern spec_coverage-97b5c1b6 UNRESOLVED: spec.md still shows "_TODO: measurable outcomes._". SCs exist in research.md but spec.md—the SSoT for spec coverage—remains empty. Success criterion measurement cannot be verified.
- Prior concern spec_coverage-2114af5e UNRESOLVED: spec.md still contains "Imported from legacy technical-design/design.md. The prose has not been verified..." legacy import note. Spec.md requires complete rewrite per pipeline quality bar.
