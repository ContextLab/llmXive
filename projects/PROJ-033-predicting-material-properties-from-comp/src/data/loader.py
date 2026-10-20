"""
Chunked dataset loader for materials properties.

Reads a CSV file in chunks (<= 5,000 rows via ``pandas.read_csv(...,
chunksize=5000)``), validates each row against the dataset contract
(``contracts/materials_dataset.schema.yaml``), removes rows with missing
required fields, drops duplicate ``material_id`` entries (keeping the
first occurrence globally), skips materials whose chemical formula
contains unknown elements (logging a warning), filters outliers using
the 1.5 x IQR rule for ``band_gap`` and ``hardness`` (logging the drop
count), and writes the cleaned data to the specified output path.

Zero-band-gap metals (band_gap == 0) are explicitly RETAINED – they are
valid regression targets, not missing data.  No synthetic imputation is
ever performed.

Peak RAM usage is monitored via ``psutil`` and asserted to remain
below 6 GB (FR-001).  A machine-readable summary of the run (drop
counts, peak RAM, checksum of the source file) is written to
``data/results/loader_report.json`` so that durable evidence of the
ingestion step survives outside the git-ignored ``data/processed``
cache.
"""

import argparse
import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Set

import pandas as pd
import psutil
import yaml
from jsonschema import ValidationError, validate

from llmxive_toolkit import paths

# -------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------
CHUNK_SIZE = 5_000
RAM_LIMIT_BYTES = 6 * 1024 ** 3  # 6 GB (FR-001)

REQUIRED_COLUMNS = [
    "material_id",
    "formula",
    "band_gap",
    "hardness",
    "crystal_system",
]

# -------------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------------
log = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Schema handling
# -------------------------------------------------------------------------
def load_schema() -> dict:
    """Load the JSON-Schema for the materials dataset."""
    schema_path = (
        Path(__file__).resolve().parents[2]
        / "contracts"
        / "materials_dataset.schema.yaml"
    )
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _to_native(value):
    """Convert numpy scalar types to native Python types so that
    ``jsonschema`` type checks behave deterministically."""
    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, AttributeError):
            return value
    return value

def validate_row(row: dict, schema: dict) -> bool:
    """Validate a single row against the contract schema.

    Returns ``True`` when the row conforms.  Rows containing NaN in a
    numeric field fail the ``minimum: 0`` check and are rejected (no
    imputation is attempted).
    """
    instance = {k: _to_native(v) for k, v in row.items()}
    try:
        validate(instance=instance, schema=schema)
    except ValidationError as e:
        log.warning(
            "Row failed schema validation (material_id=%s): %s",
            instance.get("material_id", "<unknown>"),
            e.message,
        )
        return False
    return True

# -------------------------------------------------------------------------
# Element-lookup utilities
# -------------------------------------------------------------------------
# Full list of known element symbols (1-118).  Keeping it local avoids a
# heavy dependency for the loader's skip-and-warn path.
_KNOWN_ELEMENTS: Set[str] = {
    "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne",
    "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar",
    "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
    "Ga", "Ge", "As", "Se", "Br", "Kr",
    "Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd",
    "In", "Sn", "Sb", "Te", "I", "Xe",
    "Cs", "Ba", "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy",
    "Ho", "Er", "Tm", "Yb", "Lu",
    "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg",
    "Tl", "Pb", "Bi", "Po", "At", "Rn",
    "Fr", "Ra", "Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf",
    "Es", "Fm", "Md", "No", "Lr",
    "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn", "Fl", "Lv", "Ts", "Og",
}

def _extract_elements(formula: str) -> Set[str]:
    """
    Very simple element extractor: finds all capital-letter sequences
    possibly followed by a lowercase letter.  This is sufficient for the
    unit-test fixtures and for most well-formed inorganic formulas.
    """
    return set(re.findall(r"[A-Z][a-z]?", str(formula)))

def is_known_formula(formula: str) -> bool:
    """
    Return ``True`` if the chemical formula can be parsed and all
    elements are known.  Uses ``pymatgen.Composition`` when available;
    otherwise falls back to a lightweight regex-based check against a
    hard-coded element list.
    """
    try:
        from pymatgen.core import Composition  # type: ignore

        try:
            comp = Composition(str(formula))
        except Exception:
            # Unparseable formula -> treat as unknown
            log.warning("Unparseable formula '%s'", formula)
            return False
        elements = {el.symbol for el in comp.elements}
    except ImportError:
        elements = _extract_elements(formula)

    unknown = elements - _KNOWN_ELEMENTS
    if unknown:
        log.warning(
            "Unknown element(s) %s in formula '%s' – skipping material",
            sorted(unknown),
            formula,
        )
        return False
    return True

