# The Impact of Musical Training on Functional Connectivity in Adolescent Brains

## Project Overview

This repository implements a reproducible pipeline for investigating how musical training during adolescence influences resting‑state functional connectivity, focusing on auditory, motor, and executive control networks. The codebase follows a modular structure that separates data handling, preprocessing, analysis, and visualization.

## Directory Structure

```
code/ # Python source code (modules, scripts, CLI entry‑point)
data/ # Raw, intermediate, and final data artifacts
 raw/ # Placeholder for real neuroimaging data or synthetic generators
 processed/ # Cleaned behavioral tables, connectivity matrices, results
 atlas/ # Schaefer 400‑parcel atlas CSV and checksum [UNRESOLVED-CLAIM: c_5d3fe699 — status=not_enough_info]
tests/ # Unit and integration test suite
 unit/ # Fast, isolated tests (e.g., quick‑start verification)
 integration/ # End‑to‑end pipeline tests
figures/ # Generated plots and visualisations
specs/ # Feature specifications and contracts
results/ # Final result tables and summary reports
```

The top‑level folders listed above are required by the test suite (`tests/unit/test_quickstart.py`).

## Quick‑Start

See the companion `quickstart.md` for detailed installation instructions and example commands.

## License

This project is released under the MIT License.
