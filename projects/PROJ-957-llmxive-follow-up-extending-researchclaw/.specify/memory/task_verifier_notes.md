# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — The required `data/raw/checksum.txt` file does not exist, so the loader’s checksum output is missing. Without this file the task’s specification (writing the SHA‑256 checksum in plain text) is not satisfied. The implementer must add code that writes the checksum to `data/raw/checksum.txt` in the exact `sha256: <hex>` format and ensure the file is created.
