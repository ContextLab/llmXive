"""T034 — integration test: process_document repairs citation to the fill source.

Builds a small in-memory registry with a VERIFIED filled claim, then drives
process_document (or the citation-repair step directly) and asserts that the
rendered output cites OEIS A002863.

Fully offline — no network, no mock backend.
"""

from __future__ import annotations

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id
from llmxive.fill.citation_repair import repair_citation
from llmxive.fill.models import FillProvenance

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_EVIDENCE = {
    "filled": True,
    "fill": {
        "value": "9988",
        "source_id": "A002863",
        "url": "https://oeis.org/A002863",
        "quote": "13 9988",
        "channel": "oeis",
        "conflicts": [],
    },
}


def _make_verified_claim(
    canonical: str = "9988 prime knots at 13 crossings",
) -> Claim:
    kind = ClaimKind.NUMERIC
    cid = compute_claim_id(kind, canonical, "test-render-repair-ctx")
    return Claim(
        claim_id=cid,
        kind=kind,
        raw_text=canonical,
        canonical=canonical,
        context="test-render-repair-ctx",
        artifact_path="projects/PROJ-552/idea/foo.md",
        source_type="external",
        status=ClaimStatus.VERIFIED,
        resolved_value="9988",
        evidence=_EVIDENCE,
        resolver="fill:oeis",
        attempts=1,
        updated_at="2026-05-30T00:00:00Z",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFillRenderRepairsCitation:

    def test_repair_citation_adds_oeis_source(self):
        """repair_citation annotates the rendered value with OEIS A002863."""
        claim = _make_verified_claim()
        prov_d = claim.evidence["fill"]
        provenance = FillProvenance(
            value=prov_d["value"],
            source_id=prov_d["source_id"],
            url=prov_d["url"],
            quote=prov_d["quote"],
            channel=prov_d["channel"],
            conflicts=prov_d["conflicts"],
        )

        # Simulate rendered text containing the filled value but a stale citation.
        doc = "There are 9988 prime knots at 13 crossings (Smith et al. 2023)."
        repaired = repair_citation(doc, claim=claim, provenance=provenance)

        assert "A002863" in repaired, f"Expected OEIS A002863 in repaired text, got: {repaired!r}"
        assert "oeis.org" in repaired, f"Expected oeis.org URL in repaired text, got: {repaired!r}"

    def test_repair_citation_is_idempotent(self):
        """Calling repair_citation twice yields the same result."""
        claim = _make_verified_claim()
        prov_d = claim.evidence["fill"]
        provenance = FillProvenance(**prov_d)

        doc = "There are 9988 prime knots at 13 crossings."
        once = repair_citation(doc, claim=claim, provenance=provenance)
        twice = repair_citation(once, claim=claim, provenance=provenance)

        assert once == twice, "repair_citation is not idempotent"

    def test_repair_citation_leaves_unrelated_prose_untouched(self):
        """Text outside the adjacency window of the value is not modified."""
        claim = _make_verified_claim()
        prov_d = claim.evidence["fill"]
        provenance = FillProvenance(**prov_d)

        unrelated = "The sky is blue. " * 50
        doc = unrelated + "There are 9988 prime knots at 13 crossings." + unrelated
        repaired = repair_citation(doc, claim=claim, provenance=provenance)

        # The unrelated prose far before the value must survive intact.
        assert repaired.startswith("The sky is blue."), "Unrelated prose at start was modified"
        # The citation is inserted adjacent to the value (within the 200-char window),
        # so the trailing unrelated text (beyond the window) must still appear in the output.
        assert "The sky is blue." in repaired, "Unrelated prose was removed from output"
        # The citation was inserted somewhere in the document.
        assert "A002863" in repaired or "oeis.org" in repaired, (
            "Expected fill-source citation to be inserted"
        )

    def test_process_document_repairs_citation_for_filled_claim(self, tmp_path, monkeypatch):
        """process_document wires citation repair: the rendered output cites the fill source."""
        from llmxive.claims import service as svc
        from llmxive.state import claims as _claim_store

        canonical = "9988 prime knots at 13 crossings"
        claim = _make_verified_claim(canonical)
        project_id = "PROJ-552-repair-test"

        # Seed the registry with the VERIFIED filled claim.
        _claim_store.upsert(project_id, claim, repo_root=tmp_path)

        # Patch extract_claims in the service module's own namespace (it is imported
        # at module load time via `from llmxive.claims.extract import extract_claims`).
        def _fake_extract(text, **kwargs):
            return [claim]

        monkeypatch.setattr(svc, "extract_claims", _fake_extract)

        # Patch resolve in the service module's namespace to avoid the real resolver.
        def _fake_resolve(c, **kwargs):
            from llmxive.claims.models import Verdict
            return Verdict(
                status=ClaimStatus.VERIFIED,
                value="9988",
                evidence=_EVIDENCE,
                resolver="fill:oeis",
            )

        import llmxive.claims.resolve as resolve_mod
        monkeypatch.setattr(resolve_mod, "resolve", _fake_resolve)

        doc = f"There are {canonical} (Smith et al. 2023)."
        rendered, _claims_out, _gate = svc.process_document(
            doc,
            artifact_path="projects/PROJ-552/idea/foo.md",
            project_id=project_id,
            backend=None,
            model=None,
            repo_root=tmp_path,
        )

        assert "A002863" in rendered, (
            f"Expected OEIS A002863 citation in rendered output, got:\n{rendered!r}"
        )
        assert "oeis.org" in rendered, (
            f"Expected oeis.org URL in rendered output, got:\n{rendered!r}"
        )
