# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory tree, `__init__.py` files, or `.gitkeep` placeholders are provided as evidence; the required project structure and files are absent, so the task’s requirement is not demonstrably satisfied.
- **T026b** — No log file `logs/symbolic_verification.log` was presented, nor any excerpt showing its contents (“VERIFIED” or “FAILED”). Without the required artifact, we cannot confirm that a SymPy verification script was run or that it produced the mandated output. The implementer must supply the actual log file (non‑empty) containing the verification result.
- **T034d** — The `src/analysis/stats.py` file does not contain the required `validate_heavy_tailed_pareto(...)` function (it ends with unrelated utilities), and the expected output file `data/processed/heavy_tailed_results.json` is absent. Both the core function and the verification artifact are missing.
