"""Contract-surface inventory (spec 026, Phase 2 slice M0).

Builds a *checked* manifest of the ENTIRE model-selection contract surface —
every ``default_model`` / ``default_backend`` / ``fallback_backends`` field and
every hard-coded model-id pin — across the production code, ``registry.yaml``,
and the test doubles. The slice-8 ``enforcement.py`` test consumes the committed
manifest so that deleting ``DEFAULT_MODEL`` / ``MODEL_FALLBACKS`` is safe: no new
production pin can land without either updating the manifest (a reviewed event)
or tripping CI.

The scanner is AST-based (not regex) so that a model id mentioned only in a
comment or docstring is correctly ignored — only real code pins count.
"""

from __future__ import annotations

import ast
import json
import re
from collections import Counter
from pathlib import Path

import yaml

#: Manifest schema id (mirrors the repo convention, e.g. ``llmxive-summary/1``).
SCHEMA = "llmxive-model-selection-migration/1"
#: Committed artifacts (relative to repo root) — the checked JSON that slice-8
#: enforcement consumes + its human-readable MD projection.
MANIFEST_JSON = "specs/026-model-selection-consolidation/migration_manifest.json"
MANIFEST_MD = "specs/026-model-selection-consolidation/migration_manifest.md"
#: Fixed provenance string — NEVER a timestamp/abs path (the drift test compares
#: ``build_manifest(root)`` to the committed JSON, so output must be deterministic).
GENERATED_BY = "llmxive.model_selection.inventory.build_manifest"

#: Vendor prefixes of the dotted Dartmouth model-id form (``vendor.model``).
#: ``zai-org`` (the ``zai-org.glm-5.3`` leader, policy v3) is listed so a
#: hardcoded pin on the CURRENT primary is detected like any other.
_KNOWN_VENDORS = frozenset(
    {"qwen", "google", "openai", "anthropic", "meta", "mistralai", "cohere", "zai-org"}
)
#: ``vendor.model`` — the model part must carry a digit (every real Dartmouth id
#: does), so import module names like ``google.generativeai`` are NOT matched.
_DOTTED_MODEL = re.compile(
    r"^(?:" + "|".join(sorted(_KNOWN_VENDORS)) + r")\."
    r"(?=[A-Za-z0-9._:-]*\d)[A-Za-z0-9][A-Za-z0-9._:-]*$"
)

#: Bare model ids without a vendor prefix (e.g. ``qwen3.5-122b`` as passed
#: directly by the convergence revisers). Anchored on concrete family stems so
#: ordinary words never match.
_BARE_FAMILY_MODEL = re.compile(
    r"^(?:qwen\d|gemma-\d|gpt-oss|claude-[a-z]|llama-\d|codellama|"
    r"mistral-|voyage-|gemini-|glm-\d)[A-Za-z0-9._:-]*$"
)

#: Hugging Face ``Org/Model`` form (e.g. ``Qwen/Qwen2.5-3B-Instruct``). The org
#: is restricted to a known-ML-org set so ordinary ``a/b`` path strings (e.g.
#: ``state/model_selection``) are NOT mistaken for model ids. The set includes
#: every org in the recorded Hugging Face router catalog, and an optional
#: ``:<provider>`` suffix (the router's pinned-provider form) is accepted.
_HF_ORGS = frozenset(
    {
        "BAAI",
        "BSC-LT",
        "ByteDance-Seed",
        "CohereLabs",
        "EleutherAI",
        "Gryphe",
        "HuggingFaceH4",
        "LiquidAI",
        "MiniMaxAI",
        "NousResearch",
        "Qwen",
        "RadixArk",
        "RekaAI",
        "Salesforce",
        "Sao10K",
        "Undi95",
        "XiaomiMiMo",
        "aisingapore",
        "alpindale",
        "anthracite-org",
        "bigcode",
        "cyankiwi",
        "deepseek-ai",
        "dphn",
        "google",
        "ibm-granite",
        "inclusionAI",
        "meta-llama",
        "meta-models",
        "microsoft",
        "mistralai",
        "moondream",
        "moonshotai",
        "nvidia",
        "openai",
        "reflection",
        "sentence-transformers",
        "speakleash",
        "stabilityai",
        "stepfun-ai",
        "swiss-ai",
        "tencent",
        "thinkingmachines",
        "tiiuae",
        "zai-org",
    }
)
_HF_SLASH_MODEL = re.compile(
    r"^(?:" + "|".join(re.escape(o) for o in sorted(_HF_ORGS)) + r")"
    r"/[A-Za-z0-9][A-Za-z0-9._-]*(?::[A-Za-z0-9][A-Za-z0-9._-]*)?$"
)


