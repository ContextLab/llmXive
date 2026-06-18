# Derivation Notes

## 1. Crossing Number Formula

The crossing number \(c(K)\) for a prime knot \(K\) is defined as the minimal number of crossings in any diagram of \(K\). This is taken directly from standard knot tables.

## 2. Braid Index Formula

The braid index \(b(K)\) is the minimal number of strands required to represent \(K\) as a closed braid. Values are sourced from the Knot Atlas.

## 3. Hyperbolic Volume Approximation

Hyperbolic volume \(V(K)\) is approximated using SnapPy's numerical integration of the hyperbolic structure, as described in:

> *J. R. Weeks, “SnapPea: a computer program for creating and studying hyperbolic 3‑manifolds,”* 1999.

All intermediate parameter values (tolerance, iteration limits) are recorded in the source code of `analysis/hyperbolic_volume_validation.py`.
