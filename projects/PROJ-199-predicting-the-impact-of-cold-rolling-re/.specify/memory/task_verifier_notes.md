# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of a `code/` directory is provided; the claim cannot be verified because the required artifact (the directory itself) is missing from the supplied evidence. The next implementer must create the `code/` folder in the repository so that `pathlib.Path(__file__).parent.joinpath('code').is_dir()` returns `True`.
- **T001b** — No evidence of a `data/` directory being present in the repository is provided, nor is there any code snippet showing the `pathlib.Path(__file__).parent.joinpath('data').is_dir()` check. The implementer must add the `data/` folder (even if empty) and include a verification step confirming its existence.
