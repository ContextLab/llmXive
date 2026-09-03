# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T057` (rejected 1x): The provided `code/analysis/gatekeeper.py` is truncated (ends abruptly at “THRESH”) and does not contain the full logic to write the required `gate_result.json`. Moreover, the expected output file `data/derived/gate_result.json` is missing entirely. The task’s core requirement—producing the JSON with the correct `status`, `reason`, and `synthesis_mode` fields—is therefore not satisfied.
- `T014` (rejected 1x): The provided `code/analysis/meta_analysis.py` is incomplete: it only contains utility functions and a partial fixed‑effects implementation, and the file is truncated before any gate‑logic, DerSimonian‑Laird random‑effects model, convergence handling, HK‑adjustment flagging, or JSON output writing are defined. Consequently the script does not meet the specified requirements. The missing functionality must be added to satisfy the task.
- `T018` (rejected 1x): The provided `code/analysis/heterogeneity.py` exists but the visible code stops before any main routine that reads `meta_results.json`, computes I², rounds it to two decimal places, and writes `data/derived/heterogeneity_results.json`. The required output JSON file is missing, and the script does not demonstrate the required rounding or file‑writing behavior. The implementation needs a complete execution block that performs the calculation and saves the result with exactly two decimal places.
- `T015b` (rejected 1x): The provided `code/analysis/narrative_engine.py` does not read `narrative_themes.json` or `gate_result.json` as required, checks a `meta_status` from T014 (which should be ignored), and looks for a `status` field instead of a `synthesis_mode` of `"narrative"`. Moreover, the expected output file `data/derived/narrative_content.md` is absent, indicating the script does not correctly generate the required markdown. The implementation must be revised to depend solely on T057, read the specified JSON files, respect `synthesis_mode == "narrative"`, and produce the markdown file.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

