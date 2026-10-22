#!/usr/bin/env bash
set -e
# Execute the download script with the required arguments
python code/download_encode.py \
    --cell-lines GM128*, K562, HMEC, IMR90, HepG2 \
    --output-dir data/raw