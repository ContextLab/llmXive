# Missing‑Data Flagging Guidelines

The **quantifying‑the‑complexity‑of‑knot‑diagr** project works with several large
datasets (raw knot atlas, cleaned CSVs, derived feature tables, etc.).  In many
steps of the pipeline data may be incomplete, corrupted, or inconsistent.  To
ensure reproducibility we explicitly **detect** and **flag** such problems so
that downstream analyses can either skip the affected records or handle them in
well‑defined ways.

## What constitutes “missing data”?

* **Absent fields** – a required key is not present in a JSON record or a CSV
  column is empty.
* **NaN / null values** – numeric fields contain `NaN` or string fields contain
  the literal `null`/empty string.
* **Unparsable entries** – a value cannot be cast to the expected type (e.g.
  a non‑numeric string where a float is required).
* **Mismatched schema** – the record fails validation against the JSON/YAML
  schemas in `specs/010-quantifying-the-complexity-of-knot-diagr/contracts/`.

## Flagging Mechanism

The module `code/analysis/data_quality.py` performs a pass over each dataset and
produces a **validation flag** JSON object for every record that exhibits any of
the above issues.  The flag schema is defined in
`specs/010-quantifying-the-complexity-of-knot-diagr/contracts/validation-flag.schema.yaml`
and includes:

```yaml
record_id: string               # Unique identifier of the record (e.g., Knot ID)
issues:
  - type: string               # Short code, e.g., "MISSING_FIELD"
    description: string        # Human‑readable explanation
    field: string              # The field that is problematic (optional)
```

All flags are aggregated into `data/processed/validation_flags.json`.  The file
is version‑controlled and a checksum is recorded in `data/checksums.json`.

## How downstream code should react

* **Filtering** – Analyses that require complete records should load the flag file
  and drop any record whose `record_id` appears.
* **Imputation** – For metrics where reasonable defaults exist (e.g., missing
  crossing number can be set to the median of the cohort), the flag provides the
  field name so that imputation logic can target only those entries.
* **Reporting** – The `code/analysis/data_quality_report.py` script renders a
  summary table (counts per issue type) that is included in the final
  reproducibility report (`docs/reproducibility/data_quality_report.md`).

## Auditing the flagging process

1. **Run the validator** – `python -m code.analysis.data_quality` writes the flag
   file and prints a concise summary to stdout.
2. **Check checksums** – `code/reproducibility/checksums.py` ensures the flag file
   matches the recorded SHA‑256 hash.
3. **Review the log** – Any unexpected failures are logged in
   `docs/reproducibility/logs/reproducibility.log`.

By following these conventions the project maintains a clear audit trail of
where data were incomplete and how those cases were handled, satisfying both
internal quality standards and external reproducibility expectations.
