"""
Data ingestion script for the metallic glass CTE project.

This script performs the following steps:
1. Queries the Materials Project (MP) API for entries that contain a
   thermal expansion coefficient (CTE) and are flagged as amorphous or
   metallic glass.
2. Queries the public AFLOWlib REST API as a supplemental source.
3. Saves the raw JSON responses under ``data/raw/``.
4. Computes SHA‑256 checksums for each raw file and records them in
   ``data/checksums.txt``.
5. Extracts the required fields, applies amorphous filtering (primary
   ``material_type``/``description`` check with documented fall‑backs),
   and discards entries with missing CTE or with ``amorphous_flag=False``.
6. Computes the four compositional descriptors via
   ``features.descriptors.extract_descriptors`` and merges the source
   checksum into each row.
7. Writes the cleaned dataset to ``data/processed/clean_mg_data.parquet``.
8. Emits ``data/results/ingestion_stats.json`` (completeness ratio) and
   ``data/results/data_availability_report.json`` (per‑source statistics).
9. Logs a warning if the final metallic‑glass subset contains fewer than
   500 entries; aborts only when the subset is empty.

The script is deliberately strict: any failure to fetch real data raises
an exception (no synthetic fallback) in accordance with the project
constitution.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import pandas as pd
from pymatgen.ext.matproj import MPRester

from utils.config import get_env_var
from utils.io import setup_logging, compute_sha256, fail_loud_loader
from llmxive_toolkit import paths, get_logger

from features.descriptors import extract_descriptors

logger = get_logger(__name__)

# -------------------------------------------------------------------------
# Helper utilities
# -------------------------------------------------------------------------

def _save_json(data: Any, path: Path) -> None:
    """Write *data* as pretty‑printed JSON to *path*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2, sort_keys=True)

def _load_json(path: Path) -> Any:
    """Load JSON from *path*."""
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)

# -------------------------------------------------------------------------
# 1️⃣ Materials Project query
# -------------------------------------------------------------------------

def _query_materials_project(api_key: str) -> List[Dict[str, Any]]:
    """
    Query the Materials Project for entries that contain a thermal expansion
    coefficient. Returns a list of entry dictionaries.
    """
    logger.info("Querying Materials Project for metallic‑glass CTE entries.")
    with MPRester(api_key) as mpr:
        # The MP REST API does not expose a dedicated ``material_type`` field
        # for amorphous structures, but we can request all entries that have
        # a thermal_expansion_coefficient property and then filter locally.
        criteria = {"thermal_expansion_coefficient": {"$exists": True}}
        properties = [
            "material_id",
            "pretty_formula",
            "thermal_expansion_coefficient",
            "material_type",
            "structure",
            "tags",
            "spacegroup",
            "description",
            "thermo",
            "elasticity",
        ]
        entries = mpr.query(criteria=criteria, properties=properties)
        logger.info(f"Retrieved {len(entries)} raw MP entries.")
        return entries

# -------------------------------------------------------------------------
# 2️⃣ AFLOWlib query (public REST API)
# -------------------------------------------------------------------------