def iqr_filter(df: pd.DataFrame, column: str) -> pd.Series:
    """
    Return a boolean mask indicating rows that are *within* the
    1.5 x IQR bounds for ``column``.
    """
    q1, q3 = df[column].quantile([0.25, 0.75])
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return df[column].between(lower, upper, inclusive="both")

def _sha256(path: Path) -> str:
    """Memory-efficient SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

# -------------------------------------------------------------------------
# Main loader
# -------------------------------------------------------------------------
def load_and_clean(
    input_path: Path,
    output_path: Path,
    report_path: Optional[Path] = None,
) -> dict:
    """
    Load ``input_path`` in chunks, clean the data, write the result to
    ``output_path`` and (optionally) a run summary to ``report_path``.

    Returns a summary dict with drop counts and peak RAM usage.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.is_file():
        raise FileNotFoundError(
            f"Input dataset not found at {input_path}. A verified open "
            "dataset with columns material_id, formula, band_gap, "
            "hardness, crystal_system must be supplied (see "
            "contracts/materials_dataset.schema.yaml)."
        )

    # Verify required columns exist – fail loudly, never impute.
    sample = pd.read_csv(input_path, nrows=0)
    missing = set(REQUIRED_COLUMNS) - set(sample.columns)
    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)} – the dataset "
            "contract requires material_id, formula, band_gap, hardness "
          "and crystal_system. No synthetic imputation is performed."
        )

    schema = load_schema()
    seen_ids: Set[str] = set()
    cleaned_chunks = []
    peak_ram = 0

    total_rows_read = 0
    total_dropped_missing = 0
    total_dropped_duplicate = 0
    total_dropped_schema = 0
    total_dropped_unknown = 0

    for chunk_idx, chunk in enumerate(
        pd.read_csv(input_path, chunksize=CHUNK_SIZE)
    ):
        log.info(
            "Processing chunk %d (rows: %d)", chunk_idx + 1, len(chunk)
        )
        total_rows_read += len(chunk)

        # Track RAM usage (FR-001)
        current_ram = psutil.Process().memory_info().rss
        peak_ram = max(peak_ram, current_ram)

        # -------------------------------------------------------------
        # 1. Drop rows with any missing required field
        # -------------------------------------------------------------
        before_missing = len(chunk)
        chunk = chunk.dropna(subset=REQUIRED_COLUMNS)
        dropped_missing = before_missing - len(chunk)
        total_dropped_missing += dropped_missing
        if dropped_missing:
            log.info(
                "Chunk %d: dropped %d rows with missing required fields",
                chunk_idx + 1,
                dropped_missing,
            )

        # -------------------------------------------------------------
        # 2. Drop duplicate material_id entries (keep first)
        #    a) intra-chunk duplicates
        #    b) duplicates seen in earlier chunks
        # -------------------------------------------------------------
        before_dup = len(chunk)
        chunk = chunk.drop_duplicates(subset="material_id", keep="first")
        is_new = ~chunk["material_id"].isin(seen_ids)
        inter_dup = int((~is_new).sum())
        if inter_dup:
            log.info(
                "Chunk %d: dropped %d duplicate material_id rows "
                "(across chunks)",
                chunk_idx + 1,
                inter_dup,
            )
        chunk = chunk[is_new]
        seen_ids.update(chunk["material_id"].tolist())
        total_dropped_duplicate += before_dup - len(chunk)

        # -------------------------------------------------------------
        # 3. Validate each row against the contract schema
        # -------------------------------------------------------------
        records = chunk.to_dict("records")
        keep_positions = [
            i for i, rec in enumerate(records) if validate_row(rec, schema)
        ]
        dropped_schema = len(records) - len(keep_positions)
        total_dropped_schema += dropped_schema
        if dropped_schema:
            log.info(
                "Chunk %d: dropped %d rows failing schema validation",
                chunk_idx + 1,
                dropped_schema,
            )
        chunk = chunk.iloc[keep_positions]

        # -------------------------------------------------------------
        # 4. Skip materials containing unknown elements (warn + skip)
        #    Zero-band-gap metals are retained (band_gap == 0 is valid).
        # -------------------------------------------------------------
        known_mask = chunk["formula"].apply(is_known_formula)
        unknown_mask = ~known_mask
        total_dropped_unknown += int(unknown_mask.sum())
        if unknown_mask.any():
            log.warning(
                "Chunk %d: skipping %d rows with unknown elements",
                chunk_idx + 1,
                int(unknown_mask.sum()),
            )
        chunk = chunk[known_mask]

        cleaned_chunks.append(chunk)

    # Concatenate all cleaned chunks
    if cleaned_chunks:
        cleaned_df = pd.concat(cleaned_chunks, ignore_index=True)
    else:
        cleaned_df = pd.DataFrame(columns=REQUIRED_COLUMNS)

    # -------------------------------------------------------------
    # 5. Outlier removal – 1.5 x IQR rule on band_gap and hardness,
    #    applied to the full concatenated dataset.
    # -------------------------------------------------------------
    total_dropped_outlier = 0
    if len(cleaned_df) > 0:
        mask_bg = iqr_filter(cleaned_df, "band_gap")
        mask_h = iqr_filter(cleaned_df, "hardness")
        outlier_mask = mask_bg & mask_h
        total_dropped_outlier = len(cleaned_df) - int(outlier_mask.sum())
        if total_dropped_outlier:
            log.info(
                "Outlier removal: dropped %d rows (1.5 x IQR rule on "
                "band_gap/hardness) across the full dataset",
                total_dropped_outlier,
            )
        cleaned_df = cleaned_df[outlier_mask]
    else:
        log.warning(
            "No rows survived cleaning – outlier filter skipped"
        )

    # -------------------------------------------------------------
    # RAM assertion (FR-001)
    # -------------------------------------------------------------
    if peak_ram > RAM_LIMIT_BYTES:
        raise AssertionError(
            f"Peak RAM usage {peak_ram / (1024 ** 3):.2f} GB exceeds "
            "the 6 GB limit (FR-001)"
        )
    log.info(
        "Peak RAM usage during loading: %.3f GB (limit 6 GB)",
        peak_ram / (1024 ** 3),
    )

    # Write cleaned data
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned_df.to_csv(output_path, index=False)
    log.info("Cleaned data written to %s (%d rows)", output_path, len(cleaned_df))

    summary = {
        "input_file": str(input_path),
        "input_sha256": _sha256(input_path),
        "output_file": str(output_path),
        "rows_read": total_rows_read,
        "rows_kept": len(cleaned_df),
        "dropped_missing_required": total_dropped_missing,
        "dropped_duplicate_material_id": total_dropped_duplicate,
        "dropped_schema_invalid": total_dropped_schema,
        "dropped_unknown_element": total_dropped_unknown,
        "dropped_outlier_iqr": total_dropped_outlier,
        "peak_ram_bytes": peak_ram,
        "ram_limit_bytes": RAM_LIMIT_BYTES,
        "ram_within_limit": peak_ram <= RAM_LIMIT_BYTES,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    log.info(
        "Loader summary – read: %d, missing: %d, duplicate: %d, "
        "schema-invalid: %d, unknown-elem: %d, outlier: %d, kept: %d",
        total_rows_read,
        total_dropped_missing,
        total_dropped_duplicate,
        total_dropped_schema,
        total_dropped_unknown,
        total_dropped_outlier,
        len(cleaned_df),
    )

    # Durable run evidence outside the git-ignored data caches
    if report_path is not None:
        report_path = Path(report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        log.info("Loader report written to %s", report_path)

    return summary

# -------------------------------------------------------------------------
# CLI entry point
# -------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chunked loader for materials dataset"
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to the raw CSV dataset (must conform to contract)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Path where the cleaned CSV will be written",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("data/results/loader_report.json"),
        help="Path for the JSON run summary (drop counts, peak RAM)",
    )
    return parser.parse_args()

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    args = parse_args()

    def _resolve(p: Path) -> Path:
        return p if p.is_absolute() else (paths.root / p)

    load_and_clean(
        _resolve(args.input),
        _resolve(args.out),
        _resolve(args.report),
    )

if __name__ == "__main__":
    main()
