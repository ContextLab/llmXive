# Derivation Notes

## Formula Citations with Page/Section References
- **Crossing Number Formula**: Adams, *The Knot Book*, p. 45, §2.1.
- **Braid Index Bound**: Birman & Menasco, *Studying Braids*, p. 112, §4.3.

## Step‑by‑Step Transformation Logic with Intermediate Values
1. Start with Dowker–Thistlethwaite code.
2. Convert to braid word using algorithm X (see Appendix A).
3. Compute minimal braid index via braid reduction (intermediate braid lengths recorded in `data/processed/braid_lengths.csv`).

## All Parameter Values Used
- Maximum back‑off time for downloader: 32 s.
- Random seeds: see `random_seeds.md`.

## Justification for Non‑Standard Choices
- **Exponential Backoff** chosen to balance network load and retry robustness (FR‑008).
- **CSV over Parquet** for readability in exploratory analysis.
