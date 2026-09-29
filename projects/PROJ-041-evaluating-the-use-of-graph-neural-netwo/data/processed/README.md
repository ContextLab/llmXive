# Data Directory

This directory contains processed data artifacts.

## Artifacts

- `graph_{scenario}_raw.graphml`: Raw graph constructed from netflow data.
- `graph_{scenario}_lcc.graphml`: Largest Connected Component extracted graph.
- `graph_{scenario}_subsampled.graphml`: Final subsampled graph.
- `*.hash`: SHA256 hash files for artifact verification.

## Note

The CTU dataset download (T007a) places raw data in `data/raw/`.
The `data/processed/` directory is for graphs and splits generated from this raw data.