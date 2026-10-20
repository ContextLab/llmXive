# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Tasks deliver simulated stand-ins for requirements the spec still mandates against real Uni-GUI logs and real UI-MOPD policy heads. The plan flags the mismatch 'for spec correction', but the spec was never amended, so T001 (synthetic generator tagged FR-001) and T007 (simulated heads/baseline tagged FR-004/SC-002/SC-003) silently relax unsanctioned MUSTs. The spec must be revised to sanction the simulation scope before tasks can claim these FRs/SCs.
- FR-002 states absolute thresholds (AUC-ROC ≥ 0.80, Brier ≤ 0.20) the system MUST meet; T004 reframes them as 'reported relative to a shuffled-label null control' and explicitly plans regimes where thresholds are NOT met. This is a semantic weakening of a MUST adopted without spec amendment — the anti-circularity design is sound, but the spec text must be updated to authorize the relative-to-null framing.
