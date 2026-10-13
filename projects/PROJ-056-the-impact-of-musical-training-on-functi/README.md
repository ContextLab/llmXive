# The Impact of Musical Training on Functional Connectivity in Adolescent Brains

## Project Overview

This repository implements a reproducible pipeline to investigate how musical training during adolescence influences resting‑state functional connectivity, focusing on auditory, motor, and executive control networks. The pipeline supports:

- **Synthetic verification mode** for rapid code validation without real neuroimaging data.
- **Real‑data analysis mode** (when a verified ABCD or HCP‑Adolescents dataset is supplied) that performs preprocessing, connectivity computation, statistical testing, NBS analysis, correlation with years of training, and sensitivity analyses.

## Repository Structure

The top‑level directories are:

- `code/` – Source code for data handling, analysis, utilities, and the CLI entry point.
- `data/` – Raw and processed data (synthetic or real) as well as atlases and results.
- `tests/` – Unit, integration, and contract tests that validate each pipeline component.
- `specs/` – Feature specifications, plans, and contracts for data schemas.
- `figures/` – Generated figures from the analysis.
- `results/` – Summary CSVs and tables produced by the pipeline.
- `docs/` – Documentation files (e.g., this README and `quickstart.md`).

## Quick‑Start

See the detailed instructions in `quickstart.md`, which includes the exact command to run the verification mode:

```bash
python -m code.main --mode verification
```

## License

This project is licensed under the MIT License.