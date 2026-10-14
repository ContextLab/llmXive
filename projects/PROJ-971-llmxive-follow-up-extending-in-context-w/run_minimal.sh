#!/usr/bin/env bash
# Minimal end‑to‑end pipeline for the Auto‑ICWM project.
# Generates 50 reproducible clips, extracts statistical descriptors,
# and prints a summary table.
set -e
# 1) Generate clips
python -m src.pipeline.generate_clips --num-clips 50
# 2) Extract descriptors (writes data/descriptors_subset.csv)
python -m src.pipeline.extract_descriptors
# 3) Run the end‑to‑end driver which prints a summary table
python -m src.pipeline.run_end_to_end