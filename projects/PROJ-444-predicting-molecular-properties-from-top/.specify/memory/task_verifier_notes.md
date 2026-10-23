# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — Checked `data/raw/lipophilicity.csv` and `data/checksums.txt`. The CSV exists and its SHA‑256 matches the entry in `checksums.txt`, but the file does not contain the original MoleculeNet Lipophilicity data – the “smiles” column holds stringified RDKit Mol objects instead of raw SMILES strings, indicating it is not the canonical dataset that should be downloaded. The task therefore lacks a correct raw dataset file.
