"""Model-calling workflow jobs must carry the Hugging Face funded-provider settings.

Workflows are parsed with a loader that RAISES on a duplicate mapping key, because
GitHub Actions rejects such files while ``yaml.safe_load`` silently keeps the last one.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

WF = Path(__file__).resolve().parents[2] / ".github" / "workflows"
WANT = {
    "HF_TOKEN": "${{ secrets.HF_TOKEN }}",
    "LLMXIVE_HF_BILL_TO": "${{ vars.LLMXIVE_HF_BILL_TO }}",
    "LLMXIVE_FUNDED_LEDGER_ANCHOR": "${{ vars.LLMXIVE_FUNDED_LEDGER_ANCHOR }}",
}


class _StrictLoader(yaml.SafeLoader):
    """SafeLoader that refuses duplicate keys in any mapping."""

    def construct_mapping(self, node, deep=False):
        seen = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=True)
            if key in seen:
                raise yaml.constructor.ConstructorError(
                    None, None, f"duplicate mapping key {key!r}", key_node.start_mark
                )
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


def _load(path: Path):
    return yaml.load(path.read_text(), Loader=_StrictLoader)


def _env_blocks(node):
    if isinstance(node, dict):
        if isinstance(node.get("env"), dict):
            yield node["env"]
        for v in node.values():
            yield from _env_blocks(v)
    elif isinstance(node, list):
        for v in node:
            yield from _env_blocks(v)


@pytest.mark.parametrize("path", sorted(WF.glob("*.yml")), ids=lambda p: p.name)
def test_workflow_has_no_duplicate_mapping_keys(path):
    _load(path)


def test_every_model_calling_env_block_carries_the_hf_settings():
    seen = 0
    for path in sorted(WF.glob("*.yml")):
        for env in _env_blocks(_load(path)):
            if "secrets.DARTMOUTH_CHAT_API_KEY" in str(env.get("DARTMOUTH_CHAT_API_KEY", "")):
                seen += 1
                assert {k: env.get(k) for k in WANT} == WANT, path.name
    assert seen >= 12


def test_bill_to_is_a_variable_never_a_secret():
    assert "secrets.LLMXIVE_HF_BILL_TO" not in "".join(p.read_text() for p in WF.glob("*.yml"))


# --- the funded ledger needs push access; pull-request code never gets it -------
# (final review A10, narrowed by the closing security fix): GitHub does not evaluate
# expressions inside ``permissions:``, so a write token is made unreachable from a
# pull request structurally — only a job whose ``if`` requires a manual dispatch on
# main may hold ``contents: write``.

_WRITE_FILES = ("llmxive-real-call-tests.yml", "llmxive-real-call-nightly.yml")
_ON_MAIN = "github.ref == 'refs/heads/main'"
_ON_DISPATCH = "github.event_name == 'workflow_dispatch'"


def _triggers(wf: dict) -> set[str]:
    on = wf.get("on", wf.get(True))  # PyYAML 1.1 reads the bare key `on` as True
    return {on} if isinstance(on, str) else set(on or ())


def _contents(job: dict) -> str | None:
    return (job.get("permissions") or {}).get("contents")


def _dispatch_only(wf: dict, job: dict) -> bool:
    """The job cannot run for any event but a manual dispatch."""
    return _ON_DISPATCH in str(job.get("if", "")) or _triggers(wf) == {"workflow_dispatch"}


@pytest.mark.parametrize("name", _WRITE_FILES)
def test_no_pull_request_runnable_job_has_contents_write(name):
    wf = _load(WF / name)
    assert wf["permissions"]["contents"] == "read"  # the workflow default stays read-only
    for job, body in wf["jobs"].items():
        if "pull_request" in _triggers(wf) and _ON_DISPATCH not in str(body.get("if", "")):
            assert _contents(body) in (None, "read"), job


@pytest.mark.parametrize("name", _WRITE_FILES)
def test_every_write_job_runs_only_on_a_dispatch_from_main(name):
    wf = _load(WF / name)
    writers = {j: b for j, b in wf["jobs"].items() if _contents(b) == "write"}
    assert writers, "the funded lane lost its push access"
    for job, body in writers.items():
        assert _ON_MAIN in str(body.get("if", "")), job
        assert _dispatch_only(wf, body), job
        assert _receives_hf(body), job  # write exists only for the funded ledger
        # a job-level block replaces the workflow-level one: every other default is kept
        for perm, level in wf["permissions"].items():
            if perm != "contents":
                assert body["permissions"].get(perm) == level, (job, perm)


def test_pull_request_jobs_do_not_run_the_funded_lane():
    wf = _load(WF / "llmxive-real-call-tests.yml")
    for job, body in wf["jobs"].items():
        if _contents(body) == "write" or not _receives_hf(body):
            continue  # a job without the HF settings cannot reach the funded lane
        for step in body.get("steps", []):
            run = step.get("run", "")
            if "pytest tests/real_call" in run:
                assert "--ignore=tests/real_call/test_hf_funded_real.py" in run, job


def test_the_gate_requires_the_funded_lane_only_when_it_can_run():
    wf = _load(WF / "llmxive-real-call-tests.yml")
    gate = wf["jobs"]["real-call"]
    assert "huggingface" in gate["needs"] and gate["if"] == "always()"
    script = gate["steps"][0]["run"]
    assert "jobs['huggingface']['result']" in script and "'skipped'" in script
    assert "workflow_dispatch" in script and "refs/heads/main" in script


def _receives_hf(job: dict) -> bool:
    return any("HF_TOKEN" in env or "LLMXIVE_HF_BILL_TO" in env for env in _env_blocks(job))


def test_prompt_eval_has_no_write_permission_anywhere():
    text = (WF / "prompt-eval.yml").read_text()
    assert ": write" not in text and "write-all" not in text
