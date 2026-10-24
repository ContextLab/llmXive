# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 9 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Reference power is computed using a fixed Cohen’s d = 0.2 for *all* test types (step 6). Applying a d‑value to F‑tests or odds‑ratio based analyses is not a valid construct; each test has its own standardized small‑effect metric (e.g., f = 0.2 for ANOVA). This threatens construct validity of the primary adequacy indicator.
- The validation sample sizes are very small (15 OA papers for OA rate, 30 papers for extraction validation). Such limited n provides low statistical power to reliably estimate OA prevalence and extraction precision/recall, making any conclusions about overall dataset quality under‑powered.
- The quintile inverse‑frequency weighting is described but not formally modeled; it may not fully control for popularity bias or other confounds (e.g., domain, dataset type). Without a sensitivity analysis that varies the weighting approach, the audit’s prevalence estimates could remain biased.
- The plan states that all intermediate files (e.g., `statistical_params.json`) are validated against JSON‑Schema files in `contracts/`, but no schema for the `StatisticalParameters` entity exists in the `contracts/` directory. Add a `statistical_parameters.schema.yaml` (or equivalent) and update contract tests accordingly.
- The plan references an `ExtractionAuditReport` JSON that must conform to a schema, yet no schema for this entity is provided in `contracts/`. Create a schema (e.g., `extraction_audit_report.schema.yaml`) and include contract tests.
- The `PowerAuditResult` schema lacks a field for `reference_power`, but the plan (steps 6‑7) expects reference power to be stored and reported. Extend the schema to include a `reference_power` (number 0‑1) field or adjust the plan to compute reference power without persisting it.
- The plan mentions a CLI tool `power_analysis.py` (FR‑006) that produces `output/power_requirements.json`, but this script is not listed in the project structure under `code/`. Add the script to the repo or remove the FR‑006 entry from the plan.
- The quickstart notes contract tests for `extraction_audit_report.json`, but no corresponding schema file exists in `contracts/`. This duplicates concern 2; resolve by adding the missing schema.
- Reference power is computed using a fixed Cohen’s d = 0.2 for *all* studies (step 6 of the summary). However, many studies will use F‑statistics or odds ratios, for which Cohen’s d is not the appropriate standardized effect size. Applying d = 0.2 across heterogeneous test types yields invalid power estimates and undermines the primary adequacy metric.
