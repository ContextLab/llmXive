# Duplicate generation across planning stages

The graph maps both `planned` and `tasked` to the same tasker. The tasker already
runs task generation plus analysis/convergence in its first invocation. The next
stage repeats both, rewriting reviewed work and adding another full review round.
The live canary did this from 02:31–02:40 UTC and again until 02:51, then repeated
it after a format kickback (02:51–02:53 and 02:53–03:01). These were generation
passes, not scientific execution.

A completed analysis now records a digest in the existing tasker-rounds record.
The follow-up `tasked`/`analyze_in_progress` stage consumes it only when the exact
feature artifacts, original ideas, constitution, verifier notes, peer reviews and
prompt/template resources are unchanged, and no kickback diagnosis is pending.
The run log records a deterministic skipped model call and the normal stage
transition continues. A return to `planned` always performs fresh work. Receipts
are invalidated before new work, and never written for failed/nonconverged review
or if citation validation changes a reviewed document afterward.

Validation: 77 focused tasker, review-bridge and document-boundary tests pass.
The new file-backed tests execute the actual tasker with controlled model outputs,
then verify reuse, eight input changes plus a contract change, replanning,
transient analysis failure after a prior success, and a post-review citation edit.
This does not certify scientific completion; live pipeline acceptance is pending.
