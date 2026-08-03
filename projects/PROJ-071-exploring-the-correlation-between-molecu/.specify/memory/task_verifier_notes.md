# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T015** — The `descriptors.py` file does not catch `rdkit.Chem.rdchem.AtomValenceException` specifically, nor does it call `log_error_to_file` when such an exception occurs, and there is no code that generates or passes a `source_hash`. Consequently no `data/processed/excluded_molecules.csv` was created, so the required error‑logging artifact is missing.
