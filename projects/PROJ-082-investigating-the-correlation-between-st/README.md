# PROJ-082: Investigating the Correlation Between Structural Brain Connectivity and Individual Music Preferences

An automated scientific pipeline for systematic review and meta-analysis of brain connectivity and music preference studies.

## Features

- **Automated Data Extraction**: Parses CSV/JSON inputs, converts p-values/t-stats to effect sizes.
- **Quantitative Meta-Analysis**: Random-effects (DerSimonian-Laird) and Fixed-effects models.
- **Bias Detection**: Egger's regression test for publication bias.
- **Multiple Testing Correction**: Bonferroni adjustment for multiple tracts.
- **Narrative Synthesis**: Automatic pivot to qualitative analysis when data is insufficient (`N < 10`).
- **Visualization**: Forest plots, Funnel plots, and Correlation summaries.

## Quickstart

See `docs/quickstart.md` for detailed instructions on running the pipeline, handling data scarcity, and interpreting results.

## Project Structure

- `code/`: Source code for the pipeline.
- `data/raw/`: Input data (real or mock).
- `data/processed/`: Intermediate processed data.
- `data/derived/`: Final analysis results and plots.
- `docs/`: Documentation and paper drafts.

## Narrative Mode & Data Scarcity

This project implements a strict "Fail Loud" and "Pivot" protocol for data scarcity:

1. **Gatekeeping**: The `gatekeeper` module enforces a minimum threshold of `N >= 10` valid studies for quantitative analysis.
2. **Pivot Logic**: If `N < 10`, the pipeline **does not** run meta-analysis. Instead, it triggers the `narrative_engine` to produce a "Systematic Review of Absence" report.
3. **Output**:
 - `pivot_log.json`: Explicitly states the reason for the pivot (e.g., "N=5 < 10").
 - `narrative_summary.md`: A report stating "No Quantitative Evidence Found" if appropriate.
4. **Safety**: Forest plots, Egger's test, and Bonferroni correction are **skipped** in narrative mode to prevent invalid statistical inference.

**Warning**: Do not interpret quantitative metrics if `synthesis_mode` in `gate_result.json` is "narrative".

## Testing

Run unit and integration tests:

```bash
pytest tests/
```

## License

[License Information]