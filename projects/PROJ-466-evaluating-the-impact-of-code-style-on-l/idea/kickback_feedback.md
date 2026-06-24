# Downstream review concerns (address in this revision)

A downstream convergence panel kicked this project back to the idea stage. You MUST revise the idea — especially the `Methodology sketch` — to RESOLVE each concern below, not merely re-state the idea.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'clarified'; worst unresolved severity = 'methodology'. Routing to 'flesh_out_in_progress' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- FR-005 specifies a Kruskal‑Wallis H‑test to assess whether style groups differ in diversity, but the success criterion (SC-002) interprets a significant p‑value as evidence of a *reduction* in diversity. Kruskal‑Wallis is a two‑sided omnibus test that only indicates that at least one group differs, without directionality. The spec should either (a) use a one‑sided test or (b) follow up with post‑hoc pairwise comparisons (e.g., Dunn’s test) to confirm that Strict PEP8 has lower diversity than Neutral, and to control for multiple testing.
