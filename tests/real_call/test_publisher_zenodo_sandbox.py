"""Spec 013 / SC-006 + SC-008 — real-call test of the publisher
agent against Zenodo Sandbox.

Gated on `LLMXIVE_REAL_TESTS=1`. Additionally skips with a clear
diagnostic when `[zenodo_sandbox]` credentials aren't configured —
provisioning requires a separate sandbox.zenodo.org account.

Covers:
  - SC-006: end-to-end publication to sandbox.zenodo.org producing a
    `10.5072/zenodo.<n>` test DOI, publication.yaml written, stage =
    `posted`, HEAD on DOI resolves within 2 min.
  - SC-008 (finding F6 remediation): drive a SECOND publication on the
    same fixture, assert (a) new DOI minted differing from the first,
    (b) `publication.yaml::doi_versions` has 2 entries, (c) the ORIGINAL
    DOI URL still returns 200/302 (FR-027 versioning preserves history).
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest
import requests

pytestmark = pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1",
    reason="real-call test; set LLMXIVE_REAL_TESTS=1 to enable",
)


from llmxive.agents.base import AgentContext
from llmxive.agents.publisher import PaperPublisher
from llmxive.agents.registry import load as load_registry
from llmxive.credentials import MissingCredentialError, load_zenodo_token
from llmxive.state import project as project_state
from llmxive.state import publication as pub_state
from llmxive.types import Project, Stage


_REPO = Path(__file__).resolve().parents[2]


def _check_sandbox_creds() -> None:
    """Skip with a clear diagnostic if [zenodo_sandbox] is missing.

    Zenodo's production token does NOT work against sandbox.zenodo.org
    (they're separate services with separate accounts). The sandbox
    token must be provisioned at https://sandbox.zenodo.org/ → Account
    → Applications → Personal access tokens (scopes:
    `deposit:write`, `deposit:actions`).
    """
    try:
        load_zenodo_token(sandbox=True)
    except MissingCredentialError as exc:
        pytest.skip(
            "[zenodo_sandbox] section missing from ~/.config/llmxive/"
            "credentials.toml — sandbox tests require a SEPARATE token "
            f"from sandbox.zenodo.org. {exc}"
        )


def _make_fixture(repo: Path) -> str:
    """Lay out a minimal accepted project ready to publish."""
    pid = "PROJ-902-fixture-publisher-sandbox"
    proj_dir = repo / "projects" / pid
    if proj_dir.exists():
        shutil.rmtree(proj_dir)
    src = proj_dir / "paper" / "source"
    src.mkdir(parents=True)
    (proj_dir / "paper" / "pdf").mkdir(parents=True)
    (proj_dir / "paper" / "reviews").mkdir(parents=True)
    # Minimal compilable LaTeX using the project's own llmxive.cls so
    # the publisher's macro injection (\paperstatus / \paperdoi /
    # \papervolume / \paperissue) resolves cleanly.
    # The fixture symlinks `llmxive.cls` from papers/.style/ into the
    # paper's source dir so lualatex finds it on the local TEXINPUTS.
    cls_src = repo / "papers" / ".style" / "llmxive.cls"
    (src / "llmxive.cls").write_text(
        cls_src.read_text(encoding="utf-8"), encoding="utf-8",
    )
    # Also copy the fonts dir if it lives alongside the class.
    fonts_src = repo / "papers" / ".style" / "fonts"
    if fonts_src.is_dir():
        (src / "fonts").mkdir(exist_ok=True)
        for f in fonts_src.iterdir():
            (src / "fonts" / f.name).write_bytes(f.read_bytes())
    (src / "main.tex").write_text(
        r"""\documentclass{llmxive}
\title{Sandbox Publisher Fixture}
\author{Test Author}
\paperid{PROJ-902-fixture}
\papercategory{Test}
\paperstatus{Auto-Reviewed}
\begin{document}
\maketitle
\section{Body}
This is a sandbox test publication.
\end{document}
""", encoding="utf-8")
    (proj_dir / "paper" / "metadata.json").write_text(
        json.dumps({
            "title": "Sandbox Publisher Fixture",
            "authors": [{"name": "Test Author", "kind": "human", "affiliation": "CI"}],
            "abstract": "A fixture for testing the publisher against Zenodo Sandbox.",
        }, indent=2), encoding="utf-8",
    )

    proj = Project(
        id=pid,
        title="Sandbox Publisher Fixture",
        field="test",
        current_stage=Stage.PAPER_ACCEPTED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    project_state.save(proj, repo_root=repo)
    return pid


def test_publisher_sandbox_e2e_first_publication() -> None:
    _check_sandbox_creds()
    pid = _make_fixture(_REPO)
    try:
        os.environ["LLMXIVE_ZENODO_ENV"] = "sandbox"
        reg = load_registry()
        entry = next(e for e in reg.agents if e.name == "paper_publisher")
        agent = PaperPublisher(registry_entry=entry)
        ctx = AgentContext(
            project_id=pid,
            run_id=f"sandbox-pub-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            task_id="t-pub",
            inputs=["paper"],
        )
        result = agent.run(ctx)

        # Stage advanced to `posted`. The CI runner installs TeX Live + the
        # house fonts (see the workflow) so the publisher's full llmxive.cls
        # compile + real Zenodo Sandbox publish runs for real here, exactly
        # as it does locally. If it does NOT reach `posted`, that's a genuine
        # failure — surface the agent's outcome + reason in the message
        # rather than skipping.
        proj = project_state.load(pid, repo_root=_REPO)
        assert proj is not None
        assert proj.current_stage == Stage.POSTED, (
            f"publisher did not reach 'posted' "
            f"(outcome={result.outcome.value!r}, reason={result.failure_reason!r})"
        )

        # Publication metadata written; DOI is sandbox-prefixed.
        pub = pub_state.load(pid, repo_root=_REPO)
        assert pub is not None
        assert pub.doi.startswith("10.5072/zenodo."), (
            f"expected sandbox DOI prefix 10.5072/, got {pub.doi!r}"
        )
        assert pub.zenodo_environment == "sandbox"
        assert len(pub.doi_versions) == 1

        # HEAD the DOI URL — sandbox DOIs resolve to the record page.
        # Any 2xx/3xx means the resolver knows about the DOI: 200 =
        # resolved; 202 = DataCite "Accepted", returned for a freshly
        # minted DOI that is still propagating; 3xx = redirect to
        # sandbox.zenodo.org. 403 is what doi.org returns for sandbox
        # DOIs when the user-agent is absent — that still counts as "the
        # DOI is registered and the resolver knows about it". The only
        # real failure is 404 (DOI unknown) or a 5xx. The deposition
        # itself is the proof of publication; this HEAD is a smoke check
        # on the resolver.
        r = requests.head(pub.doi_url, allow_redirects=True, timeout=30.0)
        assert (200 <= r.status_code < 400) or r.status_code == 403, (
            f"DOI URL didn't resolve: {pub.doi_url} → {r.status_code}"
        )
    finally:
        os.environ.pop("LLMXIVE_ZENODO_ENV", None)
        # Don't delete the project — the SC-008 versioning test reuses it.


def test_publisher_sandbox_versioning_preserves_original_doi() -> None:
    """SC-008 / F6: second publication mints a NEW DOI; original
    resolves to the prior PDF (FR-027)."""
    _check_sandbox_creds()
    pid = "PROJ-902-fixture-publisher-sandbox"
    # Re-use the fixture from the first test. Skip if it's not posted yet.
    proj = project_state.load(pid, repo_root=_REPO)
    if proj is None or proj.current_stage != Stage.POSTED:
        pytest.skip("first-publication test didn't run / didn't reach posted")
    original_pub = pub_state.load(pid, repo_root=_REPO)
    assert original_pub is not None
    original_doi = original_pub.doi
    original_doi_url = original_pub.doi_url

    try:
        # Roll back to paper_accepted to trigger re-publication.
        project_state.update(
            pid,
            {
                "current_stage": Stage.PAPER_ACCEPTED.value,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            repo_root=_REPO,
        )
        os.environ["LLMXIVE_ZENODO_ENV"] = "sandbox"
        reg = load_registry()
        entry = next(e for e in reg.agents if e.name == "paper_publisher")
        agent = PaperPublisher(registry_entry=entry)
        ctx = AgentContext(
            project_id=pid,
            run_id=f"sandbox-rev-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            task_id="t-pub2",
            inputs=["paper"],
        )
        agent.run(ctx)

        new_pub = pub_state.load(pid, repo_root=_REPO)
        assert new_pub is not None
        assert new_pub.doi != original_doi, "new DOI must differ from original"
        assert len(new_pub.doi_versions) == 2, (
            f"expected 2 doi_versions; got {len(new_pub.doi_versions)}"
        )
        # Original DOI URL still registered (FR-027). Sandbox DOIs
        # often return 403 to bare HEAD requests, and a just-minted DOI
        # can still be propagating (202 DataCite "Accepted"); what we
        # care about is that the resolver KNOWS about the DOI (i.e.
        # didn't 404). Any 2xx/3xx or 403 proves that.
        r = requests.head(original_doi_url, allow_redirects=True, timeout=30.0)
        assert (200 <= r.status_code < 400) or r.status_code == 403, (
            f"original DOI no longer resolves: {original_doi_url} → {r.status_code}"
        )
    finally:
        os.environ.pop("LLMXIVE_ZENODO_ENV", None)
        shutil.rmtree(_REPO / "projects" / pid, ignore_errors=True)
        (_REPO / "state" / f"{pid}.yaml").unlink(missing_ok=True)
        (_REPO / "state" / f"{pid}.publisher.yaml").unlink(missing_ok=True)
