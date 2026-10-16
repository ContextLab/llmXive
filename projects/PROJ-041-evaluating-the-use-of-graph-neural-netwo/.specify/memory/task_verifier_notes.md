# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The core utilities exist, but several explicit requirements are unmet: `requirements.txt` does not pin Python 3.11 or torch-CPU, and omits `torch-geometric` entirely (it lists only 13 unpinned packages); `pyproject.toml` even declares `requires-python = ">=3.9"`. Additionally, `memory_monitor.run_with_limit` is a simulated stand-in — it never executes a function or performs any allocation, it merely compares the passed `limit_gb` number against the configured limit, so the verification requirement ("raises MemoryLimitError when a dummy allocation exceeds 7 GB") is not genuinely implemented. Fi
- **T002** — Requested task execution failed; rerun successfully: code/data/download_ctu13.py exit=1
