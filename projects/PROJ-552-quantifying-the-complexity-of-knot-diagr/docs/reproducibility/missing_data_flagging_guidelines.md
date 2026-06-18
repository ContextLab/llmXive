# Missing Data Flagging Guidelines

When processing the knot dataset, some records may have missing fields (e.g., missing crossing number, braid word, or invariant values). The validation pipeline flags such records and records the issues in `data/processed/validation_flags.json`.

## Types of Missing Data

- **Critical fields**: Required for downstream analysis (e.g., `id`, `crossing_number`). Missing these renders the record unusable and the validator marks the record as **invalid**.
- **Optional fields**: May be absent without breaking analysis (e.g., certain derived invariants). These are flagged as **warnings**.

## Flagging Mechanism

The validator writes entries to `validation_flags.json` with the following schema:

```json
{
  "record_id": "string",
  "field": "string",
  "issue": "missing",
  "severity": "error | warning"
}
```

- `severity` **error**: the record is excluded from quantitative analyses.
- `severity` **warning**: the record is kept but the missing information is noted.

## How to Inspect Flags

```bash
python -m code.analysis.validation_status_generator --flags data/processed/validation_flags.json
```

The command prints a summary table of missing‑data issues.

## Recommended Actions

1. **Review critical errors** and consider discarding or manually completing those records.
2. **Investigate warnings** to see if the missing optional data can be computed or retrieved.
3. **Update the raw dataset** and re‑run the validation pipeline to clear resolved flags.

By following these guidelines, researchers can maintain a high‑quality dataset and ensure reproducibility of downstream analyses.

