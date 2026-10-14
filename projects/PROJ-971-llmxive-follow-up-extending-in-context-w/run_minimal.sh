#!/usr/bin/env bash
set -e

# Step 1: Generate reproducible interaction clips (default 50).
python -m src.pipeline.generate_clips

# Step 2: Extract latent statistical descriptors.
python -m src.pipeline.extract_descriptors

# Step 3: Run the end‑to‑end driver (prints a full summary table).
python -m src.pipeline.run_end_to_end
