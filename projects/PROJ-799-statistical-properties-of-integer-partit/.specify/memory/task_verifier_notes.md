# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory tree or any files were presented as evidence; the required `projects/PROJ-799-statistical-properties-of-integer-partit/` hierarchy (code/, data/, tests/, docs/, state/) is missing from the provided artifacts.
- **T003a** — No `code/.flake8` file is present in the provided evidence, and there is no content shown that would constitute a flake8 configuration. The required linting configuration file is missing, so the task is not satisfied.
- **T003b** — No `code/.black` file is present in the provided artifact list; without the configuration file the requirement to create a Black formatter config is unmet. The implementer must add a non‑empty `code/.black` file containing valid Black settings.
- **T004** — The repository lacks the required `code/utils/primes.npy` file, and the provided `prime_sieve.py` does not contain any logic that generates the primes up to 50,000, saves them as a 1‑D `np.int32` array, computes its SHA‑256 hash, or writes the hash and a fresh timestamp into `state/projects/PROJ-799.yaml`. The YAML entry still has an empty checksum and an outdated timestamp.
