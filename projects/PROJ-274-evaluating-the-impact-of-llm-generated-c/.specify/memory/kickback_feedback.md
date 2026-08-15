# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T021c` (rejected 1x): The repository lacks the required `data/raw/repo_metrics.json` file, and `code/validation.py` does not implement metric collection using `radon cc -a -s` and `cloc --json` nor does it write the JSON output. Consequently the task’s output and tool‑specific requirements are not satisfied.
- `T021b` (rejected 1x): The required `data/raw/repo_selection_rubric.json` file is missing, and the checksum entry in `data/checksums.txt` refers to `data/llm_config.yaml` instead of the expected JSON file. Consequently, the task’s core outputs and verification steps are not present.
- `T021e` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/repo_covariates.json, data/raw/repo_metrics.json, data/raw/repo_matching_report.json, data/raw/doc_quality_scores.json
- `T016` (rejected 1x): No code, configuration, or JSON output files were provided that implement the required clarification‑question logging, filter by the specified keywords, or expose `help_request_count` and the list of `{timestamp, content}` objects. Consequently the task’s deliverable is missing.
- `T030a` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

