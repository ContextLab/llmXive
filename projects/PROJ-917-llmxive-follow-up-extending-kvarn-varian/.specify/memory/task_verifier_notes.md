# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — the task writes platform-owned path(s) inside the project: `state/projects/PROJ-917-llmxive-follow-up-extending-kvarn-varian.yaml` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T005b** — The `code/config.py` defines `EPSILON_SWEEP_VALUES` as a dataclass field with a default list `[1e-8, 1e-7, 1e-6, 1e-5, 1e-4]` and not as a top‑level constant, and the list contains extra values (`1e-7`, `1e-5`) beyond the required `[1e-8, 1e-6, 1e-4]`. The task specifically required a constant `EPSILON_SWEEP_VALUES` equal to that exact three‑element list.
- **T006** — The `SimulationState` dataclass in `code/simulation/state.py` lacks the required `timing_metrics: list[float]` field and there is no evidence that this module is imported by T027d. These omissions mean the task’s specifications are not fully satisfied.
- **T008** — The `code/utils/seeds.py` file exists and correctly implements `set_global_seed` (calls `random.seed`, `np.random.seed`, and `torch.manual_seed` when torch is available). However, there is no provided evidence that `main.py` was executed twice with the same seed and that the output checksums were compared, as required by the task’s verification step. The test log only shows a pytest run, not the mandated `main.py` reproducibility check.
- **T009** — The `code/config.py` file exists but its `Config` dataclass lacks the required fields `HIDDEN_DIM`, `OOD_THRESHOLD_SIGMA`, and `MIN_CONVERGENCE_RATE`, and it does not implement any validation that raises an error when `NUM_MATRICES`, `SIMULATION_STEPS`, or `NUM_RUNS` exceed their specified maximums. These omissions mean the task’s core requirements are not met.
- **T032_base** — declared artifact(s) missing/empty/invalid: code/simulation/quantization.py
- **T009_calc** — declared artifact(s) missing/empty/invalid: code/analysis/theoretical_lower_bound.py, data/analysis/theoretical_lower_bound.json
- **T035b** — declared artifact(s) missing/empty/invalid: code/simulation/autoregressive_loop.py
- **T027d-core** — declared artifact(s) missing/empty/invalid: code/simulation/autoregressive_loop.py
- **T027d-integrate** — declared artifact(s) missing/empty/invalid: code/simulation/autoregressive_loop.py
- **T028** — declared artifact(s) missing/empty/invalid: code/simulation/kl_divergence.py
- **T030b-impl** — declared artifact(s) missing/empty/invalid: code/simulation/batch_runner.py
- **T030b-main** — declared artifact(s) missing/empty/invalid: data/results/simulation_run_001.json
- **T033** — declared artifact(s) missing/empty/invalid: data/results/final_report.md
- **T039b** — the task writes platform-owned path(s) inside the project: `state/projects/PROJ-917-llmxive-follow-up-extending-kvarn-varian.yaml` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T043** — declared artifact(s) missing/empty/invalid: data/metrics/training_log.csv
- **T044** — declared artifact(s) missing/empty/invalid: code/data_generation/health_check.py
- **T052** — declared artifact(s) missing/empty/invalid: tests/test_latency_output.py
- **T054** — declared artifact(s) missing/empty/invalid: tests/test_final_report.py, data/results/final_report.md
- **T058** — declared artifact(s) missing/empty/invalid: docs/data_generation.md
- **T060** — declared artifact(s) missing/empty/invalid: docs/limitations.md, docs/data_generation.md