#: The three agent-registry schema fields (spec 026 slice 7 migration surface).
_FIELD_NAMES = frozenset({"default_model", "default_backend", "fallback_backends"})
#: Classes whose field *definitions* ARE the schema (not just any consumer). The
#: Pydantic model in ``types.py`` is ``AgentRegistryEntry``; a drift in this name
#: drops the schema entries and trips the frozen manifest test (a reviewed event).
_SCHEMA_CLASSES = frozenset({"AgentRegistryEntry"})

#: The sanctioned canonical policy/catalog layer — an EXPLICIT file allowlist,
#: NOT the whole model_selection package (spec FR-014: literals are permitted only
#: in the canonical policy/catalog layer). A stray model pin anywhere else in the
#: package (execute.py, reservations.py, ...) must fall through to migration_target
#: so slice-8 enforcement rejects it. Extend this set only for a genuinely
#: canonical table, in a reviewed PR.
_CANONICAL_FILES = frozenset({"src/llmxive/model_selection/policy.py"})
#: Specific ``(file, symbol)`` pins sanctioned as canonical even though their file
#: is NOT wholly canonical. ``dartmouth._REASONING_MODELS`` is backend serving-mode
#: knowledge (thinking-mode disable + reasoning-safe token budget) that stays at the
#: acquisition layer — relocating it into ``policy.py`` would create a ``backends →
#: model_selection`` import cycle (decision A, 2026-07-17 maintainer review). Its
#: file-sibling ``KNOWN_FREE_MODELS`` is deliberately NOT here: the live-catalog
#: pricing + LKG store supersede that hardcoded free-ness allowlist, so it stays a
#: migration_target (deleted in slice 8). ``local.list_models`` is the SAME kind of
#: acquisition-layer serving-mode knowledge: the local transformers fallback has no
#: live discovery mechanism (unlike Dartmouth's catalog fetch), so the single
#: checkpoint it serves is inherently a fixed identifier here, not a call-site
#: profile pin (spec 026 slice 7) — moving it into ``policy.py`` would likewise
#: create a ``backends → model_selection`` import cycle.
#: ``escalations._recurring_failure_category`` names a model id for a different
#: reason again: it RECOGNIZES a provider error message (the HTTP-400 signature
#: tracked by the recurring ``provider-availability`` issue) by the id that
#: message contains. It reads an error string; it never chooses, requests or
#: ranks a model, so there is no profile to migrate it to (added 2026-11-23 when
#: merging ``main``, which introduced the matcher). Extend only for a
#: genuinely canonical symbol, in a reviewed PR.
_CANONICAL_SYMBOLS = frozenset(
    {
        ("src/llmxive/backends/dartmouth.py", "_REASONING_MODELS"),
        ("src/llmxive/state/escalations.py", "_recurring_failure_category"),
        ("src/llmxive/backends/local.py", "list_models"),
    }
)
_TESTS_PREFIX = "tests/"
_REGISTRY_PATH = "agents/registry.yaml"
#: The registry sentinel for scaffolding agents that make NO LLM call (spec 015 /
#: test_config_consistency.NO_LLM). Exemption requires this EXACT literal — an
#: empty/unknown default_model is a data error, not a silent exemption.
_NO_LLM_SENTINEL = "deterministic-no-llm"
#: Path → owning migration slice for production pins outside the canonical layer.
#: Advisory (later slices confirm ownership); the *category* is the binding part.
_ROUTER_PATH = "src/llmxive/backends/router.py"
_EXECUTION_STATUS_PATH = "src/llmxive/state/execution_status.py"
_DARTMOUTH_PATH = "src/llmxive/backends/dartmouth.py"


