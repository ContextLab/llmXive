# Tie‑Breaking Rules for Knot Representation

When multiple representations of a knot are available, the following deterministic hierarchy is applied:

1. **Braid word** – Preferred if present.
2. **DT code** – Used when a braid word is unavailable.
3. **Lexicographically smallest string** – Applied when both braid word and DT code are missing.
4. **Minimal crossing representation** – As a final fallback, the representation with the fewest crossings is chosen.

This hierarchy is fully documented here to guarantee reproducibility of representation choices.
