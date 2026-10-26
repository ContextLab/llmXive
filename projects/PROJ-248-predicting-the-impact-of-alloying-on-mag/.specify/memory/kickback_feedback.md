# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 19 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- FR‑001 is marked **Not satisfied** because no verified Curie‑temperature data is available, yet the specification requires retrieval of Materials Project entries with both magnetic_moment and curie_temperature. The plan does not provide a path to satisfy this mandatory functional requirement.
- FR‑003 (cleaning of the combined dataset) is only partially satisfied for the OQMD‑only subset; the spec expects cleaning of the full Materials Project + OQMD dataset, which is not performed.
- FR‑004 (feature engineering) is implemented only for saturation‑magnetization; the spec requires the same feature set for both targets.
- FR‑005 (train two regression models per target) is fulfilled only for saturation‑magnetization; no models are trained for Curie temperature.
- FR‑006 (hyper‑parameter tuning ≤ 30 min per target) is applied only to the saturation‑magnetization target; the Curie‑temperature target remains untuned.
- FR‑007 (evaluation on internal and external splits) is performed only for saturation‑magnetization; the required evaluation for Curie temperature is missing.
- FR‑008 (paired Wilcoxon signed‑rank test) is executed only for saturation‑magnetization; the test for Curie temperature is absent.
- FR‑009 (feature‑importance reporting) is generated only for saturation‑magnetization; the spec demands this for each target.
- FR‑012 (prediction service must return both saturation_magnetization and curie_temperature) is only conditionally addressed; the plan relies on a schema change rather than delivering the required dual‑target response.
- FR‑013 (external validation set of ≥ 200 distinct alloys for each target) is provided only for saturation‑magnetization; Curie‑temperature external validation is missing.
- FR‑014 (cleaned dataset ≥ 3 500 records for each modelling target) is satisfied only for saturation‑magnetization; the Curie‑temperature target lacks the required record count.
- SC‑001 (performance metrics for both targets) is reported only for saturation‑magnetization; Curie‑temperature metrics are absent.
- SC‑002 (R² ≥ 0.75 for Curie temperature) cannot be evaluated because no Curie‑temperature model is built.
- SC‑003 (Wilcoxon test significance for both targets) is performed only for saturation‑magnetization.
- SC‑004 (feature‑importance must identify ≥ 5 elemental descriptors) is demonstrated only for saturation‑magnetization.
- SC‑005 (prediction latency ≤ 2 s for both targets) is conditional on a schema change; the plan does not meet the original spec requirement.
- SC‑007 (cleaned dataset ≥ 3 500 records for each target) is satisfied only for saturation‑magnetization; the Curie‑temperature dataset size is undefined.
- The plan acknowledges that no verified open‑source dataset provides `curie_temperature`, so FR‑001 cannot be satisfied. Without Curie‑temperature data the core research question (predict both saturation magnetization **and** Curie temperature) is unanswerable as specified, making the chosen dataset inappropriate for the full task.
- FR‑012 requires the prediction JSON to contain both `saturation_magnetization` **and** `curie_temperature`. The plan proposes to either omit the field or set it to `null` only if the schema is relaxed, which conflicts with the mandatory schema in the specification. This mismatch prevents the pipeline from meeting the functional requirement without a spec revision.
