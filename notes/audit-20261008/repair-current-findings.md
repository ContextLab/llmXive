# Repair input lost current findings inside consolidated issues

Production repair run 37859264827 returned `no_candidate`, saying its issue
evidence contained merged fixes and pending acceptance rather than a concrete
file-level defect. The full current #1139 body does name `graph.py` and the
suspected premature deletion of `kickback_feedback.md`, with a reproduction
sequence. Rendering that 17,089-character body with the deployed head/tail
truncation removed both identifiers. This explains why that finding was not
available to the model; it does not prove the finding itself is a valid repair.

Keep the complete original issue data in `evidence.json`. For model input,
exclude collapsed historical sections and extract each current unchecked
finding into a separately bounded field. Preserve issue identities, current
body excerpts, recent trailing updates, and retry diagnostics.

On the live selected issues (1475, 1474, 1242, 1139, 262), the rendered input is
9,089 characters, within the 12,000-character limit. It contains all five issue
identities and 22 current findings; the graph/kickback finding is now present.
Thirteen repair tests and changed-file Ruff pass, including a regression with
five long consolidated issues that retains the actionable middle finding and
does not mutate the original evidence. A production repair candidate remains
unproven; this change repairs the evidence handoff, not the downstream defect.
