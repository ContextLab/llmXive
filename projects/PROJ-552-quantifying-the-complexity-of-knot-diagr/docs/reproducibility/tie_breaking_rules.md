# Tie‑Breaking Rules

When multiple representations are available for a knot (e.g., several
braid words or DT codes), the following deterministic hierarchy is applied:

1. **Braid word** – preferred if present and syntactically valid.
2. **DT code** – used when a braid word is unavailable.
3. **Lexicographic order** – fallback to the smallest string representation.

These rules are implemented in `code/data/parser.py`.
