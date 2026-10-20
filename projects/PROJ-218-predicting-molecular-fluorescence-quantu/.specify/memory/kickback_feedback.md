# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 4 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- FR-012 has two branches: (a) for NEW INFERENCE INPUTS, log a warning and SKIP the molecule; (b) during test-set evaluation, retain such molecules and log a transparency summary. T002 and T007 implement only branch (b) ('retain test molecules, log a summary'). No task implements the inference-time skip-with-warning behavior, so half of FR-012's acceptance criterion is dropped from the task list.
- T010 requires '10,000 random draws' and 'p < 0.05' in addition to the 1.5x enrichment, but SC-005 specifies '100 random draws' and requires only >=12/20 overlap plus >=1.5x mean random overlap — no p<0.05 criterion. The task's verification schema hard-codes criteria the spec never authorizes; align T010 with SC-005 or amend the spec.
- Spec's spot-check is for a single high-FQY molecule ('Given a molecule... at least 3 of the top 5 substructures'). T010 silently strengthens it to all five highest-FQY molecules ('spot-check the five highest-FQY test molecules, requiring >= 3 of each molecule's top-5'). A criterion change of this kind needs a spec edit, not a task-level redefinition.
- T001 aborts if 'fewer than 200 valid molecules', while the spec's data-source assumption states the dataset contains 'at least 500 molecules'. The task's feasibility floor is 2.5x weaker than the spec's assumption; either raise the abort threshold or note in the spec that 200 is the accepted floor.
