# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Stale contract contradicts the re-plan. output.schema.yaml still specifies 'p_raw ... adjusted ... using Thomson's MTM' and 'p_holm_bonferroni' with field name 'composition_param', while plan.md Phase 2, research.md, data-model.md, and analysis_schema.schema.yaml all mandate Pyper & Peterman N_eff and plain Bonferroni with 'composition_parameter'/'p_bonferroni'. The plan's Project Structure lists only dataset.schema.yaml and analysis_schema.schema.yaml under contracts/, yet output.schema.yaml exists and could be exercised downstream, reintroducing the un-spec'd Holm/MTM methods the re-plan explicitly reverted. Delete or rewrite this contract to match.
- The orphaned contract still specifies 'p_raw ... adjusted for effective degrees of freedom (EDF) using Thomson's MTM' and 'p_holm_bonferroni'. This contradicts the plan's reverted statistics (Pyper & Peterman N_eff + plain Bonferroni, FR-004/FR-010). A stale contract encoding the WRONG statistical method risks the implementer building against it. Delete or update output.schema.yaml to match analysis_schema.schema.yaml.