def _query_aflow() -> List[Dict[str, Any]]:
    """
    Query AFLOWlib for metallic‑glass thermal‑expansion data.
    The public endpoint returns a JSON list; we keep the response as‑is.
    """
    import requests

    logger.info("Querying AFLOWlib for metallic‑glass CTE entries.")
    # AFLOWlib's public API endpoint for property queries
    url = "https://aflowlib.org/rest/search"
    params = {
        "property": "thermal_expansion_coefficient",
        "keywords": "glass",
        "format": "json",
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        raise RuntimeError("AFLOWlib returned unexpected JSON structure.")
    logger.info(f"Retrieved {len(data)} raw AFLOW entries.")
    return data

# -------------------------------------------------------------------------
# 3️⃣ Amorphous detection (FR‑001)
# -------------------------------------------------------------------------

def _is_amorphous(entry: Dict[str, Any]) -> bool:
    """
    Primary check: ``material_type`` field for "amorphous" or "glass".
    Secondary check: ``description`` contains the word "glass".
    Documented fall‑backs:
    - ``tags`` list containing a glass‑related tag.
    - ``structure_type`` substring "amorphous".
    - Missing space‑group information.
    """
    # Primary metadata fields
    material_type = entry.get("material_type", "")
    if isinstance(material_type, str) and material_type.lower() in {"amorphous", "glass"}:
        return True

    # Description fallback
    description = entry.get("description", "")
    if isinstance(description, str) and "glass" in description.lower():
        return True

    # Documented fall‑backs
    tags = entry.get("tags", [])
    if isinstance(tags, list) and any("glass" in str(t).lower() for t in tags):
        return True

    structure_type = entry.get("structure_type", "")
    if isinstance(structure_type, str) and "amorphous" in structure_type.lower():
        return True

    # Missing space‑group is a heuristic for amorphous (no symmetry)
    if entry.get("spacegroup") is None:
        return True

    return False

# -------------------------------------------------------------------------
# 4️⃣ Entry normalisation & field extraction
# -------------------------------------------------------------------------

def _normalise_entry(
    entry: Dict[str, Any], source: str
) -> Optional[Dict[str, Any]]:
    """
    Pull the required fields from a raw entry and return a flat dictionary.
    Returns ``None`` when the entry does not meet the inclusion criteria.
    """
    # Amorphous flag
    amorphous_flag = _is_amorphous(entry)
    if not amorphous_flag:
        return None

    # CTE extraction – MP uses ``thermal_expansion_coefficient``,
    # AFLOW may use ``cte`` or similar; we try a few keys.
    cte = entry.get("thermal_expansion_coefficient")
    if cte is None:
        cte = entry.get("cte")
    if cte is None:
        # Some MP entries store the value inside a nested dict
        thermo = entry.get("thermo", {})
        cte = thermo.get("thermal_expansion_coefficient")
    if cte is None:
        return None  # discard entries without a CTE

    # Composition – prefer ``pretty_formula``; fall back to ``composition``.
    composition = entry.get("pretty_formula") or entry.get("composition")
    if not composition:
        return None

    material_id = entry.get("material_id") or entry.get("id") or "unknown"

    # Source method – MP entries are DFT; AFLOW may be experimental.
    source_method = entry.get("source_method", "DFT")
    if source_method not in {"DFT", "Experimental"}:
        source_method = "DFT"

    thermal_history = entry.get("thermal_history", "")

    return {
        "material_id": str(material_id),
        "composition": str(composition),
        "cte": float(cte),
        "source_method": source_method,
        "thermal_history": str(thermal_history),
        "amorphous_flag": True,
        "source": source,  # internal use only
    }

# -------------------------------------------------------------------------
# 5️⃣ Main orchestration
# -------------------------------------------------------------------------

@fail_loud_loader
def fetch_data() -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Orchestrates data fetching from MP, AFLOW, and (optionally) Zenodo.
    Returns a tuple ``(combined_dataframe, source)`` where *source* is the
    primary successful source identifier.
    """
    mp_key = get_env_var("MP_API_KEY")
    if not mp_key:
        raise RuntimeError("Environment variable MP_API_KEY is required.")

    # -----------------------------------------------------------------
    # Fetch MP data
    # -----------------------------------------------------------------
    mp_entries_raw = _query_materials_project(mp_key)
    mp_path = paths.data("raw", "mp_data.json")
    _save_json(mp_entries_raw, mp_path)

    # -----------------------------------------------------------------
    # Fetch AFLOW data (optional – warnings only)
    # -----------------------------------------------------------------
    try:
        aflow_entries_raw = _query_aflow()
        aflow_path = paths.data("raw", "aflow_data.json")
        _save_json(aflow_entries_raw, aflow_path)
    except Exception as e:
        logger.warning(f"AFLOWlib query failed: {e}")
        aflow_entries_raw = []
        aflow_path = None

    # -----------------------------------------------------------------
    # Compute checksums and write manifest
    # -----------------------------------------------------------------
    checksums: List[str] = []
    for p in [mp_path, aflow_path] if aflow_path else [mp_path]:
        checksum = compute_sha256(str(p))
        checksums.append(f"{p.name}: {checksum}")

    checksums_path = paths.data("checksums.txt")
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    checksums_path.write_text("\n".join(checksums), encoding="utf-8")
    logger.info(f"Checksums written to {checksums_path}")

    # -----------------------------------------------------------------
    # Normalise and combine entries
    # -----------------------------------------------------------------
    combined: List[Dict[str, Any]] = []
    for raw_entry in mp_entries_raw:
        norm = _normalise_entry(raw_entry, source="materials_project")
        if norm:
            combined.append(norm)
    for raw_entry in aflow_entries_raw:
        norm = _normalise_entry(raw_entry, source="aflowlib")
        if norm:
            combined.append(norm)

    if not combined:
        raise RuntimeError("No metallic‑glass entries with CTE were found after filtering.")

    # -----------------------------------------------------------------
    # Build DataFrame and compute descriptors
    # -----------------------------------------------------------------
    df = pd.DataFrame(combined)
    raw_counts = {
        "materials_project": len(mp_entries_raw),
        "aflowlib": len(aflow_entries_raw),
    }

    # Apply descriptor extraction
    descriptor_rows: List[Dict[str, Any]] = []
    for idx, row in df.iterrows():
        try:
            desc = extract_descriptors(row["composition"])
            descriptor_rows.append(desc)
        except Exception as e:
            logger.warning(f"Descriptor extraction failed for {row['composition']}: {e}")
            descriptor_rows.append(
                {
                    "weighted_mean_atomic_radius": None,
                    "electronegativity_variance": None,
                    "vec": None,
                    "atomic_size_coefficient_of_variation": None,
                }
            )
    desc_df = pd.DataFrame(descriptor_rows)
    df = pd.concat([df.reset_index(drop=True), desc_df], axis=1)

    # Merge checksum (use MP checksum for all rows coming from MP, etc.)
    checksum_map = {}
    if mp_path:
        checksum_map["materials_project"] = compute_sha256(str(mp_path))
    if aflow_path:
        checksum_map["aflowlib"] = compute_sha256(str(aflow_path))
    df["checksum"] = df["source"].map(checksum_map)

    # Drop the internal ``source`` column – not part of the schema
    df = df.drop(columns=["source"])

    # -----------------------------------------------------------------
    # Validation against schema
    # -----------------------------------------------------------------
    from features.dataset_models import validate_dataframe_schema

    if not validate_dataframe_schema(df):
        raise RuntimeError("Cleaned DataFrame does not conform to the dataset schema.")

    # -----------------------------------------------------------------
    # Persist cleaned data
    # -----------------------------------------------------------------
    processed_path = paths.data("processed", "clean_mg_data.parquet")
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(processed_path, index=False)
    logger.info(f"Cleaned dataset written to {processed_path}")

    # -----------------------------------------------------------------
    # Ingestion statistics
    # -----------------------------------------------------------------
    total_raw = sum(raw_counts.values())
    kept = len(df)
    ingestion_stats = {
        "total_raw_entries": total_raw,
        "entries_kept_after_filter": kept,
        "completeness_ratio": kept / total_raw if total_raw > 0 else 0.0,
    }
    stats_path = paths.results("ingestion_stats.json")
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    stats_path.write_text(json.dumps(ingestion_stats, indent=2), encoding="utf-8")
    logger.info(f"Ingestion stats written to {stats_path}")

    # -----------------------------------------------------------------
    # Data‑availability report (per source)
    # -----------------------------------------------------------------
    report = {}
    for src in ["materials_project", "aflowlib"]:
        raw = raw_counts.get(src, 0)
        post_filter = df[df["source_method"] == ("DFT" if src == "materials_project" else "Experimental")].shape[0]
        valid_cte = df[df["cte"].notna()].shape[0]
        report[src] = {
            "raw_hit_count": raw,
            "post_filter_count": post_filter,
            "valid_cte_count": valid_cte,
        }
    report_path = paths.results("data_availability_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    logger.info(f"Data‑availability report written to {report_path}")

    # -----------------------------------------------------------------
    # Graceful degradation warning
    # -----------------------------------------------------------------
    if kept == 0:
        raise RuntimeError("No valid metallic‑glass entries remain after filtering.")
    if kept < 500:
        logger.warning(
            f"Only {kept} metallic‑glass entries were collected (< 500). "
            "Continuing as per US‑1 scenario 1."
        )

    return df, "combined"

def main() -> None:
    """
    Entry point for the ingestion pipeline.
    """
    setup_logging()
    try:
        df, source = fetch_data()
        logger.info(f"Ingestion completed successfully (source={source}, rows={len(df)}).")
    except Exception as exc:
        logger.critical(f"Ingestion failed: {exc}")
        raise

if __name__ == "__main__":
    main()
