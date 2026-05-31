"""Real-call (LLMXIVE_REAL_TESTS=1) test for registrar-agnostic resolution (F-18).

The F-18 citation guard must NOT false-flag real references that are minted by a
registrar other than Crossref. The core defect it fixes: the guard previously
resolved DOIs via a Crossref-ONLY lookup, so a real Zenodo DOI
(``10.5281/zenodo.*``) or PsyArXiv/OSF DOI (``10.31234/*`` / ``10.31219/*``) —
minted via DataCite (Zenodo) or registered outside the Crossref journal corpus —
404s on Crossref and gets WRONGLY marked ``[UNVERIFIED]``.

The fix resolves every DOI through ``https://doi.org/<doi>`` (the DOI proxy's own
redirect), which is registrar-agnostic and works for Crossref, DataCite, mEDRA,
etc. This test proves, with REAL HTTP, that:

* a real, currently-live identifier from EACH service resolves PRESENT
  (``resolved`` for 2xx/3xx, or ``present_ambiguous`` for a real paywalled host
  answering 403 after a redirect — both mean "the reference EXISTS"); and
* a fabricated DOI, a fabricated URL, and the malformed ``arXiv:2402.13`` are
  FLAGGED ``[UNVERIFIED]``.

Every identifier below was confirmed live (HTTP 200/403-after-redirect) with a
real call while writing this test (per the no-fabricated-references rule). No
mocks — gated behind LLMXIVE_REAL_TESTS=1 by the repo conftest.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from llmxive.agents.citation_guard import verify_and_clean
from llmxive.librarian.verify import resolve_reference

# --- real, currently-live identifiers (one per service) ---------------------
# Confirmed live at authoring time via doi.org / arxiv.org / direct HEAD.
#   - Zenodo (DataCite): https://zenodo.org/api/records?q=covid → real record DOI
#   - PsyArXiv / OSF: https://api.crossref.org/prefixes/<p>/works → real DOIs
#   - bioRxiv/medRxiv (10.1101, in Crossref): real preprint DOIs, paywalled host
#     answers 403 after redirect → present_ambiguous (PRESENT).
LIVE_PRESENT: list[tuple[str, str, str]] = [
    ("doi", "10.5281/zenodo.10576421", "zenodo (DataCite DOI)"),
    ("doi", "10.1101/2020.09.09.290601", "bioRxiv DOI"),
    ("doi", "10.1101/2020.05.06.20092999", "medRxiv DOI"),
    ("doi", "10.31234/osf.io/gnmsw", "PsyArXiv DOI"),
    ("doi", "10.31219/osf.io/38n7h", "OSF preprint DOI"),
    ("arxiv", "1706.03762", "arXiv id"),
    ("url", "https://github.com/ContextLab/llmXive", "live https URL"),
]

# Fabricated / malformed → must resolve UNREACHABLE (and be flagged).
FLAGGED: list[tuple[str, str, str]] = [
    ("doi", "10.5281/zenodo.999999999999", "fabricated Zenodo DOI (404)"),
    ("url", "https://nope.example.invalid/does-not-exist", "fabricated URL (DNS fail)"),
    ("arxiv", "2402.13", "malformed arXiv id"),
]


@pytest.mark.parametrize("kind,value,label", LIVE_PRESENT, ids=[t[2] for t in LIVE_PRESENT])
def test_resolve_reference_present_for_every_service(kind: str, value: str, label: str) -> None:
    outcome = resolve_reference(kind, value)
    assert outcome.present, (
        f"{label} ({value}) should resolve PRESENT (registrar-agnostic), "
        f"got state={outcome.state!r} status={outcome.http_status} reason={outcome.reason!r}"
    )


@pytest.mark.parametrize("kind,value,label", FLAGGED, ids=[t[2] for t in FLAGGED])
def test_resolve_reference_unreachable_for_fakes(kind: str, value: str, label: str) -> None:
    outcome = resolve_reference(kind, value)
    assert not outcome.present, (
        f"{label} ({value}) must NOT resolve PRESENT; "
        f"got state={outcome.state!r} status={outcome.http_status}"
    )
    assert outcome.state == "unreachable"


def test_verify_and_clean_keeps_real_services_flags_fakes(tmp_path: Path) -> None:
    """End-to-end: a doc mixing one real ref from every service plus the fakes.

    Every real-service reference must survive untouched; every fabricated/malformed
    reference must be wrapped ``[UNRESOLVED-CLAIM: ...]`` with its claim text preserved.
    """
    doc = (
        "# Mixed-registrar references\n\n"
        "Zenodo dataset doi:10.5281/zenodo.10576421 underpins the analysis.\n"
        "A bioRxiv preprint doi:10.1101/2020.09.09.290601 reports related work,\n"
        "as does a medRxiv preprint doi:10.1101/2020.05.06.20092999.\n"
        "See the PsyArXiv preprint doi:10.31234/osf.io/gnmsw and the OSF\n"
        "preprint doi:10.31219/osf.io/38n7h.\n"
        "Transformers were introduced in arXiv:1706.03762.\n"
        "Code lives at https://github.com/ContextLab/llmXive.\n\n"
        "A fabricated dataset doi:10.5281/zenodo.999999999999 and a dead\n"
        "link [Broken](https://nope.example.invalid/does-not-exist) and a\n"
        "fabricated citation (Lee et al. 2024, arXiv:2402.13) must all be flagged.\n"
    )
    cleaned, report = verify_and_clean(
        doc,
        repo_root=tmp_path,
        project_id="PROJ-TEST-REGISTRAR",
        artifact_path="specs/001-x/spec.md",
    )

    # Every REAL-service reference survives untouched (NOT in flagged set).
    for present in (
        "10.5281/zenodo.10576421",
        "10.1101/2020.09.09.290601",
        "10.1101/2020.05.06.20092999",
        "10.31234/osf.io/gnmsw",
        "10.31219/osf.io/38n7h",
        "arXiv:1706.03762",
        "https://github.com/ContextLab/llmXive",
    ):
        assert present in cleaned, f"real reference {present!r} should be preserved"
    assert "10.5281/zenodo.10576421" not in report.flagged_values
    assert "10.1101/2020.09.09.290601" not in report.flagged_values
    assert "10.31234/osf.io/gnmsw" not in report.flagged_values
    assert "1706.03762" not in report.flagged_values

    # Every fabricated / malformed reference is flagged.
    assert "[UNRESOLVED-CLAIM: 10.5281/zenodo.999999999999" in cleaned, cleaned
    assert "[UNRESOLVED-CLAIM: arXiv:2402.13" in cleaned, cleaned
    assert "(https://nope.example.invalid/does-not-exist)" not in cleaned
    assert "2402.13" in report.flagged_values
    assert "10.5281/zenodo.999999999999" in report.flagged_values
    # Surrounding claim text preserved (no silent deletion).
    assert "underpins the analysis" in cleaned
    assert "must all be flagged" in cleaned
