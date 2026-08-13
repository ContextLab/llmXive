# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — No files or code were presented in `code/models/` defining the three required classes (CityBoundary, RasterCovariate, TemperatureRaster) or any schema validation logic. Without these artifacts, the task’s requirement is not satisfied. The next implementer must add the model definitions and validation code in the specified directory.
- **T008** — No `.env` file, loading code, or documentation was provided to show that environment variable management for Overpass/AWS API keys has been added. The required artifact (configuration and implementation of `.env` support) is missing.
- **T015** — No evidence of a GeoTIFF stack was provided; there is no listing or content showing files in `data/processed/`, nor any confirmation that aligned rasters were created. The required output is missing, so the task is not satisfied.
- **T015a** — No `data-model.md` file or its contents were provided; without the actual markdown document we cannot confirm that reprojection and resampling methods are documented as required. The task remains undone.
- **T021** — declared artifact(s) missing/empty/invalid: data/results/eda_report.md
- **T022** — No variogram or correlation heatmap images, code, or generated files are present; the implementer provided only a textual description without any concrete artifact demonstrating the required visualizations. The task therefore lacks the necessary output.
- **T032** — No code, data files, scripts, or generated outputs (e.g., raster GeoTIFFs, correlation matrices, model reports) were supplied for any of the three user stories, so the required artifacts do not exist to verify that the ingestion, EDA, and spatial modeling steps were implemented. The task therefore remains incomplete.
- **T035** — declared artifact(s) missing/empty/invalid: data/results/sensitivity_report.md
- **T033** — declared artifact(s) missing/empty/invalid: data/results/metrics.csv
- **T036a** — No updated README.md file was provided or shown, and there is no evidence of added CLI usage examples or installation instructions. The required artifact is missing, so the task is not satisfied.
- **T037a** — No linting or formatting artifacts (e.g., ruff/black run logs, diff reports, or updated files in the `code/` directory) are provided, nor any evidence that the tools were executed. Without such files or output, the requirement to run ruff and black across `code/` is not satisfied.
- **T037b** — No evidence (e.g., cleaned source files, linter reports, diff showing removed imports, or a summary of dead code eliminated) was provided to demonstrate that unused imports and dead code in the `code/` directory have been removed. The implementer’s claim cannot be verified without such artifacts.
