# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008a` (rejected 1x): The `code/utils/checksum.py` script is present, but the required output file `data/checksums.txt` does not exist, so the task of recording the SHA256 checksums for the raw data files is not fulfilled.
- `T013` (rejected 1x): The repository contains the required `code/data/fetch_literature_pcm.py` script, but the expected output file `data/external/literature_pcms_raw.csv` is absent. Without the CSV, the deliverable is not fully satisfied. The next implementer must ensure the script is executed (or otherwise provide the CSV) so that the file exists and contains the fetched literature PCM data.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

