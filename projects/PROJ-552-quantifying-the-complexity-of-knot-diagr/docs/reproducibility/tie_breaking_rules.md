# Tie‑Breaking Rules

This document defines the deterministic tie‑breaking rules used when multiple
representations of a knot are available.

1. **Braid word** takes precedence over Dowker‑Thistlethwaite (DT) code.
2. If both are present, the lexicographically smaller string is chosen.
3. In the unlikely event of a perfect tie, the knot name is used as a final
 discriminator.

These rules are applied by the parser in `code/data/parser.py`.