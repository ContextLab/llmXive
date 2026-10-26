# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 6 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan performs a group‑aware split only by `pairing_id` (Phase 4). If a single material (e.g., `material_1_id` or `material_2_id`) appears in multiple pairings, that material can be present in both training and test sets, leading to data leakage and inflated performance estimates. To control this confound, the split should also enforce that no individual material identifier appears in both sets (e.g., by grouping on both `pairing_id` and the constituent material IDs, or by using a stricter leave‑one‑material‑out strategy).
- The plan references FR‑015 ("Model Training & Nested CV") which does not exist in the specification. This introduces an unbacked functional requirement.
- The plan references FR‑017 (implicit) which is not defined in the spec, creating an over‑reach beyond the documented functional requirements.
- The plan cites OpenML dataset ID 42123 as the primary source of surface‑roughness and tribology data and assumes it contains columns `Sa`, `Sq`, `Ssk`, `Sku`, `Sp`, `Sv`, `coeff_friction`, and `wear_rate`. OpenML ID 42123 is not a surface‑roughness/tribology dataset (it corresponds to a different domain), so it cannot provide the required features. Using this dataset would make the entire analysis incapable of answering the research question.
- Principle II (Verified Accuracy) requires every external citation to be verified. The plan lists OpenML ID 42123 and a NIST DOI but provides no verified URLs in the “Verified datasets” block, violating the constitution.
- Inconsistent terminology for the grouping identifier: the plan (and data‑model) use `pairing_id`, while the specification (FR‑014) refers to `material_pair_id`. This mismatch can cause traceability errors.
