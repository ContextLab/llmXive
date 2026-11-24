"""
Knowledge Base construction and retrieval for context‑grounded prompting.

This module builds a static JSON knowledge base mapping (setting, culture)
pairs observed in the video metadata to simple social‑norm profiles.
Each profile is validated against the contract schema
`specs/001-llmxive-follow-up-extending-perception-o/contracts/context_profile.schema.yaml`.

The knowledge base is written to ``data/context/knowledge_base.json`` and a
coverage report is written to ``data/derived/context_coverage.json``.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Tuple

import yaml
import jsonschema

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
KB_JSON_PATH = paths.data("context", "knowledge_base.json")
COVERAGE_JSON_PATH = paths.data("derived", "context_coverage.json")
METADATA_JSONL_PATH = paths.data("raw", "video_metadata.jsonl")
SCHEMA_PATH = (
    paths.root
    / "specs"
    / "001-llmxive-follow-up-extending-perception-o"
    / "contracts"
    / "context_profile.schema.yaml"
)

# ----------------------------------------------------------------------
# Neutral (fallback) profile – must satisfy the schema
# ----------------------------------------------------------------------
NEUTRAL_PROFILE: Dict[str, object] = {
    "setting": "neutral",
    "culture": "neutral",
    "norms": [],
    "script": "No specific context is available; a generic neutral profile is used.",
}

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_schema() -> Dict:
    """Load the JSON‑Schema that defines a valid context profile."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    return schema

def _required_fields(schema: Dict) -> Tuple[str, ...]:
    """Return the tuple of required property names from the schema."""
    return tuple(schema.get("required", []))

def _generate_profile(setting: str, culture: str, schema: Dict) -> Dict:
    """
    Produce a profile dict that satisfies *schema* for the given setting/culture.
    Missing required keys are filled with simple placeholder content.
    """
    profile: Dict[str, object] = {}
    required = _required_fields(schema)

    # Populate known fields with sensible placeholders.
    if "setting" in required:
        profile["setting"] = setting
    if "culture" in required:
        profile["culture"] = culture
    if "norms" in required:
        # A single norm string that mentions both dimensions.
        profile["norms"] = [f"Norm for {setting} in {culture} culture."]
    if "script" in required:
        profile["script"] = f"Typical script for a {setting} scenario within {culture} culture."

    # Any additional required keys get a generic placeholder.
    for key in required:
        if key not in profile:
            profile[key] = "placeholder"

    return profile

def _load_metadata_records() -> Tuple[Dict, ...]:
    """Read the streamed JSON‑Lines metadata file and return a tuple of records."""
    if not METADATA_JSONL_PATH.is_file():
        raise FileNotFoundError(f"Metadata file not found at {METADATA_JSONL_PATH}")

    records = []
    with open(METADATA_JSONL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return tuple(records)

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def build_knowledge_base() -> None:
    """
    Construct ``knowledge_base.json`` from the video metadata.

    For every unique (setting, culture) pair observed in the metadata a
    profile is generated that satisfies the contract schema.  A neutral
    fallback profile is also stored under the key ``neutral|neutral``.
    A coverage report (percentage of records that have a *specific*
    profile, i.e. not the neutral fallback) is written to
    ``data/derived/context_coverage.json``.
    """
    schema = _load_schema()
    records = _load_metadata_records()

    # Aggregate unique (setting, culture) pairs.
    unique_pairs = set()
    for rec in records:
        setting = rec.get("setting")
        culture = rec.get("culture")
        if setting is None or culture is None:
            # Skip malformed records – they will be caught by the
            # dataset‑validation tests (T001).
            continue
        unique_pairs.add((setting, culture))

    # Build the knowledge‑base dictionary keyed by ``setting|culture``.
    kb: Dict[str, Dict] = {}
    for setting, culture in unique_pairs:
        key = f"{setting}|{culture}"
        kb[key] = _generate_profile(setting, culture, schema)

    # Insert the neutral fallback profile.
    kb["neutral|neutral"] = NEUTRAL_PROFILE

    # Validate every generated profile against the schema.
    for key, profile in kb.items():
        try:
            jsonschema.validate(instance=profile, schema=schema)
        except jsonschema.ValidationError as exc:
            log.error(f"Generated profile for key {key} failed validation: {exc}")
            raise

    # Write the knowledge base.
    with open(KB_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(kb, f, indent=2, ensure_ascii=False)
    log.info(f"Knowledge base written to {KB_JSON_PATH}")

    # ------------------------------------------------------------------
    # Coverage computation
    # ------------------------------------------------------------------
    total_records = len(records)
    matched_records = sum(
        1
        for rec in records
        if f"{rec.get('setting')}|{rec.get('culture')}" in kb
        and f"{rec.get('setting')}|{rec.get('culture')}" != "neutral|neutral"
    )
    coverage_percent = (matched_records / total_records * 100) if total_records else 0.0

    coverage_report = {
        "total_records": total_records,
        "matched_records": matched_records,
        "coverage_percent": round(coverage_percent, 2),
    }
    with open(COVERAGE_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(coverage_report, f, indent=2, ensure_ascii=False)
    log.info(f"Context‑coverage report written to {COVERAGE_JSON_PATH}")

def load_knowledge_base() -> Dict[Tuple[str, str], Dict]:
    """
    Load the JSON knowledge base and return a mapping keyed by the tuple
    ``(setting, culture)``.
    """
    if not KB_JSON_PATH.is_file():
        raise FileNotFoundError(f"Knowledge base not found at {KB_JSON_PATH}")

    with open(KB_JSON_PATH, "r", encoding="utf-8") as f:
        raw_kb: Dict[str, Dict] = json.load(f)

    kb: Dict[Tuple[str, str], Dict] = {}
    for key, profile in raw_kb.items():
        setting, culture = key.split("|", 1)
        kb[(setting, culture)] = profile
    return kb

def retrieve_profile(metadata: Dict) -> Dict:
    """
    Retrieve the context profile for a single video *metadata* record.

    If the (setting, culture) pair is not present in the knowledge base,
    the neutral fallback profile is returned and a warning is logged
    (fulfilling FR‑009).
    """
    setting = metadata.get("setting")
    culture = metadata.get("culture")
    if setting is None or culture is None:
        log.warning(
            "Metadata missing 'setting' or 'culture'; using neutral fallback profile."
        )
        return NEUTRAL_PROFILE

    kb = load_knowledge_base()
    key = (setting, culture)
    if key in kb:
        return kb[key]

    log.warning(
        f"No specific context profile for setting='{setting}', culture='{culture}'. "
        "Returning neutral fallback."
    )
    return NEUTRAL_PROFILE

def main() -> None:
    """Entry‑point for ``python -m code.src.context.knowledge_base``."""
    log.info("Building static context knowledge base …")
    build_knowledge_base()
    log.info("Knowledge‑base construction complete.")

if __name__ == "__main__":
    main()
