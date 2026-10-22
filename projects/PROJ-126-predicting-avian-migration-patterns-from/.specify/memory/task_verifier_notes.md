# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `code/config.py` defines most required constants, but `DATA_ROOT` is set to an absolute path (`Path(__file__).parents[1] / "data"`) instead of the required literal `Path("../data")`. This does not meet the specification. The rest of the file and `run_pipeline.sh` are present and functional. Fix the `DATA_ROOT` definition to exactly `DATA_ROOT = Path("../data")`.
- **T002** — Requested task execution failed; rerun successfully: code/data_loader.py exit=1
