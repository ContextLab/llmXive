# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan attempts to ingest cloud‑screened Landsat LST composites but explicitly states that **no open‑access URL is verified** and the pipeline will abort if the download fails. This violates FR‑002 (must ingest Landsat thermal data) and Constitution Principle II (Verified Accuracy), rendering the analysis unable to proceed without a real, accessible LST dataset. Replace the missing LST source with a verified, openly downloadable product (e.g., a pre‑processed Landsat LST GeoTIFF hosted on HuggingFace or an open Earth Engine export) and update the plan accordingly.
