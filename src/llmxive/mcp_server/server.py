"""llmXive MCP server — librarian search/verify + claims register→resolve→cache.

Issue #295 scope item 2: expose the librarian's search-and-verify tools and
the claim layer (spec 016/020) over the Model Context Protocol, decoupled
from the bespoke pipeline router, so ANY MCP client (Claude Code, etc.) can
drive them directly.

Every tool is a thin wrapper over an existing llmxive function — no logic is
reimplemented here. Results are plain JSON-serializable dicts/lists/strings;
failures (missing API key, network error) come back as a clear ``{"error":
...}`` payload instead of crashing the server.

The MCP SDK is imported lazily inside :func:`create_server` so importing
``llmxive`` (or this module) never requires the optional ``mcp`` extra.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover — typing only; SDK is optional at runtime
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

#: Abstracts are trimmed to this many characters in tool output.
_ABSTRACT_SNIPPET_CHARS = 500

#: Ad-hoc MCP calls register claims under this synthetic project id, keeping
#: them in their own ``state/claims/<id>.yaml`` register, away from real
#: pipeline projects (the underlying store honors LLMXIVE_REPO_ROOT via
#: llmxive.config.repo_root()).
MCP_ADHOC_PROJECT_ID = "mcp-adhoc"

MISSING_MCP_SDK_MSG = (
    "The MCP python SDK is not installed. Install the optional extra with: "
    'pip install "llmxive[mcp]"'
)


def _candidate_to_dict(candidate: Any) -> dict[str, Any]:
    """Convert a librarian ``Candidate`` dataclass to a JSON-friendly dict."""
    abstract = candidate.claimed_abstract or ""
    if len(abstract) > _ABSTRACT_SNIPPET_CHARS:
        abstract = abstract[: _ABSTRACT_SNIPPET_CHARS - 1].rstrip() + "…"
    return {
        "backend": candidate.backend,
        "id": candidate.primary_pointer,
        "title": candidate.claimed_title,
        "authors": candidate.claimed_authors,
        "year": candidate.claimed_year,
        "venue": candidate.claimed_venue,
        "abstract_snippet": abstract or None,
    }


def _claim_to_dict(claim: Any) -> dict[str, Any]:
    """Serialize a Claim via the store's canonical dict form."""
    from llmxive.state.claims import _claim_to_dict as store_claim_to_dict

    return store_claim_to_dict(claim)


def _error(message: str) -> dict[str, str]:
    return {"error": message}