def categorize(entry: dict) -> tuple[str, int | None]:
    """Classify one raw entry → ``(category, owning_slice)``.

    Categories: ``canonical_layer`` (sanctioned mechanism), ``test_double``,
    ``registry``, ``schema`` (AgentSpec field defs), ``exempt`` (the
    ``deterministic-no-llm`` sentinel), ``migration_target`` (everything else —
    a production pin/consumer to migrate). ``owning_slice`` is advisory.
    """
    rel = entry["file"]
    if rel in _CANONICAL_FILES:
        return ("canonical_layer", None)
    if (rel, entry["symbol"]) in _CANONICAL_SYMBOLS:
        return ("canonical_layer", None)
    if rel.startswith(_TESTS_PREFIX):
        return ("test_double", None)
    if rel == _REGISTRY_PATH:
        # Exempt ONLY the exact no-llm sentinel (not merely an unresolvable value).
        if entry["symbol"] == "default_model" and entry.get("value") == _NO_LLM_SENTINEL:
            return ("exempt", None)
        return ("registry", 7)
    if entry["kind"] == "agentspec_field":
        return ("schema", 7)
    if rel == _ROUTER_PATH:
        return ("migration_target", 5)
    if rel == _EXECUTION_STATUS_PATH:
        return ("migration_target", 6)
    # The free-model ALLOWLIST is retired together with DEFAULT_MODEL /
    # MODEL_FALLBACKS in slice 8, not slice 7: slice 7 only removes
    # ``test_config_consistency``'s DEPENDENCE on it (US5 AC4), because the
    # capability policy — not an allowlist — becomes the free/paid authority.
    # Labelling it slice 7 would make "no owning_slice==7 rows remain" unable to
    # ever hold, so the slice-7 completion gate could never be self-verifying.
    if (rel, entry["symbol"]) == (_DARTMOUTH_PATH, "KNOWN_FREE_MODELS"):
        return ("migration_target", 8)
    return ("migration_target", 7)


def looks_like_model_id(value: str) -> bool:
    """True if ``value`` is a concrete model identifier we pin against."""
    return bool(
        _DOTTED_MODEL.match(value)
        or _BARE_FAMILY_MODEL.match(value)
        or _HF_SLASH_MODEL.match(value)
    )


def _model_id_consts(node: ast.AST) -> list[ast.Constant]:
    """Model-id string-literal ``Constant`` nodes within a value subtree."""
    return [
        s
        for s in ast.walk(node)
        if isinstance(s, ast.Constant)
        and isinstance(s.value, str)
        and looks_like_model_id(s.value)
    ]


#: Callables that are still "data" — a table wrapped in one of these is a pin
#: table, not an arbitrary function call (Constitution I: one source of truth).
_COLLECTION_CTORS = frozenset({"frozenset", "set", "tuple", "list", "dict"})


def _is_pure_data(node: ast.AST) -> bool:
    """True if ``node`` is only literals + collection displays/constructors.

    Distinguishes a constant pin table (``KNOWN_FREE_MODELS = frozenset({...})``,
    ``MODEL_FALLBACKS = {...}``) from an assignment whose value merely *contains*
    a model id passed to a call (``x = summarize(..., model="...")``). Only the
    former is a ``module_constant``; the latter's literal is left for Pass 2 so
    it keeps its true ``model=`` symbol + line.
    """
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return all(_is_pure_data(elt) for elt in node.elts)
    if isinstance(node, ast.Dict):
        keys = [k for k in node.keys if k is not None]
        return all(_is_pure_data(k) for k in keys) and all(
            _is_pure_data(v) for v in node.values
        )
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name) and func.id in _COLLECTION_CTORS:
            return all(_is_pure_data(a) for a in node.args) and all(
                _is_pure_data(kw.value) for kw in node.keywords
            )
        return False
    return False


