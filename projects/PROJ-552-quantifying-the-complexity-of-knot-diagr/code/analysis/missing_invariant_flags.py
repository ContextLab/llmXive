"""
Missing Invariant Flags
=======================
Defines flags for invariants that could not be computed for a knot.

These flags are distinct from general data quality flags and are used to
record cases where a specific invariant is uncomputable due to missing data
or algorithmic limitations, satisfying functional requirements FR‑002 and
FR‑009.
"""

missing_invariant_flags = {
    "uncomputable_hyperbolic_volume": "Hyperbolic volume could not be computed",
    "uncomputable_unknotting_number": "Unknotting number could not be computed",
    # Add additional missing invariant flags as needed.
}

