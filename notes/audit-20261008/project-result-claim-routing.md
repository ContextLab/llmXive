# Project outcomes cannot be established by external literature

At 05:34–05:37 UTC on 2026-10-09 the isolated canary's generated results
summary claimed that validation passed and no conditional-TV reversals occurred.
The latter conflicts with the independent prime-11 oracle. The claim pipeline
classified these as external entity facts and attempted Wikipedia URLs named
`All_totients_match_validation` and `Conditional_TV_sequence_is_non-increasing_across_N_values`,
then spent many model calls seeking external substantiation. A web source cannot
establish the outcome of this project's own execution.

Claim extraction now supplies `evidence_scope: project_result | external`.
Project outcomes route to the existing RESULT resolver regardless of whether
the wording is numeric, qualitative, comparative, or causal. They require signed
execution evidence and cannot use external computational/literature fill. An
explicitly external result attributed to another study retains external
resolution, even if it uses phrases such as `accuracy was`. Missing scope keeps
the existing classifier behavior for compatibility. Strict and tolerant YAML
parsing preserve the new field.

Validation: 53 extraction/classification/routing checks passed, one preexisting
skip. Six new behavioral regressions fail on the prior platform. The tests route
unsupported outcomes through the actual resolver with fill enabled and prove
they remain NOT_ENOUGH_INFO without any backend call. A live GPT-OSS extraction
of the observed validation/reversal claims plus a table row count categorized
all three as project results, retained an external paper claim as external, and
excluded planned outputs/time budgets. See `project-result-scope-live.json`.

This corrects evidence routing, not the underlying scientific result. It does
not make the canary accepted and does not fabricate receipts or weaken their
requirements. Model scope classification remains imperfect and requires the
existing independent scientific review as well.
