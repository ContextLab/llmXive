# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T076` (rejected 1x): The provided `code/data/audit_trail.py` is truncated (the `log_attempt` entry dictionary is incomplete) and thus does not contain a functional implementation. Moreover, there is no evidence that `data_source_report.md` references the audit trail as required. The task’s required artifacts are either missing or not fully realized.
- `T078` (rejected 1x): The provided `tests/integration/test_narrative_pivot.py` file is present, but the excerpt stops before any test function or assertions are shown. There is no visible code that runs the pipeline, checks `meta_results.json` for `synthesis_mode: "narrative"` and `pivot_reason: "Insufficient studies"`, or asserts that `forest_plot.png`, Egger’s test output, and Bonferroni correction files are absent. The required verification logic is therefore missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

