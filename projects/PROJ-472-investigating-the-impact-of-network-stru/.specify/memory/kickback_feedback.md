# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009` (rejected 1x): The provided `code/data/download.py` only contains helper functions and a truncated placeholder; it never implements the required workflow (fetch both datasets, match subject IDs, store matched subjects or fallback, set `simulation_required` in `data/processed/routing_state.json`, or stream large files). Moreover, the `data/processed/routing_state.json` file is missing entirely. The task’s core logic and output artifacts are therefore not present.
- `T010` (rejected 1x): The provided `preprocess_dMRI.py` is truncated (ends mid‑line with a syntax error) and shows no implementation of the required `.tck`‑to‑adjacency‑matrix conversion using MRtrix3 `tck2connectome`. Moreover, the required parcellation zip file is absent (though the script attempts to download it, the download code itself is incomplete). The artifact therefore does not fulfill the task’s core functionality.
- `T011a` (rejected 1x): The repository contains `code/data/check_availability.py`, but the required input file `data/processed/routing_state.json` is absent, causing the script to raise a `FileNotFoundError`. Consequently, the expected output `data/processed/data_availability_status.json` is never created, and the script appears truncated (no code that writes the JSON). The task’s core requirement—producing the availability status file based on the routing state—is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

