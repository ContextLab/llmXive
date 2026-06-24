# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 6 concern(s) remained unresolved after 3 round(s) at stage 'clarified'; worst unresolved severity = 'requirement'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- User Story 2 has no directly associated functional requirement(s) (FR‑###) or success criterion(​s) (SC‑###). The story describes establishing precision thresholds but the FR list contains no requirement covering precision validation for core invariants, nor is there a SC that measures this activity. This orphan story leaves the implementation without concrete guidance.
- Functional Requirement FR‑005 is referenced in the Assumptions (VIF assessment) but does not appear in the Functional Requirements section. An FR without any backing user story or acceptance scenario constitutes scope creep.
- The contract `knot_record.schema.yaml` requires each record to contain a `source` object (fields: database, version, url, accessed_at) **and** additional fields `source_timestamp` (ISO‑8601) and `checksum_sha256`. The specification’s `Key Entities` section defines only the `source` object with its four fields and does not mention `source_timestamp` or `checksum_sha256`. This mismatch means records will not validate against the schema, violating Plan ↔ contracts consistency.
- Assumptions reference FR-005 (VIF assessment) but no Functional Requirement FR-005 is defined in the specification, causing a missing requirement reference.
- The `KnotRecord` definition lists `source_timestamp` and `checksum_sha256` fields, but the contract `knot_record.schema.yaml` requires a nested `source` object with fields `database`, `version`, `url`, `accessed_at`. This mismatch will cause schema validation failures. Align the record schema with the contract by either embedding these fields inside the `source` object or updating the contract to reflect the flat fields.
- The contract `knot_record.schema.yaml` requires a `source` object with fields `database`, `version`, `url`, `accessed_at`. The spec’s `KnotRecord` entity additionally mandates `source_timestamp` and `checksum_sha256` fields that are not defined in the contract, causing a schema mismatch. This violates the plan‑↔‑contract consistency requirement.
