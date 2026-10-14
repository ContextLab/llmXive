# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The directory layout is only partially evidenced (code/, data/, tests/ exist, but docs/ and contracts/ are not confirmed), and `code/pyproject.toml` lists dependencies without any version pins ("pandas", "matplotlib", etc.), contradicting the requirement to install *pinned* dependencies. There is also no evidence of an actual install (e.g., the `docs/install_log.txt` the quickstart claims is written by `setup_project.py` is not present in the evidence), so the dependency installation claim is unverified. Fix: add version pins to `code/pyproject.toml`/`requirements.txt`, confirm `docs/` and `co
- **T002** — Requested task execution failed; rerun successfully: code/data/thin_slice.py exit=1
