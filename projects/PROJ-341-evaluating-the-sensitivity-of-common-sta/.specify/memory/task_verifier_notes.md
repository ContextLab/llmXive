# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T036** — The provided `code/main.py` exists, but it only defines a `check_memory_limit` helper that is never invoked and does not implement any real memory‑optimisation strategies (e.g., streaming data, reducing in‑memory structures, explicit GC calls). The script still runs the full simulation unchanged, with default iteration counts, and offers no evidence that the simulation stays under 7 GB RAM. Consequently, the task of optimizing the file to guarantee <7 GB RAM usage is not fulfilled.
