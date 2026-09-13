# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T039** — The required `data/raw/species_list.txt` file is absent, so the code cannot perform the mandated validation. Moreover, `code/data_loader.py` only checks that each entry has non‑empty NCBI and KEGG fields; it does not enforce a unique 1:1 mapping or detect ambiguous/missing IDs, contrary to the task specification.
