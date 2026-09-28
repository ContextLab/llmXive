# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017` (rejected 1x): No `build.sh` script or diff showing added logging for compilation warnings/errors and an exit‑code‑1 on failure is provided. Without the actual script (or a clear excerpt) we cannot verify that the required logging and error‑handling behavior was implemented. The task remains undone.
- `T021` (rejected 1x): No `main.cpp` (or any source file) containing the required multi‑threaded worker logic was provided; the evidence contains no code, build scripts, or compiled binaries to demonstrate that `std::thread` and `std::atomic<long>` are used as specified. The implementer’s claim cannot be verified without the actual artifact.
- `T022` (rejected 1x): declared artifact(s) missing/empty/invalid: hardware_spec.yaml
- `T023` (rejected 1x): No `main.cpp` file or diff showing the addition of `std::chrono::high_resolution_clock` timing logic and CSV output is provided. Without the actual source code or generated CSV, we cannot confirm that the required wall‑clock timing and CSV export were implemented. The task therefore remains incomplete.
- `T024` (rejected 1x): No code changes or scripts were provided showing a CSV writer added to `main.cpp` or `run_benchmarks.sh`, and there is no generated CSV file or evidence that rows with the required fields are being appended. The required artifact is missing, so the task is not satisfied.
- `T025` (rejected 1x): No `run_benchmarks.sh` script or diff showing added CPU pinning and governor‑setting logic was provided; there is no evidence of `cpupower` commands or sysfs fallback code, nor any test output confirming the changes work. The required artifact is missing.
- `T026` (rejected 1x): No updated `run_benchmarks.sh` script or any code changes were presented, and there is no evidence (e.g., diff, script content, test output) showing that the script now repeats each configuration ≥5 times with timeout handling. The required artifact is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

