# Downstream review concerns (address in this revision)

A downstream convergence panel kicked this project back to the idea stage. You MUST revise the idea — especially the `Methodology sketch` — to RESOLVE each concern below, not merely re-state the idea.

**Why it was kicked back**: 8 concern(s) remained unresolved after 3 round(s) at stage 'clarified'; worst unresolved severity = 'methodology'. Routing to 'flesh_out_in_progress' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- SC-002 states 'sufficient observations per dataset' without a numeric threshold. Prior kickback notes data-model.md specifies minItems: 1000, but SC-002 does not explicitly state '≥1000 observations' for verifiability.
- FR-024 (prior sensitivity analysis alpha/gamma ranges) and FR-025 (ELBO variance exclusion) have no matching user story. These are orphaned functional requirements with no story to trace back to. Either add User Story 4 for prior sensitivity or remove if not critical.
- SC-007 (memory <7GB RAM) and SC-008 (runtime <30 minutes) have no matching user story. These infrastructure constraints lack user-facing story backing. Either add User Story 5 for resource validation or move to project constraints section.
- US3 acceptance scenarios (threshold calibration at 95th percentile, adaptive updates) lack explicit SC backing. FR-006/FR-007 cover the functional behavior, but no Success Criteria validates these acceptance scenarios. Add SC-010 for threshold calibration validation.
- Spec header states 'Constitution: Principles I-VIII apply' but the provided Constitution document only defines Principles I-VII. Either remove the VIII reference or confirm Principle VIII exists in the Constitution.
- Spec header states 'Constitution: Principles I-VIII apply' but Constitution file only defines Principles I-VII. Update to 'Principles I-VII apply' to match actual constitution.
- SC-002 states 'sufficient observations per dataset' without defining the threshold. While data-model.md specifies minItems:1000, the spec should explicitly state '≥1000 observations' to enable unambiguous verification of statistical power for anomaly rate detection (1-5% injection rates require adequate sample sizes).
- SC-002 states 'sufficient observations per dataset' without defining the threshold. While data-model.md specifies minItems:1000, the spec should explicitly state '≥1000 observations' to enable unambiguous verification of statistical power for anomaly rate detection (1-5% injection rates require adequate sample sizes).
