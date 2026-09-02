# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T072** — The required `data/raw/elemental_properties.csv` file is absent, so the descriptor calculator cannot look up element properties. Moreover, while the code logs warnings for missing elements, it does not implement logic to skip or exclude the entire composition entry from analysis as the task specifies. Both the missing data file and the incomplete exclusion behavior need to be addressed.