def _parent_map(tree: ast.AST) -> dict[int, ast.AST]:
    parents: dict[int, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[id(child)] = parent
    return parents


def _docstring_const_ids(tree: ast.AST) -> set[int]:
    """``id()`` of every docstring Constant (module/class/function first stmt)."""
    ids: set[int] = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(body, list) or not body:
            continue
        first = body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
            if isinstance(first.value.value, str):
                ids.add(id(first.value))
    return ids


def _default_arg_symbols(tree: ast.AST) -> dict[int, str]:
    """Map ``id(Constant)`` of a default-argument literal to its parameter name."""
    out: dict[int, str] = {}
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        args = fn.args
        positional = [*getattr(args, "posonlyargs", []), *args.args]
        with_defaults = positional[len(positional) - len(args.defaults):]
        for arg, default in zip(with_defaults, args.defaults, strict=True):
            for sub in ast.walk(default):
                if isinstance(sub, ast.Constant):
                    out[id(sub)] = arg.arg
        for arg, default in zip(args.kwonlyargs, args.kw_defaults, strict=True):
            if default is None:
                continue
            for sub in ast.walk(default):
                if isinstance(sub, ast.Constant):
                    out[id(sub)] = arg.arg
    return out


def _symbol_for_literal(
    node: ast.Constant, parents: dict[int, ast.AST], default_arg_symbol: dict[int, str]
) -> str:
    """Best-effort name for a standalone literal: default-arg / keyword / assign
    target, else the enclosing function name."""
    if id(node) in default_arg_symbol:
        return default_arg_symbol[id(node)]
    fallback = "<literal>"
    cur: ast.AST = node
    while id(cur) in parents:
        parent = parents[id(cur)]
        if isinstance(parent, ast.keyword) and parent.arg:
            return parent.arg
        if isinstance(parent, ast.Assign):
            for target in parent.targets:
                if isinstance(target, ast.Name):
                    return target.id
        if isinstance(parent, ast.AnnAssign) and isinstance(parent.target, ast.Name):
            return parent.target.id
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)) and fallback == "<literal>":
            fallback = parent.name
        cur = parent
    return fallback


def scan_python(path, rel: str) -> list[dict]:
    """Scan one Python file for contract-surface entries.

    ``rel`` is the repo-relative POSIX path recorded on each entry. Returns raw
    entries (``file``/``line``/``kind``/``symbol``/``models``); categorization is
    applied by :func:`build_manifest`.
    """
    tree = ast.parse(path.read_text(), filename=str(path))
    parents = _parent_map(tree)
    docstring_ids = _docstring_const_ids(tree)
    default_arg_symbol = _default_arg_symbols(tree)

    entries: list[dict] = []
    claimed: set[int] = set()

    # Pass 1: named constants whose value is a model-id DATA TABLE (one entry per
    # name, carrying every model — a fallback table stays a single entry). The
    # pure-data gate excludes assignments that merely pass a model to a call.
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
            continue
        if not _is_pure_data(node.value):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names = [t.id for t in targets if isinstance(t, ast.Name)]
        if not names:
            continue
        model_consts = _model_id_consts(node.value)
        if not model_consts:
            continue
        models = sorted({c.value for c in model_consts})
        claimed.update(id(c) for c in model_consts)
        for name in names:
            entries.append(
                {
                    "file": rel,
                    "line": node.lineno,
                    "kind": "module_constant",
                    "symbol": name,
                    "models": models,
                }
            )

    # Pass 2: standalone model-id literals (default args, keyword args, returns),
    # excluding docstrings and anything already claimed by a Pass-1 constant.
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            continue
        if id(node) in claimed or id(node) in docstring_ids:
            continue
        if not looks_like_model_id(node.value):
            continue
        entries.append(
            {
                "file": rel,
                "line": node.lineno,
                "kind": "model_id_literal",
                "symbol": _symbol_for_literal(node, parents, default_arg_symbol),
                "models": [node.value],
            }
        )

    # Pass 3: AgentSpec schema field DEFINITIONS (carry no literal — detected by
    # name within the schema class; the slice-7 migration surface).
    for cls in ast.walk(tree):
        if not (isinstance(cls, ast.ClassDef) and cls.name in _SCHEMA_CLASSES):
            continue
        for stmt in cls.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                if stmt.target.id in _FIELD_NAMES:
                    entries.append(
                        {
                            "file": rel,
                            "line": stmt.lineno,
                            "kind": "agentspec_field",
                            "symbol": stmt.target.id,
                            "models": [],
                        }
                    )

    # Pass 4: reads of the schema fields (``entry.default_model`` etc.) — the
    # compatibility consumers that slice 7 rewrites.
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in _FIELD_NAMES:
            entries.append(
                {
                    "file": rel,
                    "line": node.lineno,
                    "kind": "field_consumer",
                    "symbol": node.attr,
                    "models": [],
                }
            )

    return entries


