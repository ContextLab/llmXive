# Missing Data Handling

The dataset may contain missing entries for certain knot invariants. Missing values are flagged during the validation phase using `code/analysis/data_quality.py`. Rows with missing critical invariants are excluded from downstream metric calculations. Optional imputation strategies are documented in `docs/reproducibility/missing_data_flagging_guidelines.md`.

## Flagging

- Missing values are recorded in `data/processed/validation_flags.json` under the key `missing`.
- The flagging process adds a boolean column `has_missing` to the cleaned dataframe.

## Exclusion

- Any knot record with `has_missing == True` is omitted from composite metric computation and regression modeling.
- Users can override this behavior by setting `include_missing=True` in the analysis functions.

## Imputation (optional)

- Simple imputation (mean or median) can be performed using `code/analysis/_utils.py` functions `impute_mean` and `impute_median`.
- Advanced imputation is not currently supported.

