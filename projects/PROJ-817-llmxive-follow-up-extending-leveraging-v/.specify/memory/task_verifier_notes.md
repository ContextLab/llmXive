# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The provided `code/src/data/download.py` streams **timbrooks/instructpix2pix-clip-filtered** instead of the required **timbrooks/instructpix2pix**, and writes rows with an `edit_prompt` field rather than a `prompt` field as the task specifies. Consequently the script does not fulfill the exact dataset and column requirements of T001.
- **T002** — The script writes the CSV to `results/curated_prompts.csv` (as shown by the execution log) while the task requires the file at `data/results/curated_prompts.csv`, which is missing. Moreover, the conflict generator merely concatenates two prompts with temporal phrasing and does not enforce antonymic attribute targets as the specification demands. Both issues must be fixed for the task to be considered complete.
