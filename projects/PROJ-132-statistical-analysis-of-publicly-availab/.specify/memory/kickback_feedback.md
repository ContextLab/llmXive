# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T005a` (rejected 1x): No artifact (script, log, report, or data file) was provided to demonstrate that the full eBird Basic Dataset for North America (2020–2024) was actually checked for availability. The claim lacks any concrete evidence of verification, so the requirement is not satisfied.
- `T005b` (rejected 1x): No downloaded dataset files, checksum logs, or verification scripts were presented. The required artifact—a downloaded eBird Basic Dataset (or the sample `vvud/eb-data`) and evidence that its checksums were verified—is missing, so the task is not satisfied.
- `T005d` (rejected 1x): No evidence of an `data/raw/archive/` directory containing copied raw files was provided, nor any SHA‑256 checksum file or listing. The required archive and checksum artifacts are missing, so the task is not satisfied.
- `T016` (rejected 1x): The `src/data/preprocess.py` file does not contain a `generate_provenance` function (the shown excerpt ends before such a definition and the file is truncated), and the required output file `data/provenance/row_mapping.json` is absent from the repository. Both the implementation and the generated artifact are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

