"""Curate a balanced 1 000‑prompt CSV.

This script reads the raw sample produced by ``code.src.data.download``,
selects 500 neutral prompts, generates 500 conflicting prompts using the
``conflict_generator`` helper, assigns deterministic UUIDs, and writes the
result to ``data/results/curated_prompts.csv`` with the required columns:

- prompt_id (UUID5 based on the prompt text)
- instruction_type (\"neutral\" or \"conflict\")
- prompt_text
- synthetic_score (placeholder value 0.5)
- human_score (null/NaN)
- checksum (SHA‑256 over the prompt text)

The script exits with status ``0`` on success and ``1`` on any error.
"""

from __future__ import annotations

import sys
import uuid

import pandas as pd
from llmxive_toolkit import get_logger, paths

from code.src.data.conflict_generator import generate_conflicting_prompts

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
RAW_PARQUET = paths.data("raw", "prompts_sample.parquet")
OUTPUT_CSV = paths.results("curated_prompts.csv")
# ----------------------------------------------------------------------


def _checksum_text(text: str) -> str:
    """Compute SHA‑256 checksum for a prompt string."""
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _assign_uuid(prompt_text: str) -> str:
    """Deterministic UUID5 based on the prompt text."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, prompt_text))


def main() -> int:
    try:
        # Load raw sample
        df_raw = pd.read_parquet(RAW_PARQUET, engine="fastparquet")
        log.info("Loaded %d raw prompts from %s", len(df_raw), RAW_PARQUET)

        # ------------------------------------------------------------------
        # 1️⃣ Select 500 neutral prompts (deterministic)
        # ------------------------------------------------------------------
        if len(df_raw) < 500:
            raise RuntimeError("Not enough raw prompts to select 500 neutral examples")

        neutral_df = df_raw.sample(n=500, random_state=42, replace=False).reset_index(drop=True)
        neutral_records = [
            {
                "prompt_text": str(row["edit_prompt"]).strip(),
                "instruction_type": "neutral",
                "checksum": _checksum_text(str(row["edit_prompt"]).strip()),
            }
            for _, row in neutral_df.iterrows()
        ]

        # ------------------------------------------------------------------
        # 2️⃣ Generate 500 conflicting prompts
        # ------------------------------------------------------------------
        conflict_records = generate_conflicting_prompts(df_raw, n=500, seed=123)

        # ------------------------------------------------------------------
        # 3️⃣ Combine, assign UUIDs and placeholder scores
        # ------------------------------------------------------------------
        all_records = neutral_records + conflict_records
        for rec in all_records:
            rec["prompt_id"] = _assign_uuid(rec["prompt_text"])
            rec["synthetic_score"] = 0.5  # placeholder synthetic feasibility
            rec["human_score"] = pd.NA

        curated_df = pd.DataFrame(all_records, columns=[
            "prompt_id",
            "instruction_type",
            "prompt_text",
            "synthetic_score",
            "human_score",
            "checksum",
        ])

        # ------------------------------------------------------------------
        # 4️⃣ Write CSV
        # ------------------------------------------------------------------
        OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
        curated_df.to_csv(OUTPUT_CSV, index=False)
        log.info("Wrote curated CSV with %d rows to %s", len(curated_df), OUTPUT_CSV)

        # Basic sanity check for the unit test
        if len(curated_df) != 1000:
            raise RuntimeError("Curated CSV does not contain exactly 1000 rows")

        return 0
    except Exception as exc:  # pragma: no cover – logged and propagated as non‑zero exit
        log.error("Curate step failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
