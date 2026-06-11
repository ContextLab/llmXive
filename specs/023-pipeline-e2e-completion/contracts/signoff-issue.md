# Contract: Publication Sign-off Issue & Vote Parsing

**Feature**: 023-pipeline-e2e-completion (US5, FR-019..021)

## Issue creation (gate activation)

Opened automatically when a paper reaches `awaiting_publication_signoff`
with all automated checks green (compiled PDF exists, rendering audit
passed, claims/citations verified). Exactly one open sign-off issue per
project (re-activation reuses the existing open issue).

**Required content**:

- Title: `[sign-off] PROJ-### — <paper title>`
- Body tags every maintainer (`@login` for each repo collaborator with
  write access, or the explicitly configured list)
- Links: compiled PDF, paper source, review trail, project page
- One-glance summary: what the paper claims, panel verdict, audit status
- Voting protocol stated verbatim in the body (see below)
- Labels: `publication-signoff`, project id

## Voting protocol

| Action by a maintainer | Meaning |
|-|-|
| 👍 reaction on the issue body, or comment `approve` | approve |
| 👎 reaction, or comment `reject: <reason>` | reject (reason required for routing; bare 👎 prompts for a reason and does not decide) |
| anything from a non-maintainer | ignored for decision purposes |

**Precedence**: any maintainer rejection blocks publication even if
approvals exist; the conflict is recorded in an issue comment.
**Identity**: voter login validated against the maintainer list at parse
time.

## Parser behavior (scheduled poll)

- Decision idempotent: once `signoff.yaml` records `approved` + DOI, the
  parser never re-mints (re-runs converge; edited/deleted issues cannot
  cause a second mint because the local record is authoritative once
  written).
- Approve → mint DOI (Zenodo; sandbox in tests) → write publication
  record → set `posted` → close issue with a comment containing the DOI.
- Reject → convert reason to review feedback → project re-enters the
  revision loop → issue closed with the routing reference.
- No response → reminder comment after the reminder window elapses
  (repeating), project stays parked WITHOUT scheduler picks.

## Failure modes

- DOI minted but state write fails → next poll detects the recorded
  deposition/DOI and completes state convergence without a second mint.
- Issue deleted → gate re-opens a new issue noting the prior one; any
  recorded decision stands.
