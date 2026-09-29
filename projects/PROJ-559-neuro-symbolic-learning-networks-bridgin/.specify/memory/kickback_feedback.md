# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan states the system 'ingests mathematics problems from public datasets (ASSISTments, Khan Academy)... and generates explanations'. It then claims to 'compare the three conditions'. However, the spec (FR-001) requires ingesting *both* datasets. The research.md notes that Khan Academy data lacks a verified URL and relies solely on ASSISTments. If the problem set is limited to ASSISTments, the external validity (generalizability) of the findings to 'mathematics education' is severely compromised. The plan does not address how to mitigate the bias of using a single dataset source for a generalizable claim.
- Constitution Principle II (Verified Accuracy) is marked PASS, but the plan does not explicitly describe the 'Reference-Validator Agent' workflow or the 'CITATION_TITLE_OVERLAP_THRESHOLD' check mentioned in the Constitution. The plan states 'All dataset URLs cross-referenced' but lacks the specific automated gate mechanism required by the Constitution to block review points if citations are unreachable or mismatched.
