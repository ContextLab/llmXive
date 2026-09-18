# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — The required output file `data/processed/metadata.csv` does not exist, and the `save_metadata_csv` implementation only writes whatever fields are present in the input list— it never adds the required `wavelength_range` column nor ensures the full set of columns (planet_name, temperature, metallicity, snr, resolution, planet_category, instrument, wavelength_range). Consequently the deliverable is missing and the function does not meet the task specification.
