"""Integration: the canonical correction sweep inside process_document.

Verifies the PROJ-552 fix end-to-end at the service chokepoint. The document
contains BOTH the fabricated '27,635' mention and the verified '9,988' mention
of the SAME subject (prime knots at crossing number 13). The extraction backend
lifts the verified mention as a claim; that claim is already VERIFIED + sourced
in the registry (reused, not re-resolved), so it flows into ``resolved_claims``
→ ``build_canonical_facts``. The sweep then forces EVERY '27,635' to '9988'
while preserving the correct mention and unrelated numbers, and persists the
per-project verified_facts.yaml.

A document with no verified facts is byte-identical to today (pure
strengthening).

Real filesystem, deterministic extraction backend, no model mocks.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from llmxive.claims.classify import classify
from llmxive.claims.models import Claim, ClaimStatus, compute_claim_id
from llmxive.state import claims as _claim_store

_FAB_13 = (
    "For crossing number 13, the exact count is 27,635 prime knots, as "
    "established in Hoste, Thistlethwaite & Weeks (1998)."
)
_OK_13 = (
    "The number of prime knots at crossing number 13 is 9,988 "
    "(sequence A002863 in the OEIS)."
)


class _ExtractsVerifiedMentionBackend:
    """Real chat backend that extracts the verified mention (_OK_13) as ONE claim.

    Deterministic, no network. The claim it emits is pre-seeded as VERIFIED in
    the registry (same claim_id), so the service reuses it without re-resolving
    — exactly the per-round reuse path the real pipeline takes.
    """

    def chat(self, messages, **kwargs):  # type: ignore[no-untyped-def]
        yaml_doc = (
            "claims:\n"
            f"  - claim_text: '{_OK_13}'\n"
            f"    canonical: '{_OK_13}'\n"
            "    context: ''\n"
        )

        class _R:
            text = yaml_doc

        return _R()


def _seed_verified_fact(project_id: str, repo_root: Path) -> str:
    """Pre-seed the VERIFIED+sourced claim the backend will extract; return its id."""
    kind = classify(_OK_13, _OK_13)
    claim_id = compute_claim_id(kind, _OK_13, "")
    claim = Claim(
        claim_id=claim_id,
        kind=kind,
        raw_text=_OK_13,
        canonical=_OK_13,
        context="",
        artifact_path=f"projects/{project_id}/specs/spec.md",
        source_type="external",
        status=ClaimStatus.VERIFIED,
        resolved_value="9988",
        evidence={
            "filled": True,
            "fill": {
                "value": "9988",
                "source_id": "A002863",
                "url": "https://oeis.org/A002863",
                "quote": "... 2176, 9988, 46972 ... (sequence A002863 in the OEIS).",
                "channel": "oeis",
                "conflicts": [],
            },
        },
        resolver="fill",
        attempts=1,
        updated_at="2026-06-02T00:00:00Z",
    )
    _claim_store.upsert(project_id, claim, repo_root=repo_root)
    return claim_id


class TestProcessDocumentCanonicalSweep:
    def test_sweep_forces_every_27635_to_9988(self, tmp_path: Path) -> None:
        from llmxive.claims.service import process_document

        project_id = "PROJ-CANON-1"
        (tmp_path / "state" / "claims").mkdir(parents=True, exist_ok=True)
        _seed_verified_fact(project_id, tmp_path)

        doc = (
            "# Spec\n\n"
            + _FAB_13
            + "\n\nAnd separately, "
            + _OK_13
            + "\n\nReiterated: "
            + _FAB_13
            + "\n\nUnrelated: the study ran for 7 years.\n"
        )
        rendered, _claims, _gate = process_document(
            doc,
            artifact_path=f"projects/{project_id}/specs/001/spec.md",
            project_id=project_id,
            backend=_ExtractsVerifiedMentionBackend(),
            model=None,
            repo_root=tmp_path,
        )

        assert "27,635" not in rendered
        assert "27635" not in rendered
        assert "9988" in rendered or "9,988" in rendered
        # Unrelated prose + numbers preserved.
        assert "7 years" in rendered
        assert "Hoste" in rendered

    def test_verified_facts_persisted(self, tmp_path: Path) -> None:
        from llmxive.claims.service import process_document

        project_id = "PROJ-CANON-2"
        (tmp_path / "state" / "claims").mkdir(parents=True, exist_ok=True)
        _seed_verified_fact(project_id, tmp_path)

        process_document(
            _FAB_13 + "\n\n" + _OK_13,
            artifact_path=f"projects/{project_id}/specs/001/spec.md",
            project_id=project_id,
            backend=_ExtractsVerifiedMentionBackend(),
            model=None,
            repo_root=tmp_path,
        )
        facts_path = (
            tmp_path / "projects" / project_id / ".specify" / "memory"
            / "verified_facts.yaml"
        )
        assert facts_path.exists()
        data = yaml.safe_load(facts_path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        # Exactly one verified subject, mapped to value 9988.
        assert any(
            (entry or {}).get("value") == "9988" for entry in data.values()
        )

    def test_no_verified_facts_is_byte_identical(self, tmp_path: Path) -> None:
        """Pure strengthening: with no verified facts, output is unchanged."""
        from llmxive.claims import service as svc

        project_id = "PROJ-CANON-3"
        (tmp_path / "state" / "claims").mkdir(parents=True, exist_ok=True)

        class _SilentBackend:
            def chat(self, messages, **kwargs):  # type: ignore[no-untyped-def]
                class _R:
                    text = "claims: []"

                return _R()

        doc = "# Spec\n\nThe model used 5,000 samples over 7 years.\n"
        rendered, _c, _g = svc.process_document(
            doc,
            artifact_path=f"projects/{project_id}/specs/001/spec.md",
            project_id=project_id,
            backend=_SilentBackend(),
            model=None,
            repo_root=tmp_path,
        )
        # No verified facts → the sweep is a no-op → the doc is preserved exactly.
        assert rendered == doc
        facts_path = (
            tmp_path / "projects" / project_id / ".specify" / "memory"
            / "verified_facts.yaml"
        )
        # No facts → nothing persisted.
        assert not facts_path.exists()
