# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan states **“No verified open dataset provides both SMILES and experimental FQY.”** It then relies on joining a verified SMILES parquet (huggingface URL) with an **unverified** FQY JSON source (none provided). For the research question—predicting fluorescence quantum yields—a verified joint dataset containing both SMILES and FQY is required. Using an unverified or missing FQY source makes the dataset inappropriate and risks the pipeline aborting, violating the data‑resource feasibility requirement.
