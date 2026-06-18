# Checksum Manifest Policy

For each data directory, a single authoritative checksum manifest must be provided.
The project adopts `checksums.sha256` as the sole source of truth. The previously
included `checksums.csv` and `checksums.json` files are deprecated and may be
removed in future releases. Scripts and documentation should reference only the
SHA‑256 manifest.

This policy aligns with Principle III (no in‑place modification) by eliminating
redundant checksum representations and reducing the risk of divergence.
