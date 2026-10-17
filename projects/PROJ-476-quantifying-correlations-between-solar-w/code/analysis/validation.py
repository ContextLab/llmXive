"""
Validation module for the solar wind composition vs geomagnetic indices study.

This script:
1. Loads the synchronized dataset (`data/processed/synced.csv`).
2. Subsets the data to the held‑out validation period (2018‑01‑01 to 2020‑12‑31).
3. Runs the same lagged correlation workflow as the full‑period analysis.
4. Flags rows where |pearson_r| > 0.5 **and** the Holm‑Bonferroni‑corrected p‑value
   is < 0.05, storing the flag in a column `validation_significant`.
5. Writes the results to `results/validation_correlations.csv`.
6. Generates a concise Markdown report `results/validation_report.md` that lists each
   flagged pair in the required format, or a default statement when no pair meets
   the criteria.
"""

import pandas as pd
from llmxive_toolkit import paths, get_logger

from code.analysis.correlation import (
    load_synced_data,
    run_correlation_analysis,
)
from code.config import TEST_START, TEST_END

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration – composition parameters, geomagnetic indices, lags
# ----------------------------------------------------------------------
COMPOSITION_PARAMS = ["proton_density", "temperature", "helium_abundance"]
GEOMAGNETIC_INDICES = ["Kp", "Dst"]
LAGS_HOURS = [0, 1, 2, 3, 6]

def _subset_validation_period(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only rows whose timestamp falls within the validation window.

    The timestamps in the synced CSV are timezone‑aware ISO‑8601 strings.
    ``TEST_START`` and ``TEST_END`` are defined in ``code.config`` as
    ``datetime`` objects (UTC).  Pandas comparison works directly with
    timezone‑aware ``datetime64[ns, tz]`` objects.
    """
    mask = (df["timestamp"] >= TEST_START) & (df["timestamp"] <= TEST_END)
    return df.loc[mask].copy()

def _add_validation_flag(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a Boolean column ``validation_significant`` that is True when
    both the absolute Pearson correlation exceeds 0.5 **and** the
    Holm‑Bonferroni‑corrected p‑value is below 0.05.
    """
    condition = (df["pearson_r"].abs() > 0.5) & (df["p_holm_bonferroni"] < 0.05)
    df = df.copy()
    df["validation_significant"] = condition
    return df

def _write_report(df: pd.DataFrame) -> None:
    """
    Write ``results/validation_report.md``.
    The report lists each flagged pair in the form:

        Helium abundance vs. Dst at 3 h lag: r = 0.54 (significant)

    If no rows are flagged, a default explanatory sentence is written.
    """
    report_path = paths.results("validation_report.md")
    flagged = df[df["validation_significant"]]

    with open(report_path, "w", encoding="utf-8") as f:
        if flagged.empty:
            f.write(
                "No composition parameter achieved the pre‑registered effect‑size threshold; composition does not add predictive value beyond dynamic pressure.\n"
            )
            log.info("Validation report written – no significant pairs.")
            return

        for _, row in flagged.iterrows():
            comp = row["composition_parameter"]
            idx = row["geomagnetic_index"]
            lag = int(row["lag_hours"])
            r = round(row["pearson_r"], 3)
            f.write(
                f"{comp.replace('_', ' ').title()} vs. {idx} at {lag} h lag: r = {r} (significant)\n"
            )
        log.info(f"Validation report written with {len(flagged)} significant rows.")

def main() -> None:
    """
    Entry point for the ``validate`` stage.
    """
    # 1. Load the full synced dataset
    synced_path = paths.data("processed", "synced.csv")
    df_full = load_synced_data(str(synced_path))

    # 2. Subset to the validation period
    df_val = _subset_validation_period(df_full)

    # 3. Run the full correlation workflow on the subset
    #    (the function writes the CSV, but we capture the returned DataFrame)
    results_df = run_correlation_analysis(
        df=df_val,
        composition_params=COMPOSITION_PARAMS,
        geomagnetic_indices=GEOMAGNETIC_INDICES,
        lags=LAGS_HOURS,
        output_path=str(paths.results("validation_correlations.csv")),
    )

    # 4. Add the validation significance flag
    results_df = _add_validation_flag(results_df)

    # 5. Write the (possibly updated) CSV – the DataFrame already
    #    includes the new column, but we rewrite to guarantee ordering.
    results_df.to_csv(
        paths.results("validation_correlations.csv"),
        index=False,
    )
    log.info(f"Validation correlations written to {paths.results('validation_correlations.csv')}")

    # 6. Produce the Markdown report
    _write_report(results_df)

if __name__ == "__main__":
    main()
