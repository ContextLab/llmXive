# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): The repository lacks the required `data/annotations/raw_comments.json` output file and the `contracts/annotations.yaml` schema file. Moreover, `src/extraction/preprocess.py` extracts comment data with different field names (`author`, `body`, `created_at`, etc.) and does not write a JSON file matching the specified schema (`reviewer_id`, `comment_body`, `timestamp`, `is_confirmed`, `linked_pr_id`). The task’s core requirements are therefore unmet.
- `T015` (rejected 1x): The repository contains a `src/extraction/preprocess.py` file, but the shown code does not include any logic that writes raw JSON files to `data/raw/` nor generates a `data/raw/checksums.json`. Moreover, the required `data/raw/checksums.json` file is absent from the project. The task’s core requirement—saving raw JSON with SHA‑256 checksums—is therefore not fulfilled.
- `T018` (rejected 1x): declared artifact(s) missing/empty/invalid: src/detection/detect_llm_code.py, data/derived/llm_detections.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