def _registry_field_models(value_node: yaml.Node) -> list[str]:
    """Model ids among a registry field's value(s) (backends/sentinels yield []).

    Backend names and the ``deterministic-no-llm`` sentinel are not model ids.
    """
    if isinstance(value_node, yaml.ScalarNode):
        return [value_node.value] if looks_like_model_id(value_node.value) else []
    if isinstance(value_node, yaml.SequenceNode):
        return sorted(
            {
                item.value
                for item in value_node.value
                if isinstance(item, yaml.ScalarNode) and looks_like_model_id(item.value)
            }
        )
    return []


def _registry_field_value(value_node: yaml.Node):
    """The raw literal value of a registry field (a string, or a list for
    ``fallback_backends``) — recorded so ``categorize`` can check the exact no-llm
    sentinel rather than inferring exemption from empty models (review finding 7b)."""
    if isinstance(value_node, yaml.ScalarNode):
        return value_node.value
    if isinstance(value_node, yaml.SequenceNode):
        return [i.value for i in value_node.value if isinstance(i, yaml.ScalarNode)]
    return None


def scan_registry(path, rel: str) -> list[dict]:
    """Scan ``registry.yaml`` for every agent's model-selection fields.

    Each of ``default_backend`` / ``fallback_backends`` / ``default_model`` on
    each agent becomes a ``registry_field`` entry (line anchored on the key).
    """
    root = yaml.compose(path.read_text())
    entries: list[dict] = []
    if not isinstance(root, yaml.MappingNode):
        return entries

    for key_node, value_node in root.value:
        if key_node.value != "agents" or not isinstance(value_node, yaml.SequenceNode):
            continue
        for agent_node in value_node.value:
            if not isinstance(agent_node, yaml.MappingNode):
                continue
            for field_key, field_value in agent_node.value:
                if field_key.value not in _FIELD_NAMES:
                    continue
                entries.append(
                    {
                        "file": rel,
                        "line": field_key.start_mark.line + 1,
                        "kind": "registry_field",
                        "symbol": field_key.value,
                        "models": _registry_field_models(field_value),
                        "value": _registry_field_value(field_value),
                    }
                )

    return entries


#: Directories scanned for Python contract surface (relative to the repo root).
_PYTHON_ROOTS = ("src/llmxive", "tests")


def build_manifest(repo_root) -> dict:
    """Scan the whole repo and return the checked contract-surface manifest.

    Deterministic: entries carry repo-relative POSIX paths and are totally
    ordered, so ``build_manifest(root)`` is byte-stable across runs and machines
    (the drift test + slice-8 enforcement depend on it).
    """
    repo_root = Path(repo_root)
    entries: list[dict] = []

    for base in _PYTHON_ROOTS:
        root = repo_root / base
        if not root.exists():
            continue
        for py in sorted(root.rglob("*.py")):
            if "__pycache__" in py.parts:
                continue
            entries.extend(scan_python(py, py.relative_to(repo_root).as_posix()))

    registry = repo_root / _REGISTRY_PATH
    if registry.exists():
        entries.extend(scan_registry(registry, _REGISTRY_PATH))

    for entry in entries:
        category, owning_slice = categorize(entry)
        entry["category"] = category
        entry["owning_slice"] = owning_slice

    entries.sort(
        key=lambda e: (e["file"], e["line"], e["kind"], e["symbol"], tuple(e["models"]))
    )
    return {"schema": SCHEMA, "generated_by": GENERATED_BY, "entries": entries}


