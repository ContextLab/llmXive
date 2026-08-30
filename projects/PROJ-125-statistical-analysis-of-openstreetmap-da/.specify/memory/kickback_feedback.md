# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003` (rejected 1x): No `.gitignore` or `.env.example` files are present in the provided evidence; the implementer did not supply the required files, so the task is not satisfied.
- `T015a` (rejected 1x): No evidence was presented showing that a `data-model.md` file exists in `specs/001-urban-heat-osm/`, nor any content indicating it has been updated with the required reprojection/resampling details. The implementer must provide the actual file and its updated sections.
- `T007` (rejected 1x): No `code/models/` directory or Python files defining `CityBoundary`, `RasterCovariate`, or `TemperatureRaster` with schema validation were presented. The claim lacks any concrete code artifacts, so the required data models are missing.
- `T008` (rejected 1x): No code, configuration file, or documentation showing that a `.env` system for managing Overpass and AWS API keys has been added to the project is present. The required artifact (e.g., a `.env.example` file, loading logic in the codebase, and instructions for using it) is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

