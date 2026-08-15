# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T007` (rejected 1x): No files or code were presented in `code/models/` defining the three required classes (CityBoundary, RasterCovariate, TemperatureRaster) or any schema validation logic. Without these artifacts, the task’s requirement is not satisfied. The next implementer must add the model definitions and validation code in the specified directory.
- `T008` (rejected 1x): No `.env` file, loading code, or documentation was provided to show that environment variable management for Overpass/AWS API keys has been added. The required artifact (configuration and implementation of `.env` support) is missing.
- `T015` (rejected 1x): No evidence of a GeoTIFF stack was provided; there is no listing or content showing files in `data/processed/`, nor any confirmation that aligned rasters were created. The required output is missing, so the task is not satisfied.
- `T015a` (rejected 1x): No `data-model.md` file or its contents were provided; without the actual markdown document we cannot confirm that reprojection and resampling methods are documented as required. The task remains undone.
- `T022` (rejected 1x): No variogram or correlation heatmap images, code, or generated files are present; the implementer provided only a textual description without any concrete artifact demonstrating the required visualizations. The task therefore lacks the necessary output.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

