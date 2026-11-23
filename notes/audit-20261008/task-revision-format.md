# Invalid generated task documents are reply failures

The original production-guarded isolated canary reached a new failure at 07:12 UTC on 2026-10-09: `TaskFormatError: Unterminated Markdown code fence in tasks.md`. The task reviser parsed its response envelope, then completion-preservation validation raised an exception outside the malformed-response classifier. The engine logged a platform failure and left the project planned. The rejected document was not accepted.

Research and paper task revisers now validate generated task syntax before returning it, translating only `TaskFormatError` into the existing malformed-reply error. The existing one corrective retry and bounded engine retry/kickback then apply. Genuine backend/programming errors retain their existing behavior; malformed documents are never substituted for the valid artifact, and independent rereview still decides acceptance.

36 focused revision/recovery/self-consistency checks pass. All six new regressions fail on the old source: unmatched Markdown fences and duplicate task identities recover with a valid second reply on both tracks; persistent malformed replies retain the original input and reach the existing engine classification. Full live convergence remains unproven; this is a demonstrated error-handling fix, not a claim that models now always follow the protocol.
