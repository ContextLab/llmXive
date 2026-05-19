"""Spec 013 / US6 — unit tests for `paper/publication.yaml` round-trip
and metadata.json mirror (FR-032, SC-007).

Covers T037 + the F9 finding remediation (metadata.json mirror assertion).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from llmxive.state import publication as pub_state
from llmxive.types import AuthorEntry, DOIVersion, Publication


_NOW = datetime(2026, 5, 19, 10, 30, 0, tzinfo=timezone.utc)


def _make_publication(project_id: str = "PROJ-001-test") -> Publication:
    return Publication(
        project_id=project_id,
        title="A Paper",
        volume="26",
        issue="05",
        display_volume_issue="26.05",
        doi="10.5281/zenodo.13456789",
        doi_url="https://doi.org/10.5281/zenodo.13456789",
        concept_doi=None,
        doi_versions=[
            DOIVersion(
                doi="10.5281/zenodo.13456789",
                version_index=1,
                published_at=_NOW,
                pdf_sha256="a" * 64,
            ),
        ],
        zenodo_id=13456789,
        zenodo_environment="production",
        citation_string="Alice. 2026. *A Paper*. llmXive **26.05**. doi:10.5281/zenodo.13456789.",
        authors_at_publication=[AuthorEntry(name="Alice", kind="human")],
        accepted_at=_NOW,
        published_at=_NOW,
        review_summary={"num_reviewers": 13, "num_revision_rounds": 1,
                        "num_action_items_addressed": 113, "num_action_items_failed": 3},
    )


class TestPublicationRoundTrip:
    def test_save_and_load(self, tmp_path: Path) -> None:
        repo = tmp_path
        pub = _make_publication()
        # Ensure metadata.json exists so the mirror has something to merge into.
        meta_path = repo / "projects" / "PROJ-001-test" / "paper" / "metadata.json"
        meta_path.parent.mkdir(parents=True)
        meta_path.write_text(
            json.dumps({"title": "A Paper", "arxiv_id": "0000.0001"}), encoding="utf-8",
        )

        pub_state.save("PROJ-001-test", pub, repo_root=repo)
        loaded = pub_state.load("PROJ-001-test", repo_root=repo)
        assert loaded is not None
        assert loaded.doi == pub.doi
        assert loaded.display_volume_issue == "26.05"
        assert len(loaded.doi_versions) == 1

    def test_metadata_json_mirror(self, tmp_path: Path) -> None:
        """F9 / SC-007: after save(), metadata.json mirrors doi /
        doi_url / zenodo_id / volume / issue / doi_versions."""
        repo = tmp_path
        meta_path = repo / "projects" / "PROJ-001-test" / "paper" / "metadata.json"
        meta_path.parent.mkdir(parents=True)
        meta_path.write_text(
            json.dumps({"title": "Original Title", "arxiv_id": "X"}), encoding="utf-8",
        )

        pub = _make_publication()
        pub_state.save("PROJ-001-test", pub, repo_root=repo)

        m = json.loads(meta_path.read_text())
        assert m["doi"] == pub.doi
        assert m["doi_url"] == pub.doi_url
        assert m["zenodo_id"] == pub.zenodo_id
        assert m["volume"] == pub.volume
        assert m["issue"] == pub.issue
        assert isinstance(m["doi_versions"], list)
        assert len(m["doi_versions"]) == 1
        # FR-016: other fields untouched.
        assert m["title"] == "Original Title"
        assert m["arxiv_id"] == "X"

    def test_load_returns_none_for_unpublished(self, tmp_path: Path) -> None:
        assert pub_state.load("PROJ-999-never", repo_root=tmp_path) is None


class TestAppendVersion:
    def test_appends_new_doi_version(self, tmp_path: Path) -> None:
        repo = tmp_path
        (repo / "projects" / "PROJ-001-test" / "paper").mkdir(parents=True)
        (repo / "projects" / "PROJ-001-test" / "paper" / "metadata.json").write_text(
            json.dumps({"title": "T"}), encoding="utf-8",
        )
        pub_state.save("PROJ-001-test", _make_publication(), repo_root=repo)
        new_version = DOIVersion(
            doi="10.5281/zenodo.99999",
            version_index=2,
            published_at=_NOW,
            pdf_sha256="b" * 64,
        )
        updated = pub_state.append_version("PROJ-001-test", new_version, repo_root=repo)
        assert len(updated.doi_versions) == 2
        assert updated.doi == "10.5281/zenodo.99999"  # new canonical

    def test_duplicate_version_raises(self, tmp_path: Path) -> None:
        repo = tmp_path
        (repo / "projects" / "PROJ-001-test" / "paper").mkdir(parents=True)
        (repo / "projects" / "PROJ-001-test" / "paper" / "metadata.json").write_text(
            json.dumps({"title": "T"}), encoding="utf-8",
        )
        pub_state.save("PROJ-001-test", _make_publication(), repo_root=repo)
        dup = DOIVersion(
            doi="10.5281/zenodo.13456789",  # same as initial
            version_index=2,
            published_at=_NOW,
            pdf_sha256="c" * 64,
        )
        import pytest
        with pytest.raises(ValueError, match="already recorded"):
            pub_state.append_version("PROJ-001-test", dup, repo_root=repo)
