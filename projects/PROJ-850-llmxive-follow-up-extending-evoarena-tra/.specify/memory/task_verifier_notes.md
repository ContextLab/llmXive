# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006** — The provided `terminal_bench_evo.py` file is present but the visible code stops before any logic that actually attempts to download the real dataset, decides on fallback, or writes the resulting JSONL to `data/raw/terminal_bench_evo.jsonl`. Moreover, the expected output file is missing, and there is no evidence that the script implements the required download‑fallback flow. The next implementer must add the download verification, fallback generation, and file‑writing code, and ensure the script creates `data/raw/terminal_bench_evo.jsonl`.
- **T007** — declared artifact(s) missing/empty/invalid: src/agents/base_agent.py
- **T008** — No scripts, configuration files, or code snippets were presented showing that random seeds have been set deterministically across the project. Without concrete evidence of seed initialization (e.g., `random.seed`, `np.random.seed`, `torch.manual_seed`, etc.) in every relevant script, the requirement is not satisfied. The next implementer must add and commit the seed‑setting code and provide the updated files as proof.
- **T012** — declared artifact(s) missing/empty/invalid: src/heuristics/conflict_detector.py
- **T013** — declared artifact(s) missing/empty/invalid: src/heuristics/conflict_detector.py
- **T014a** — declared artifact(s) missing/empty/invalid: src/heuristics/conflict_detector.py, data/processed/sensitivity_analysis_thresholds.csv
- **T014b** — declared artifact(s) missing/empty/invalid: src/heuristics/conflict_detector.py, data/processed/sensitivity_analysis_models.csv
- **T015** — declared artifact(s) missing/empty/invalid: src/heuristics/conflict_detector.py
- **T016** — No validation script output, result logs, or precision/recall metrics are present; the claim provides no evidence that the synthetic dataset was run or that the ≥80% baseline was achieved. The required artifact—a report or data confirming the precision/recall performance—is missing.
- **T018** — No test code, data, or results were supplied to demonstrate that `EvoMem-Conflict` filters non‑conflict patches using the US1 heuristic, nor any indication that the required dependencies (T012, T020) were satisfied. The claim lacks any concrete artifact, so the task is not genuinely completed.
- **T020** — declared artifact(s) missing/empty/invalid: src/agents/evomem_conflict.py
- **T021** — declared artifact(s) missing/empty/invalid: src/agents/evomem_conflict.py
- **T023** — The required file `src/analysis/runner.py` does not exist in the repository, so no logging functionality can be verified. The task’s core artifact is missing entirely.
- **T024a** — No `config.json` file containing the runner time limit was provided, nor any evidence that the implementer extracted the limit from a `plan.md` constraints section. The required artifact is missing, so the task is not satisfied.
