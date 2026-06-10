# llmXive MCP server

Exposes the librarian search-and-verify tools and the claims
register→resolve→cache layer over the
[Model Context Protocol](https://modelcontextprotocol.io), decoupled from the
bespoke pipeline router (issue #295, scope item 2).

## Install & run

```bash
pip install -e ".[mcp]"        # adds the optional MCP SDK dependency
python -m llmxive.mcp_server   # stdio MCP server, name "llmxive"
```

Honors `LLMXIVE_REPO_ROOT` (via `llmxive.config.repo_root()`) for the claim
register location, and the usual credential resolution (env vars first, then
`~/.config/llmxive/credentials.toml`).

## Tools

| Tool | Wraps | Needs |
|-|-|-|
| `search_semantic_scholar(query, limit=10)` | `librarian.search.SemanticScholarClient.search_papers` | `SEMANTIC_SCHOLAR_API_KEY` |
| `search_arxiv(query, max_results=10)` | `librarian.search.ArxivClient.search` | — |
| `get_arxiv_paper(arxiv_id)` | `librarian.search.ArxivClient.get_by_id` | — |
| `search_theorems(term, limit=10)` | `librarian.theoremsearch.TheoremSearchClient.search` | — |
| `resolve_reference(kind, value)` | `librarian.verify.resolve_reference` | — |
| `register_and_resolve_claims(text, artifact_path="mcp-adhoc.md")` | `claims.service.process_document` (project `mcp-adhoc`) | Dartmouth Chat key |
| `claim_status(claim_id)` | `state.claims.get` (scans all registers) | — |
| `credit_balance()` | `backends.credits.fetch_credit_balance` | Dartmouth Chat key |

Missing keys / failures return an `{"error": "..."}` payload instead of
crashing the server.

## Claude Code client config

```bash
claude mcp add llmxive -- python -m llmxive.mcp_server
```

(Use the python interpreter of the environment where `llmxive[mcp]` is
installed, e.g. `claude mcp add llmxive -- /path/to/.venv/bin/python -m llmxive.mcp_server`.)
