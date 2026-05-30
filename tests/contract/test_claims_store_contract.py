"""T005 — contract tests for state/claims.py (spec 016 foundational)."""

from __future__ import annotations

from pathlib import Path

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id
from llmxive.state import claims as claims_store


def _make_claim(kind: ClaimKind = ClaimKind.NUMERIC, canonical: str = "x=1", context: str = "ctx") -> Claim:
    cid = compute_claim_id(kind, canonical, context)
    return Claim(
        claim_id=cid,
        kind=kind,
        raw_text="raw text here",
        canonical=canonical,
        context=context,
        artifact_path="projects/PROJ-TEST/specs/spec.md",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value=None,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="2026-05-30T00:00:00Z",
    )


class TestClaimsStoreMissingFile:
    def test_load_missing_returns_empty(self, tmp_path: Path):
        result = claims_store.load("PROJ-MISSING", repo_root=tmp_path)
        assert result == []


class TestClaimsStoreRoundTrip:
    def test_save_and_load(self, tmp_path: Path):
        c = _make_claim()
        saved_path = claims_store.save("PROJ-001", [c], repo_root=tmp_path)
        assert saved_path.exists()
        loaded = claims_store.load("PROJ-001", repo_root=tmp_path)
        assert len(loaded) == 1
        assert loaded[0].claim_id == c.claim_id
        assert loaded[0].kind == c.kind
        assert loaded[0].canonical == c.canonical

    def test_path_convention(self, tmp_path: Path):
        c = _make_claim()
        saved_path = claims_store.save("PROJ-ABC", [c], repo_root=tmp_path)
        expected = tmp_path / "state" / "claims" / "PROJ-ABC.yaml"
        assert saved_path == expected

    def test_save_multiple_and_load(self, tmp_path: Path):
        c1 = _make_claim(canonical="x=1", context="ctx1")
        c2 = _make_claim(canonical="x=2", context="ctx2")
        claims_store.save("PROJ-001", [c1, c2], repo_root=tmp_path)
        loaded = claims_store.load("PROJ-001", repo_root=tmp_path)
        assert len(loaded) == 2
        ids = {c.claim_id for c in loaded}
        assert c1.claim_id in ids
        assert c2.claim_id in ids


class TestClaimsStoreUpsert:
    def test_upsert_insert_new(self, tmp_path: Path):
        c = _make_claim()
        claims_store.upsert("PROJ-001", c, repo_root=tmp_path)
        loaded = claims_store.load("PROJ-001", repo_root=tmp_path)
        assert len(loaded) == 1
        assert loaded[0].claim_id == c.claim_id

    def test_upsert_replace_by_claim_id(self, tmp_path: Path):
        c = _make_claim()
        claims_store.upsert("PROJ-001", c, repo_root=tmp_path)
        # Update the same claim (same id) with a new status
        updated = Claim(
            claim_id=c.claim_id,
            kind=c.kind,
            raw_text=c.raw_text,
            canonical=c.canonical,
            context=c.context,
            artifact_path=c.artifact_path,
            source_type=c.source_type,
            status=ClaimStatus.VERIFIED,
            resolved_value="1.0",
            evidence={"url": "http://example.com"},
            resolver="grounding",
            attempts=1,
            updated_at="2026-05-30T01:00:00Z",
        )
        claims_store.upsert("PROJ-001", updated, repo_root=tmp_path)
        loaded = claims_store.load("PROJ-001", repo_root=tmp_path)
        assert len(loaded) == 1  # no duplicate
        assert loaded[0].status == ClaimStatus.VERIFIED
        assert loaded[0].resolved_value == "1.0"

    def test_upsert_no_duplicate_different_claims(self, tmp_path: Path):
        c1 = _make_claim(canonical="x=1", context="ctx1")
        c2 = _make_claim(canonical="x=2", context="ctx2")
        claims_store.upsert("PROJ-001", c1, repo_root=tmp_path)
        claims_store.upsert("PROJ-001", c2, repo_root=tmp_path)
        loaded = claims_store.load("PROJ-001", repo_root=tmp_path)
        assert len(loaded) == 2

    def test_upsert_creates_file_if_missing(self, tmp_path: Path):
        c = _make_claim()
        claims_store.upsert("PROJ-NEW", c, repo_root=tmp_path)
        path = tmp_path / "state" / "claims" / "PROJ-NEW.yaml"
        assert path.exists()


class TestClaimsStoreGet:
    def test_get_existing(self, tmp_path: Path):
        c = _make_claim()
        claims_store.save("PROJ-001", [c], repo_root=tmp_path)
        result = claims_store.get("PROJ-001", c.claim_id, repo_root=tmp_path)
        assert result is not None
        assert result.claim_id == c.claim_id

    def test_get_missing_returns_none(self, tmp_path: Path):
        result = claims_store.get("PROJ-001", "c_00000000", repo_root=tmp_path)
        assert result is None

    def test_get_wrong_id_returns_none(self, tmp_path: Path):
        c = _make_claim()
        claims_store.save("PROJ-001", [c], repo_root=tmp_path)
        result = claims_store.get("PROJ-001", "c_00000000", repo_root=tmp_path)
        assert result is None


class TestRepoRootOverride:
    def test_different_tmp_paths_are_isolated(self, tmp_path: Path):
        tmp_a = tmp_path / "a"
        tmp_b = tmp_path / "b"
        tmp_a.mkdir()
        tmp_b.mkdir()
        c = _make_claim()
        claims_store.save("PROJ-001", [c], repo_root=tmp_a)
        assert claims_store.load("PROJ-001", repo_root=tmp_b) == []
