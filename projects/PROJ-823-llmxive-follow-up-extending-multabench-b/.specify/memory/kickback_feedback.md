# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T063` (rejected 1x): The repository lacks the required `code/pipelines/generate_final_summary.py` script, the `final_gate_report.json`, `zero_variance_audit.log`, and the `correlation_report_{run_id}.json` artifacts, and no `FINAL_RESEARCH_SUMMARY.md` is present. Consequently the task’s core output cannot have been generated.
- `T064` (rejected 1x): The repository contains no `FINAL_RESEARCH_SUMMARY.md` with a `final_verification` section, nor any evidence (e.g., t‑test or correlation output files, logs, or code) showing that the t‑test and correlation were re‑run on the final validated dataset and compared to the initial run. Without these artifacts, the task’s requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

