"""Contract-surface inventory tests (spec 026, Phase 2 slice M0).

``inventory.py`` builds a *checked* manifest of every model-selection pin /
field / consumer across the repo, so the slice-8 enforcement test can guard the
post-migration state and the ``DEFAULT_MODEL`` / ``MODEL_FALLBACKS`` deletion is
safe. These tests pin the scanner's behavior on synthetic trees; a separate
frozen drift test (added with the committed manifest) pins the real repo.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from llmxive.model_selection.inventory import (
    MANIFEST_JSON,
    MANIFEST_MD,
    build_manifest,
    categorize,
    manifest_json,
    render_markdown,
    scan_python,
    scan_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write(path, body):
    path.write_text(dedent(body).lstrip("\n"))
    return path


def test_scan_python_ignores_comments_and_docstrings(tmp_path):
    """The whole reason M0 is AST-based, not regex: a model id mentioned only in
    a comment or docstring is NOT a pin. Only the real assignment counts."""
    src = _write(
        tmp_path / "sample.py",
        '''
        """Module doc mentions qwen.qwen3.5-122b in prose."""
        # fall back to openai.gpt-oss-120b when qwen flaps
        DEFAULT_MODEL = "qwen.qwen3.5-122b"
        def f():
            "docstring naming google.gemma-4-31B-it"
            return 1
        ''',
    )

    entries = scan_python(src, "src/llmxive/sample.py")

    kinds = {(e["kind"], tuple(e["models"])) for e in entries}
    assert kinds == {("module_constant", ("qwen.qwen3.5-122b",))}
    (only,) = entries
    assert only["file"] == "src/llmxive/sample.py"
    assert only["symbol"] == "DEFAULT_MODEL"
    assert only["line"] == 3


def test_scan_python_detects_literals_and_default_args(tmp_path):
    """Real pins take three shapes beyond a named constant: a default arg, a
    bare-family literal (no vendor prefix, e.g. ``qwen3.5-122b`` in the
    convergence revisers), and a keyword-arg literal. Each is a model_id_literal
    tagged with the enclosing symbol; none is double-counted."""
    src = _write(
        tmp_path / "m.py",
        '''
        _DEFAULT_MODEL = "openai.gpt-oss-120b"
        def judge(model: str = "openai.gpt-oss-120b"):
            return model
        def revise(self):
            return chat(model=self._model or "qwen3.5-122b")
        ''',
    )

    entries = scan_python(src, "src/llmxive/m.py")
    by_line = {e["line"]: e for e in entries}

    assert by_line[1]["kind"] == "module_constant"
    assert by_line[1]["symbol"] == "_DEFAULT_MODEL"
    assert by_line[1]["models"] == ["openai.gpt-oss-120b"]

    assert by_line[2]["kind"] == "model_id_literal"
    assert by_line[2]["symbol"] == "model"
    assert by_line[2]["models"] == ["openai.gpt-oss-120b"]

    assert by_line[5]["kind"] == "model_id_literal"
    assert by_line[5]["symbol"] == "model"
    assert by_line[5]["models"] == ["qwen3.5-122b"]

    # No literal is double-counted against its own module_constant.
    assert len(entries) == 3


def test_scan_python_call_arg_literal_not_attributed_to_assignment(tmp_path):
    """A model id buried in a call argument (``x = f(model="...")``) belongs to
    the ``model=`` keyword at its own line — NOT to the outer assignment target.
    This is the convergence-reviser shape."""
    src = _write(
        tmp_path / "rev.py",
        '''
        def revise(self):
            comments_block = summarize(
                text,
                model=self._model or "qwen3.5-122b",
                token_budget=10,
            )
            return comments_block
        ''',
    )

    entries = scan_python(src, "src/llmxive/rev.py")

    assert not any(e["symbol"] == "comments_block" for e in entries)
    lit = [e for e in entries if e["models"] == ["qwen3.5-122b"]]
    assert len(lit) == 1
    assert lit[0]["kind"] == "model_id_literal"
    assert lit[0]["symbol"] == "model"
    assert lit[0]["line"] == 4


def test_scan_python_banned_module_names_are_not_models(tmp_path):
    """Import module names (``google.generativeai``) are not model ids: a real
    Dartmouth id always carries a digit after the vendor."""
    src = _write(
        tmp_path / "guard.py",
        '''
        _BANNED = {
            "google.generativeai",
            "google.genai",
            "anthropic",
            "openai",
            "mistralai",
        }
        ''',
    )

    assert scan_python(src, "src/llmxive/pipeline/guard.py") == []


def test_scan_python_frozenset_table_stays_single_constant(tmp_path):
    """Guards the pure-data gate: a ``frozenset({...})`` table is still ONE
    module_constant (collection constructors count as data, not a call)."""
    src = _write(
        tmp_path / "d.py",
        '''
        KNOWN_FREE_MODELS = frozenset({
            "qwen.qwen3.5-122b",
            "openai.gpt-oss-120b",
        })
        ''',
    )

    entries = scan_python(src, "src/llmxive/backends/dartmouth.py")

    assert len(entries) == 1
    assert entries[0]["kind"] == "module_constant"
    assert entries[0]["symbol"] == "KNOWN_FREE_MODELS"
    assert entries[0]["models"] == ["openai.gpt-oss-120b", "qwen.qwen3.5-122b"]


def test_scan_python_fallback_table_single_entry_no_double_count(tmp_path):
    """A fallback table is ONE module_constant carrying every model in it — the
    keys/values inside are not re-emitted as standalone literals."""
    src = _write(
        tmp_path / "r.py",
        '''
        MODEL_FALLBACKS = {
            "qwen.qwen3.5-122b": ["google.gemma-4-31B-it", "openai.gpt-oss-120b"],
        }
        ''',
    )

    entries = scan_python(src, "src/llmxive/backends/router.py")

    assert len(entries) == 1
    (e,) = entries
    assert e["kind"] == "module_constant"
    assert e["symbol"] == "MODEL_FALLBACKS"
    assert e["models"] == [
        "google.gemma-4-31B-it",
        "openai.gpt-oss-120b",
        "qwen.qwen3.5-122b",
    ]


def test_scan_python_hf_slash_model_but_not_paths(tmp_path):
    """The ``Org/Model`` form is a model id; ordinary ``a/b`` path strings are
    not (the org must be a known ML org)."""
    src = _write(
        tmp_path / "l.py",
        '''
        def list_models():
            return ["Qwen/Qwen2.5-3B-Instruct"]
        CACHE_DIR = "state/model_selection"
        DOC = "see src/llmxive/foo for details"
        ''',
    )

    entries = scan_python(src, "src/llmxive/backends/local.py")

    models = sorted(m for e in entries for m in e["models"])
    assert models == ["Qwen/Qwen2.5-3B-Instruct"]


def test_scan_python_agentspec_field_definitions(tmp_path):
    """The AgentSpec schema fields carry NO model literal, so they must be
    detected by name-in-class (slice-7 schema migration surface)."""
    src = _write(
        tmp_path / "types.py",
        '''
        class AgentRegistryEntry(BaseModel):
            default_backend: BackendName
            fallback_backends: list[BackendName] = Field(default_factory=list)
            default_model: str = Field(min_length=1)
        class Other(BaseModel):
            default_model: str = "x"
        ''',
    )

    entries = scan_python(src, "src/llmxive/types.py")

    schema_fields = [e for e in entries if e["kind"] == "agentspec_field"]
    # Exactly the three fields on the schema class — NOT the ``Other`` class.
    assert len(schema_fields) == 3
    fields = {e["symbol"]: e for e in schema_fields}
    assert set(fields) == {"default_backend", "fallback_backends", "default_model"}
    for e in fields.values():
        assert e["models"] == []
    assert fields["default_backend"]["line"] == 2


def test_scan_python_field_consumers(tmp_path):
    """Reads of the three schema fields are compatibility consumers (slice 7)."""
    src = _write(
        tmp_path / "cli.py",
        '''
        def run(entry, spec):
            print(entry.default_model)
            back = entry.default_backend.value
            return spec.fallback_backends
        ''',
    )

    entries = scan_python(src, "src/llmxive/cli.py")

    consumers = {
        e["symbol"]: e for e in entries if e["kind"] == "field_consumer"
    }
    assert set(consumers) == {"default_model", "default_backend", "fallback_backends"}
    assert consumers["default_model"]["line"] == 2
    for e in consumers.values():
        assert e["models"] == []


def test_scan_registry_extracts_agent_fields_with_lines(tmp_path):
    """Every agent's three fields are recorded (162 in the real registry); only
    ``default_model`` carries a model id, and the ``deterministic-no-llm``
    sentinel carries none."""
    reg = _write(
        tmp_path / "registry.yaml",
        """
        version: 0.9.0
        agents:
        - name: brainstorm
          default_backend: dartmouth
          fallback_backends:
          - local
          default_model: qwen.qwen3.5-122b
        - name: scaffold
          default_backend: dartmouth
          fallback_backends: []
          default_model: deterministic-no-llm
        """,
    )

    entries = scan_registry(reg, "agents/registry.yaml")

    assert {e["kind"] for e in entries} == {"registry_field"}
    assert sorted(e["symbol"] for e in entries) == [
        "default_backend",
        "default_backend",
        "default_model",
        "default_model",
        "fallback_backends",
        "fallback_backends",
    ]
    # Only the qwen default_model is a model id; backends + the no-llm sentinel
    # are not.
    assert sorted(m for e in entries for m in e["models"]) == ["qwen.qwen3.5-122b"]
    dm = next(e for e in entries if e["symbol"] == "default_model" and e["models"])
    assert dm["line"] == 7


def _cat(file, kind="model_id_literal", symbol="x", models=("qwen.qwen3.5-122b",)):
    return categorize(
        {"file": file, "kind": kind, "symbol": symbol, "models": list(models)}
    )


def test_categorize_maps_paths_to_categories():
    """The canonical layer is sanctioned; router/execution_status/other prod pins
    are migration targets owned by slices 5/6/7; the no-llm sentinel is exempt."""
    assert _cat("src/llmxive/model_selection/policy.py") == ("canonical_layer", None)
    assert _cat("tests/unit/test_foo.py") == ("test_double", None)
    assert _cat("src/llmxive/backends/router.py", symbol="DEFAULT_MODEL") == (
        "migration_target",
        5,
    )
    assert _cat(
        "src/llmxive/state/execution_status.py", symbol="FREE_MODEL_TIERS"
    ) == ("migration_target", 6)
    assert _cat("src/llmxive/claims/extract.py", symbol="_DEFAULT_MODEL") == (
        "migration_target",
        7,
    )
    assert _cat(
        "src/llmxive/types.py", kind="agentspec_field", symbol="default_model", models=()
    ) == ("schema", 7)
    assert _cat(
        "agents/registry.yaml", kind="registry_field", symbol="default_model"
    ) == ("registry", 7)
    # The deterministic-no-llm sentinel: a default_model with no resolvable model.
    assert _cat(
        "agents/registry.yaml",
        kind="registry_field",
        symbol="default_model",
        models=(),
    ) == ("exempt", None)
    assert _cat(
        "agents/registry.yaml",
        kind="registry_field",
        symbol="default_backend",
        models=(),
    ) == ("registry", 7)


def _mini_repo(root):
    (root / "src/llmxive/backends").mkdir(parents=True)
    (root / "src/llmxive/backends/router.py").write_text(
        'DEFAULT_MODEL = "qwen.qwen3.5-122b"\n'
    )
    (root / "src/llmxive/model_selection").mkdir(parents=True)
    (root / "src/llmxive/model_selection/policy.py").write_text(
        'GOLDEN = "openai.gpt-oss-120b"\n'
    )
    (root / "agents").mkdir()
    (root / "agents/registry.yaml").write_text(
        "agents:\n- name: a\n  default_model: qwen.qwen3.5-122b\n"
    )
    (root / "tests").mkdir()
    (root / "tests/test_x.py").write_text('M = "openai.gpt-oss-120b"\n')


def test_build_manifest_orchestrates_categorizes_and_sorts(tmp_path):
    _mini_repo(tmp_path)

    manifest = build_manifest(tmp_path)

    assert manifest["schema"] == "llmxive-model-selection-migration/1"
    # No timestamp / absolute path may appear (drift test must be deterministic).
    assert "generated_by" in manifest and str(tmp_path) not in repr(manifest)

    triples = {(e["file"], e["category"], e["owning_slice"]) for e in manifest["entries"]}
    assert ("src/llmxive/backends/router.py", "migration_target", 5) in triples
    assert ("src/llmxive/model_selection/policy.py", "canonical_layer", None) in triples
    assert ("agents/registry.yaml", "registry", 7) in triples
    assert ("tests/test_x.py", "test_double", None) in triples

    keys = [(e["file"], e["line"], e["kind"], e["symbol"]) for e in manifest["entries"]]
    assert keys == sorted(keys)


def test_render_markdown_is_deterministic_with_counts_and_pins(tmp_path):
    _mini_repo(tmp_path)
    manifest = build_manifest(tmp_path)

    md = render_markdown(manifest)

    assert render_markdown(manifest) == md  # pure projection of the manifest
    assert manifest["schema"] in md
    # counts table reflects the categories present
    assert "canonical_layer" in md and "migration_target" in md and "registry" in md
    # migration pins are enumerated with file + models
    assert "src/llmxive/backends/router.py" in md
    assert "qwen.qwen3.5-122b" in md
    # minimal table separators per the house style
    assert "|-|-|" in md


def test_committed_manifest_is_current_with_the_live_scan():
    """The 'checked' guarantee: the committed JSON + MD are byte-identical to a
    fresh scan of the repo. A new production model pin that lands without
    regenerating this manifest (a reviewed event) fails here — which is what
    makes the slice-8 DEFAULT_MODEL / MODEL_FALLBACKS deletion safe."""
    manifest = build_manifest(REPO_ROOT)

    regen_hint = "regenerate: python -m llmxive.model_selection.inventory"
    committed_json = (REPO_ROOT / MANIFEST_JSON).read_text()
    assert committed_json == manifest_json(manifest), f"{MANIFEST_JSON} is stale — {regen_hint}"

    committed_md = (REPO_ROOT / MANIFEST_MD).read_text()
    assert committed_md == render_markdown(manifest), f"{MANIFEST_MD} is stale — {regen_hint}"
