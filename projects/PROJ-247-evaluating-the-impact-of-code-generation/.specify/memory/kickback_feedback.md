# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): No code files, scripts, or modules implementing the required extraction logic are present; the only evidence is the task description and project specifications, which do not include the actual implementation of a parser for Python/JavaScript files to extract functions or classes. The artifact needed to satisfy the task is missing.
- `T012b` (rejected 1x): No code, tests, logs, or any other artifact implementing the `git mv` detection and exclusion logic was provided. The claim cannot be verified because the required implementation and its verification output are missing.
- `T016` (rejected 1x): No code, configuration, or output files were provided that implement the “exclude repos with <5 LLM and <5 Human blocks after tagging” rule. The claim lacks any artifact (e.g., a script, pipeline step, or resulting CSV) demonstrating that repositories are filtered according to the specified inclusion criteria. The required implementation and evidence are missing.
- `T017b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/ground_truth/classifier_metrics.json
- `T021` (rejected 1x): No code, script, or documentation implementing the bug‑fix‑latency calculation is present; the claim provides only a textual description without any artifact (e.g., a Python module, CLI tool, or test suite) that parses commit messages, matches file paths to issue descriptions, or prioritizes issues. Consequently the required implementation is missing.
- `T022` (rejected 1x): No code, script, notebook, or other artifact implementing the required code churn calculation is present. The claim lacks any concrete implementation that aggregates lines added/deleted per block over a multi‑month window (excluding the initial commit), so the task’s deliverable is missing.
- `T023` (rejected 1x): No code, script, log output, or documentation was provided that demonstrates handling of null latency pairs, exclusion from latency analysis, retention for churn analysis, or logging of exclusion reasons. The required artifact is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

