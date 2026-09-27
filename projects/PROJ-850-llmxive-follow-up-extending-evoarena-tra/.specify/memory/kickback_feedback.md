# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T006` (rejected 1x): The provided `terminal_bench_evo.py` file is present but the visible code stops before any logic that actually attempts to download the real dataset, decides on fallback, or writes the resulting JSONL to `data/raw/terminal_bench_evo.jsonl`. Moreover, the expected output file is missing, and there is no evidence that the script implements the required download‑fallback flow. The next implementer must add the download verification, fallback generation, and file‑writing code, and ensure the script creates `data/raw/terminal_bench_evo.jsonl`.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: src/agents/base_agent.py
- `T008` (rejected 1x): No scripts, configuration files, or code snippets were presented showing that random seeds have been set deterministically across the project. Without concrete evidence of seed initialization (e.g., `random.seed`, `np.random.seed`, `torch.manual_seed`, etc.) in every relevant script, the requirement is not satisfied. The next implementer must add and commit the seed‑setting code and provide the updated files as proof.
- `T012` (rejected 1x): declared artifact(s) missing/empty/invalid: src/heuristics/conflict_detector.py
- `T013` (rejected 1x): declared artifact(s) missing/empty/invalid: src/heuristics/conflict_detector.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

