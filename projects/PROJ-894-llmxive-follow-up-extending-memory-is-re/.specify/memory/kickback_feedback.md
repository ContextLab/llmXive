# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T011a` (rejected 1x): The `data/raw/locomo.csv` file does not exist, and the provided `code/data_loader.py` contains extensive graph‑parsing imports and logic (e.g., `networkx`, `spacy`) beyond the required simple download‑and‑save functionality. Both the missing output file and the extraneous processing mean the task’s requirements are not met.
- `T011c` (rejected 1x): The repository contains a `code/data_loader.py` file, but it does not demonstrate calling `inject_noise` on the graph from T011a-1 nor does it create the required `data/processed/graphs/graph_noise_42.json` file (the file is missing). Consequently the task’s core output and behavior are not present.
- `T013b` (rejected 1x): The required input graph `data/processed/graphs/graph_noise_42.json` and the output CSV `data/processed/noisy_baseline_results.csv` are both missing, and the provided `code/runner.py` is truncated and does not contain a full implementation that processes the noisy graph or writes the required log file.
- `T019a` (rejected 1x): The provided `code/runner.py` is incomplete (truncated) and does not contain logic that specifically runs the Lazy strategy, applies the 0.7 evidence threshold, or writes results to `data/processed/lazy_results.csv`. Moreover, the required `lazy_results.csv` file is absent. The task’s output schema and logging requirements are therefore not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