def create_server() -> FastMCP:
    """Build the FastMCP server with all llmXive tools registered."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover — exercised via __main__
        raise ImportError(MISSING_MCP_SDK_MSG) from exc

    server = FastMCP("llmxive")

    @server.tool()
    def search_semantic_scholar(query: str, limit: int = 10) -> list[dict[str, Any]] | dict[str, str]:
        """Search Semantic Scholar for papers by keyword query.

        Returns a list of candidate records (backend, id, title, authors,
        year, venue, abstract_snippet). Requires SEMANTIC_SCHOLAR_API_KEY
        (free tier) — returns an error payload if the key is missing.
        """
        from llmxive.librarian.search import SemanticScholarClient

        client = SemanticScholarClient()
        if not client.has_key:
            return _error(
                "SEMANTIC_SCHOLAR_API_KEY is not configured — request a free "
                "key at https://www.semanticscholar.org/product/api#api-key-form "
                "and store it with llmxive.credentials.save_semantic_scholar_key()."
            )
        try:
            return [_candidate_to_dict(c) for c in client.search_papers(query, limit=limit)]
        except Exception as exc:
            return _error(f"semantic scholar search failed: {type(exc).__name__}: {exc}")

    @server.tool()
    def search_arxiv(query: str, max_results: int = 10) -> list[dict[str, Any]] | dict[str, str]:
        """Search arXiv for papers by keyword query.

        Returns a list of candidate records (backend, id, title, authors,
        year, venue, abstract_snippet). Rate-limited per arXiv's guidelines;
        sustained 429s trip a 60s circuit breaker and yield an empty list.
        """
        from llmxive.librarian.search import ArxivClient

        try:
            return [
                _candidate_to_dict(c)
                for c in ArxivClient().search(query, max_results=max_results)
            ]
        except Exception as exc:
            return _error(f"arxiv search failed: {type(exc).__name__}: {exc}")

    @server.tool()
    def get_arxiv_paper(arxiv_id: str) -> dict[str, Any]:
        """Fetch one arXiv paper by id (e.g. '1706.03762' or '1706.03762v3').

        Returns a candidate record (backend, id, title, authors, year, venue,
        abstract_snippet), or an error payload if the id does not resolve.
        """
        from llmxive.librarian.search import ArxivClient

        try:
            candidate = ArxivClient().get_by_id(arxiv_id)
        except Exception as exc:
            return _error(f"arxiv lookup failed: {type(exc).__name__}: {exc}")
        if candidate is None:
            return _error(f"no arXiv paper found for id {arxiv_id!r}")
        return _candidate_to_dict(candidate)

    @server.tool()
    def search_theorems(term: str, limit: int = 10) -> list[dict[str, Any]] | dict[str, str]:
        """Search TheoremSearch for mathematical theorems, resolved to arXiv.

        Returns a list of candidate records for arXiv-sourced theorem hits.
        An unavailable TheoremSearch backend returns an error payload (the
        service is optional enrichment, not a hard dependency).
        """
        from llmxive.backends.base import TransientBackendError
        from llmxive.librarian.theoremsearch import TheoremSearchClient

        try:
            return [
                _candidate_to_dict(c)
                for c in TheoremSearchClient().search(term, limit=limit)
            ]
        except TransientBackendError as exc:
            return _error(f"theoremsearch unavailable: {exc}")
        except Exception as exc:
            return _error(f"theorem search failed: {type(exc).__name__}: {exc}")

    @server.tool()
    def resolve_reference(kind: str, value: str) -> dict[str, Any]:
        """Existence-check one reference: kind is 'url', 'arxiv', or 'doi'.

        Resolves the reference through doi.org / arxiv.org / the URL itself
        (real HTTP, redirect-following). Returns state ('resolved' |
        'present_ambiguous' | 'unreachable'), the final resolved_url, the
        http_status, a reason, and a boolean 'present'. Anti-fabrication
        existence check only — titles are not compared.
        """
        from llmxive.librarian.verify import resolve_reference as _resolve

        if kind not in ("url", "arxiv", "doi"):
            return _error(f"kind must be one of 'url', 'arxiv', 'doi' (got {kind!r})")
        try:
            outcome = _resolve(kind, value)
        except Exception as exc:
            return _error(f"reference resolution failed: {type(exc).__name__}: {exc}")
        return {
            "state": outcome.state,
            "resolved_url": outcome.resolved_url,
            "http_status": outcome.http_status,
            "reason": outcome.reason,
            "present": outcome.present,
        }

    @server.tool()
    def register_and_resolve_claims(text: str, artifact_path: str = "mcp-adhoc.md") -> dict[str, Any]:
        """Run the claim layer on a document: extract→register→resolve→render.

        Extracts check-worthy claims from the text with an LLM, registers
        them in the durable claim register (state/claims/), resolves each
        against authoritative sources (reusing cached VERIFIED claims), and
        returns the rendered text plus the claim records and gate report.
        Requires a Dartmouth Chat API key — returns an error payload if the
        key is unavailable.
        """
        from llmxive.backends.dartmouth import _ensure_api_key_env
        from llmxive.backends.router import make_backend
        from llmxive.claims.service import process_document
        from llmxive.config import repo_root

        _ensure_api_key_env()
        import os

        if not os.environ.get("DARTMOUTH_CHAT_API_KEY"):
            return _error(
                "DARTMOUTH_CHAT_API_KEY is not available (checked the environment "
                "and ~/.config/llmxive/credentials.toml) — the claim layer needs "
                "an LLM backend for extraction."
            )
        try:
            backend = make_backend("dartmouth")
            # model=None → the claim layer's default reasoning model with the
            # router's standard peer-model fallback chain (qwen → gpt-oss →
            # gemma), exactly as the pipeline invokes it.
            rendered, claims, gate_report = process_document(
                text,
                artifact_path=artifact_path,
                project_id=MCP_ADHOC_PROJECT_ID,
                backend=backend,
                model=None,
                repo_root=repo_root(),
            )
        except Exception as exc:
            return _error(f"claim processing failed: {type(exc).__name__}: {exc}")
        return {
            "rendered_text": rendered,
            "claims": [_claim_to_dict(c) for c in claims],
            "gate_report": {
                "blocked": gate_report.blocked,
                "unresolved_markers": list(gate_report.unresolved_markers),
            },
            "project_id": MCP_ADHOC_PROJECT_ID,
        }

    @server.tool()
    def claim_status(claim_id: str) -> dict[str, Any]:
        """Look up one claim by id in the durable claim register.

        Scans every per-project register under state/claims/ and returns the
        claim record (status, kind, raw/canonical text, resolved value,
        evidence, resolver, timestamps) plus the owning project_id, or an
        error payload if the claim id is unknown.
        """
        from llmxive.config import repo_root
        from llmxive.state import claims as claim_store

        claims_dir = repo_root() / "state" / "claims"
        if not claims_dir.is_dir():
            return _error(f"no claim registers exist yet under {claims_dir}")
        for register in sorted(claims_dir.glob("*.yaml")):
            project_id = register.stem
            try:
                claim = claim_store.get(project_id, claim_id)
            except Exception as exc:
                logger.warning("claim register %s unreadable: %s", register, exc)
                continue
            if claim is not None:
                payload = _claim_to_dict(claim)
                payload["project_id"] = project_id
                return payload
        return _error(f"claim {claim_id!r} not found in any register under {claims_dir}")

    @server.tool()
    def credit_balance() -> dict[str, Any]:
        """Fetch the live Dartmouth Chat daily paid-credit balance.

        Returns account, spend, max_budget, budget_duration, budget_reset_at,
        and the derived remaining credits. Requires a Dartmouth Chat API key
        — returns an error payload on any failure (network, auth).
        """
        from llmxive.backends.credits import fetch_credit_balance

        try:
            balance = fetch_credit_balance()
        except Exception as exc:
            return _error(f"credit balance unavailable: {type(exc).__name__}: {exc}")
        payload = dataclasses.asdict(balance)
        payload["remaining"] = balance.remaining
        return payload

    return server


def main() -> None:
    """Run the llmXive MCP server over stdio (``python -m llmxive.mcp_server``)."""
    create_server().run()


__all__ = ["MCP_ADHOC_PROJECT_ID", "MISSING_MCP_SDK_MSG", "create_server", "main"]