def _detail_table(entries: list[dict]) -> list[str]:
    rows = ["|file|line|kind|symbol|models|", "|-|-|-|-|-|"]
    for e in entries:
        rows.append(
            f"|{e['file']}|{e['line']}|{e['kind']}|{e['symbol']}|"
            f"{', '.join(e['models']) or '—'}|"
        )
    return rows


def _rollup_table(entries: list[dict]) -> list[str]:
    by_file: dict[str, list[dict]] = {}
    for e in entries:
        by_file.setdefault(e["file"], []).append(e)
    rows = ["|file|entries|distinct models|", "|-|-|-|"]
    for path in sorted(by_file):
        group = by_file[path]
        models = sorted({m for e in group for m in e["models"]})
        rows.append(f"|{path}|{len(group)}|{', '.join(models) or '—'}|")
    return rows


def render_markdown(manifest: dict) -> str:
    """Deterministic human-readable projection of the manifest for PR review.

    Full detail for the production migration surface; a per-file rollup for the
    bulky ``registry`` / ``test_double`` categories (the JSON keeps every line).
    """
    entries = manifest["entries"]
    counts = Counter(e["category"] for e in entries)
    out: list[str] = [
        "# Model-selection migration manifest (spec 026, Phase 2 slice M0)",
        "",
        f"Schema `{manifest['schema']}` · generated by `{manifest['generated_by']}` · "
        f"{len(entries)} contract-surface entries.",
        "",
        "Checked artifact: regenerate with `python -m llmxive.model_selection.inventory` "
        "(writes the JSON + this file); the frozen drift test asserts they match the live "
        "scan, and slice-8 `enforcement.py` consumes the JSON. `owning_slice` is advisory.",
        "",
        "## Counts by category",
        "",
        "|category|count|",
        "|-|-|",
    ]
    out.extend(f"|{cat}|{counts[cat]}|" for cat in sorted(counts))
    out.append("")

    # Full detail for the production migration surface (grouped by owning slice).
    migration = [e for e in entries if e["category"] == "migration_target"]
    out += ["## Migration targets", ""]
    for slice_ in sorted({e["owning_slice"] for e in migration}, key=lambda s: (s is None, s)):
        group = [e for e in migration if e["owning_slice"] == slice_]
        out += [f"### Slice {slice_} ({len(group)})", ""]
        out += _detail_table(group)
        out.append("")

    for cat in ("schema", "canonical_layer", "exempt"):
        group = [e for e in entries if e["category"] == cat]
        if not group:
            continue
        out += [f"## {cat} ({len(group)})", ""]
        out += _detail_table(group)
        out.append("")

    for cat in ("registry", "test_double"):
        group = [e for e in entries if e["category"] == cat]
        if not group:
            continue
        out += [
            f"## {cat} ({len(group)} entries — per-file rollup; see JSON for line detail)",
            "",
        ]
        out += _rollup_table(group)
        out.append("")

    return "\n".join(out) + "\n"


def manifest_json(manifest: dict) -> str:
    """Canonical on-disk JSON form (stable across runs — sorted, trailing NL)."""
    return json.dumps(manifest, indent=2, sort_keys=True) + "\n"


def write_manifest(repo_root) -> tuple[Path, Path]:
    """Regenerate the committed JSON + MD artifacts. Returns their paths."""
    repo_root = Path(repo_root)
    manifest = build_manifest(repo_root)
    json_path = repo_root / MANIFEST_JSON
    md_path = repo_root / MANIFEST_MD
    json_path.write_text(manifest_json(manifest))
    md_path.write_text(render_markdown(manifest))
    return json_path, md_path


if __name__ == "__main__":  # pragma: no cover - regeneration entry point
    import sys

    from llmxive.config import repo_root

    root = Path(sys.argv[1]) if len(sys.argv) > 1 else repo_root()
    written = write_manifest(root)
    for path in written:
        print(f"wrote {path}")
