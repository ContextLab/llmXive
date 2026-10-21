# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'science'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The data model defines a `run_config` entity (see contracts/run_config.schema.yaml) but the implementation plan never references or uses this entity, violating the Plan ↔ data‑model consistency requirement.
- The plan uses cosine similarity between the Low‑Rank RL update direction and the OPD subspace (early‑trajectory alignment) as evidence that ‘foresight’ has been induced. Because the Low‑Rank RL updates are *explicitly projected* onto that subspace by construction (US‑2), this metric is definitionally guaranteed to be ≥ 0.99 and therefore provides a tautological validation of the hypothesis rather than an independent test.
- Both primary metrics are measured on the same GSM8K subset used for training (or a simple filtered version of it). Without a truly held‑out test set that is independent of the training data, improvements in steps‑to‑80 % could reflect over‑fitting to the specific subset rather than a genuine foresight effect.
