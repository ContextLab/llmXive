"""
T017: Data export to data/raw/ and data/manifest.jsonl.

This script produces the real US1 export artifacts:
  - data/raw/chunk_*.jsonl : synthetic video frames with visual-only labels
  - data/manifest.jsonl    : per-chunk manifest entries with SHA-256 checksums

It drives the existing generator (src.data_synthesis.generator.generate_video_stream)
in CI mode (1 hour subset) so it completes within the runner budget, then writes
the manifest using the exporter's hashing utility (src.data_synthesis.exporter.compute_file_hash),
and verifies the exported volume via src.data_synthesis.verify_volume.

Run:  python code/src/data_synthesis/run_export.py
"""
import json
import os
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

# Make the project's code/ package tree importable regardless of cwd.
CODE_ROOT = paths.code()
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from src.data_synthesis.generator import (  # noqa: E402
    FRAME_RATE,
    TARGET_DURATION_SECONDS_CI,
    generate_video_stream,
)
from src.data_synthesis.exporter import compute_file_hash  # noqa: E402
from src.data_synthesis.verify_volume import (  # noqa: E402
    calculate_total_duration,
    load_manifest,
)

log = get_logger("T017-export")


def write_manifest(entries, manifest_path: Path) -> None:
    """Write one JSONL line per chunk with duration and SHA-256 checksum."""
    with open(manifest_path, "w", encoding="utf-8") as f:
        for entry in entries:
            record = dict(entry)
            record["duration_seconds"] = record["frame_count"] / FRAME_RATE
            chunk_file = Path(record["file_path"])
            if not chunk_file.exists():
                raise FileNotFoundError(
                    f"Exported chunk missing on disk: {chunk_file}"
                )
            record["sha256"] = compute_file_hash(chunk_file)
            record["data_source"] = "synthetic_generator"
            record["label_source"] = "visual_only"
            f.write(json.dumps(record) + "\n")
    log.info(f"Wrote {len(entries)} manifest entries to {manifest_path}")


def main() -> int:
    raw_dir = paths.data("raw")
    manifest_path = paths.data("manifest.jsonl")

    seed = int(os.getenv("DATA_SEED", "42"))
    is_ci = os.getenv("CI", "true").lower() != "false"

    # CI mode caps generation at the 1-hour subset (fits runner budget);
    # Non-CI mode would generate the full 50-hour dataset (FR-001).
    duration = TARGET_DURATION_SECONDS_CI if is_ci else 180000
    log.info(
        f"Exporting synthetic dataset: duration={duration}s seed={seed} "
        f"ci_mode={is_ci} -> {raw_dir}"
    )

    entries = generate_video_stream(
        duration_seconds=duration,
        output_dir=raw_dir,
        seed=seed,
        is_ci_mode=is_ci,
    )
    if not entries:
        raise RuntimeError("Generator produced no chunks; nothing to export.")

    write_manifest(entries, manifest_path)

    # Verify the exported volume using the project's own verifier (T013a).
    manifest_data = load_manifest(manifest_path)
    total_seconds = calculate_total_duration(manifest_data)
    total_frames = sum(e["frame_count"] for e in entries)
    log.info(
        f"Export verified: {len(entries)} chunks, {total_frames} frames, "
        f"{total_seconds:.2f} seconds of video."
    )
    if is_ci and total_seconds < TARGET_DURATION_SECONDS_CI - FRAME_RATE:
        raise RuntimeError(
            f"Exported volume {total_seconds}s below CI target "
            f"{TARGET_DURATION_SECONDS_CI}s"
        )

    print(
        f"T017 export complete: data/raw/ ({len(entries)} chunks, "
        f"{total_frames} frames, {total_seconds:.2f}s) and {manifest_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
