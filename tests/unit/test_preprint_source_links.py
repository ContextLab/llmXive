"""The dashboard must point at a preprint's SOURCE, not a copy we do not host.

The ingested bodies (`original.pdf`, `original-llmxive.pdf`) are no longer
committed or mirrored: they carry the arXiv Non-exclusive Distribution License,
whose text grants distribution to arXiv.org and is silent on anyone else, and
they were 4.39 GB of an 8.96 GB repository. So the modal needs the source URL,
the licence, and the digest of the version llmXive actually reviewed — the
source URL serves the CURRENT version, and 5 of a random 12 ingested preprints
already differ from the reviewed bytes.
"""

from __future__ import annotations

import json

import pytest

from llmxive.web_data import _paper_metadata, _preprint_source

FULL = {
    "arxiv_id": "2606.18216",
    "arxiv_url": "https://arxiv.org/abs/2606.18216",
    "license": "arXiv Non-exclusive Distribution License",
    "license_url": "http://arxiv.org/licenses/nonexclusive-distrib/1.0/",
    "abstract": "An abstract.",
    "committed_pdf_digests": {
        "original.pdf": {"sha256": "c" * 64, "bytes": 9128866},
        "original-llmxive.pdf": {"sha256": "5" * 64, "bytes": 9147612},
    },
}


def _project(tmp_path, metadata):
    paper = tmp_path / "paper"
    paper.mkdir(parents=True)
    if metadata is not None:
        (paper / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    return tmp_path


def test_the_source_block_carries_url_licence_and_reviewed_digest(tmp_path):
    source = _preprint_source(_project(tmp_path, FULL))
    assert source["url"] == "https://arxiv.org/abs/2606.18216"
    assert source["arxiv_id"] == "2606.18216"
    assert source["license"] == "arXiv Non-exclusive Distribution License"
    assert source["license_url"] == "http://arxiv.org/licenses/nonexclusive-distrib/1.0/"
    # The digest is of the ORIGINAL body, which is what the reviews read.
    assert source["reviewed_version"] == {
        "file": "original.pdf", "sha256": "c" * 64, "bytes": 9128866,
    }


def test_the_cover_prepended_version_attests_when_the_raw_body_was_not_kept(tmp_path):
    """Three ingests committed only `original-llmxive.pdf`; it is the same body."""
    metadata = dict(FULL, committed_pdf_digests={
        "original-llmxive.pdf": {"sha256": "5" * 64, "bytes": 9147612},
    })
    source = _preprint_source(_project(tmp_path, metadata))
    assert source["reviewed_version"] == {
        "file": "original-llmxive.pdf", "sha256": "5" * 64, "bytes": 9147612,
    }


def test_a_paper_without_recorded_digests_reports_no_reviewed_version(tmp_path):
    metadata = {k: v for k, v in FULL.items() if k != "committed_pdf_digests"}
    source = _preprint_source(_project(tmp_path, metadata))
    assert source["reviewed_version"] is None
    assert source["url"], "the source link must survive a missing digest"


@pytest.mark.parametrize("metadata", [None, {}, {"arxiv_id": ""}], ids=["absent", "empty", "blank"])
def test_missing_or_empty_metadata_never_raises(tmp_path, metadata):
    source = _preprint_source(_project(tmp_path, metadata))
    assert source == {} or source["url"] == ""


def test_unreadable_metadata_is_not_fatal(tmp_path):
    pdir = _project(tmp_path, None)
    (pdir / "paper" / "metadata.json").write_text("{not json", encoding="utf-8")
    assert _paper_metadata(pdir) == {}
    assert _preprint_source(pdir) == {}


def test_a_json_list_is_not_metadata(tmp_path):
    pdir = _project(tmp_path, None)
    (pdir / "paper" / "metadata.json").write_text("[1, 2]", encoding="utf-8")
    assert _paper_metadata(pdir) == {}


# --- the live corpus -----------------------------------------------------

def _repo_preprints():
    from llmxive.config import repo_root

    return sorted(repo_root().glob("projects/*/paper/metadata.json"))


#: A sparse checkout can materialize ONE project's paper metadata (CI's offline
#: job pins `projects/PROJ-565-.../paper/` for an unrelated fixture), and a
#: corpus of one is not the corpus. Below this the check skips loudly rather
#: than passing on a sample it cannot speak for.
MIN_CORPUS = 50


@pytest.mark.skipif(
    len(_repo_preprints()) < MIN_CORPUS,
    reason=f"fewer than {MIN_CORPUS} preprint metadata files checked out",
)
def test_every_ingested_preprint_can_be_linked_and_attributed():
    """No ingested paper may be left without a source link or a named licence.

    Without both, the dashboard would show a paper it does not host and cannot
    point at — and the reviewed-version digest is what keeps a review attached
    to the bytes it was written against.
    """
    missing_url, missing_licence, unattested = [], [], []
    attested = with_digests = 0
    for meta_file in _repo_preprints():
        pdir = meta_file.parent.parent
        source = _preprint_source(pdir)
        if not source.get("url"):
            missing_url.append(pdir.name)
        if not source.get("license"):
            missing_licence.append(pdir.name)
        # An INGESTED body must be attested. A paper rebuilt from arXiv LaTeX
        # source has no ingested body (only main-llmxive.pdf, which is ours).
        digests = _paper_metadata(pdir).get("committed_pdf_digests") or {}
        if digests:
            with_digests += 1
            if source.get("reviewed_version"):
                attested += 1
            else:
                unattested.append(pdir.name)
    assert not missing_url, f"no source URL: {missing_url[:5]}"
    assert not missing_licence, f"no licence recorded: {missing_licence[:5]}"
    assert not unattested, f"committed body with no reviewed digest: {unattested[:5]}"
    assert attested == with_digests, f"{attested} attested of {with_digests} with digests"


# --- the Pages mirror must not publish a third-party body ----------------

def _mirror_script() -> str:
    """The real `run:` body of pages.yml's PDF-mirror step."""
    import yaml

    from llmxive.config import repo_root

    workflow = yaml.safe_load((repo_root() / ".github/workflows/pages.yml").read_text())
    for job in workflow["jobs"].values():
        for step in job.get("steps", []):
            if "Mirror paper PDFs" in str(step.get("name", "")):
                return step["run"]
    raise AssertionError("pages.yml no longer has a PDF-mirror step")


def test_the_pages_mirror_skips_third_party_bodies(tmp_path):
    """Run the REAL mirror step against a synthetic tree.

    This filter is load-bearing even though the files are gitignored:
    `resolve_original_pdf` re-downloads `original.pdf` into the working tree
    during a run, and the step globs the working tree.
    """
    import subprocess

    pdf_dir = tmp_path / "projects" / "PROJ-1-x" / "paper" / "pdf"
    pdf_dir.mkdir(parents=True)
    for name in ("original.pdf", "original-llmxive.pdf",
                 "main-llmxive.pdf", "peer-review-llmxive.pdf"):
        (pdf_dir / name).write_bytes(b"%PDF-1.7\nbody\n%%EOF\n")

    script = tmp_path / "mirror.sh"
    script.write_text(_mirror_script(), encoding="utf-8")
    done = subprocess.run(["bash", str(script)], cwd=tmp_path,
                          capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stdout + done.stderr

    mirrored = sorted(p.name for p in (tmp_path / "docs" / "papers").rglob("*.pdf"))
    assert mirrored == ["main-llmxive.pdf", "peer-review-llmxive.pdf"], mirrored
    assert "skip third-party body" in done.stdout
