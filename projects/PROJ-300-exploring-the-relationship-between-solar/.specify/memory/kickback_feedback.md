# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'clarified'; worst unresolved severity = 'requirement'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The Assumptions section states: 'The distance from the L1 point to the reconnection region... is approximated as 60 R_E... This distance is used in FR-012 to compute the physics-based propagation lag L_phys; it is not employed elsewhere in the analysis.' However, the preceding sentence in the same paragraph claims: 'The distance... is used *only for interpretive context, not for computing the propagation lag*.' This creates a direct contradiction within the Assumptions section itself regarding whether the 60 R_E distance is used for computation or only context, which conflicts with FR-012's explicit requirement to compute L_phys using this distance.
- SC-002 requires the optimal lag to differ from L_phys by ≤ 15 minutes. This is a hypothesis validation criterion, not a system verification criterion. The system cannot be 'verified' as meeting this if the physics is wrong or the data is noisy. The SC should verify that the system *correctly calculates* the difference, not that the difference falls within a specific range.
