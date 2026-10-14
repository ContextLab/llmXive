#!/usr/bin/env bash
set -e

# Run the minimal end‑to‑end pipeline on 50 clips
python -m src.pipeline.run_end_to_end --subset 50
