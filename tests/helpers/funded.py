"""Synthetic funded-provider fixtures (spec 027): fictional ``acme/...`` repo ids and
rating tables. These are test data, not LMArena numbers, and the ids are fictional so
the pinned-model detector never matches them.

``REASONING`` / ``CODING`` map a repo to ``(rating, rating_lower, rating_upper)``; a
row given as a single rating gets the bounds ``rating - 5`` / ``rating + 5``. Each
table holds 20 repos, so the cut-off indices are economy 9, balanced 5, strong 1,
strongest 0. ``REPO_D`` is deliberately absent from both tables (unscored).
"""

from __future__ import annotations

from datetime import date

PUBLISHED = date(2026, 11, 22)

REPO_A = "acme/alpha-large"
REPO_B = "acme/beta-mini"
REPO_C = "acme/gamma-vision"
REPO_D = "acme/delta-unscored"
REPO_E = "acme/gpt-oss-120b"   # family "gpt-oss", which is in the reviewed policy table
FILLERS = tuple(f"acme/filler-{i:02d}" for i in range(1, 17))

Triple = tuple[float, float, float]


def _band(rating: float) -> Triple:
    return (float(rating), float(rating) - 5.0, float(rating) + 5.0)


_F = FILLERS

REASONING: dict[str, Triple] = {
    REPO_A: _band(1400),
    REPO_E: (1390.0, 1380.0, 1400.0),
    _F[0]: _band(1376),
    _F[1]: _band(1360),
    _F[2]: _band(1350),
    REPO_C: _band(1340),
    _F[3]: _band(1330),
    _F[4]: _band(1320),
    _F[5]: _band(1310),
    REPO_B: _band(1300),
    _F[6]: _band(1290),
    **{_F[7 + i]: _band(1280 - 10 * i) for i in range(9)},          # F08..F16: 1280, 1270, ..., 1200
}

CODING: dict[str, Triple] = {
    REPO_B: _band(1500),
    REPO_A: _band(1480),
    **{_F[i]: _band(1460 - 10 * i) for i in range(16)},             # F01..F16: 1460, 1450, ..., 1310
    REPO_C: _band(1290),
    REPO_E: _band(1280),
}
