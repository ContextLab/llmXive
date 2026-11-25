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
    "LLMXIVE_HF_BILL_TO": "${{ secrets.LLMXIVE_HF_BILL_TO }}",
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


#: Read-only jobs (``contents: read``: they cannot push the funded ledger, so Hugging
#: Face can never serve them) that still pass the funded settings. Any other read-only
#: job must NOT receive them (least privilege); listing a job here is a decision.
_READ_ONLY_WITH_HF = {
    ("llmxive-real-call-tests.yml", "dartmouth"):
        "its real-call suite runs with the settings present and the funded class failing closed",
}


def _passes_dartmouth_key(env: dict) -> bool:
    return "secrets.DARTMOUTH_CHAT_API_KEY" in str(env.get("DARTMOUTH_CHAT_API_KEY", ""))


def _job_contents(wf: dict, job: dict) -> str | None:
    """The job's effective ``contents`` permission (job block, else workflow default)."""
    perms = job.get("permissions", wf.get("permissions"))
    return perms.get("contents") if isinstance(perms, dict) else perms


def test_every_model_calling_env_block_carries_the_hf_settings_where_it_can_use_them():
    """Every env mapping passing the Dartmouth key in a job that can write the ledger,
    or in a documented read-only exception, carries the Hugging Face settings; every
    other read-only job carries none of them."""
    seen, exceptions_seen = 0, set()
    for path in sorted(WF.glob("*.yml")):
        wf = _load(path)
        top = wf.get("env") if isinstance(wf.get("env"), dict) else {}
        assert not _passes_dartmouth_key(top), path.name  # keys are scoped to jobs
        for job, body in (wf.get("jobs") or {}).items():
            can_write = _job_contents(wf, body) not in ("read", "none")
            excepted = (path.name, job) in _READ_ONLY_WITH_HF
            for env in _env_blocks(body):
                if not _passes_dartmouth_key(env):
                    continue
                seen += 1
                if excepted:
                    exceptions_seen.add((path.name, job))
                if can_write or excepted:
                    assert {k: env.get(k) for k in WANT} == WANT, (path.name, job)
                else:
                    assert not set(WANT) & set(env), (path.name, job)  # read-only: none of them
    assert seen >= 12
    assert exceptions_seen == set(_READ_ONLY_WITH_HF)  # no stale exception entries
    for (name, job) in _READ_ONLY_WITH_HF:              # an exception is a READ-ONLY job
        wf = _load(WF / name)
        assert _job_contents(wf, wf["jobs"][job]) == "read", (name, job)


def test_prompt_eval_does_not_receive_the_funded_settings():
    env = _load(WF / "prompt-eval.yml")["jobs"]["eval"]["env"]
    assert _passes_dartmouth_key(env) and not set(WANT) & set(env)


# --- read-only model jobs skip cleanly when no provider is usable -----------------

_GATE_JOBS = (("llmxive-real-call-tests.yml", "dartmouth"), ("prompt-eval.yml", "eval"))
_USABLE = "steps.providers.outputs.usable == 'true'"
_SKIP_LINE = ("no model provider usable in a read-only run "
              "(Dartmouth unreachable; Hugging Face needs a write-capable run)")


@pytest.mark.parametrize("name,job", _GATE_JOBS, ids=lambda v: v)
def test_read_only_model_job_gates_every_model_step_on_a_usable_provider(name, job):
    wf = _load(WF / name)
    body = wf["jobs"][job]
    assert _job_contents(wf, body) == "read"
    steps = body["steps"]
    gate_at = [i for i, s in enumerate(steps) if s.get("id") == "providers"]
    assert len(gate_at) == 1, "exactly one gate step"
    gate = steps[gate_at[0]]
    assert gate["run"].strip() == "python -m llmxive.checks.backends --read-only-gate"
    assert "if" not in gate and not gate.get("continue-on-error")
    before = steps[: gate_at[0]]
    assert any("pip install -e" in s.get("run", "") for s in before)  # the gate needs the package
    assert not any(k in s.get("run", "") for s in before for k in ("pytest", "promptfoo", "checks.backends"))
    after = steps[gate_at[0] + 1:]
    skip = [s for s in after if "!= 'true'" in str(s.get("if", ""))]
    assert len(skip) == 1 and skip[0]["if"] == "steps.providers.outputs.usable != 'true'"
    run = skip[0]["run"]
    assert f'echo "::notice title=Skipped::{_SKIP_LINE}"' in run
    assert f'echo "{_SKIP_LINE}" >> "$GITHUB_STEP_SUMMARY"' in run
    model_steps = [s for s in after if s is not skip[0]]
    assert model_steps
    for step in model_steps:
        assert _USABLE in str(step.get("if", "")), step.get("name")
        assert not step.get("continue-on-error"), step.get("name")


def test_the_gated_steps_are_the_model_steps_that_ran_before():
    steps = _load(WF / "llmxive-real-call-tests.yml")["jobs"]["dartmouth"]["steps"]
    gated = {s["run"] for s in steps if _USABLE in str(s.get("if", ""))}
    assert "python -m llmxive.checks.backends" in gated
    assert "pytest tests/contract -v" in gated
    assert any(r.startswith("pytest tests/real_call") and "--ignore=tests/real_call/test_hf_funded_real.py" in r
               for r in gated)
    eval_steps = _load(WF / "prompt-eval.yml")["jobs"]["eval"]["steps"]
    gated = [s for s in eval_steps if _USABLE in str(s.get("if", ""))]
    assert any("promptfoo" in s.get("run", "") for s in gated)
    upload = next(s for s in eval_steps if s.get("uses", "").startswith("actions/upload-artifact"))
    assert upload in gated and "always()" in upload["if"]


def test_the_dartmouth_job_still_must_succeed_in_the_final_gate():
    """A skip ends the job green, so the gate's 'dartmouth must be success when live'
    rule holds in both cases; the rule itself is unchanged."""
    script = _load(WF / "llmxive-real-call-tests.yml")["jobs"]["real-call"]["steps"][0]["run"]
    assert "('dartmouth', 'live')" in script and "expected = 'success' if required else 'skipped'" in script


def test_bill_to_is_a_secret_never_a_variable():
    """Actions prints a variable's value in every job log; a secret is masked."""
    assert "vars.LLMXIVE_HF_BILL_TO" not in "".join(p.read_text() for p in WF.glob("*.yml"))


def test_the_reliability_run_reaches_the_funded_ledger_from_a_repository_without_origin():
    """The acceptance test works in a fresh ``git init`` repository, so the run must
    name the ledger remote and give git credentials through the environment, and it
    must prove both in a preflight step before the hours-long run starts."""
    steps = _load(WF / "llmxive-reliability-run.yml")["jobs"]["reliability-run"]["steps"]
    names = [s.get("name") for s in steps]
    preflight, run = names.index("Funded path preflight"), names.index("Full-pipeline acceptance run")
    assert preflight < run
    assert steps[preflight]["run"] == "python scripts/ci/funded_preflight.py"
    ledger_keys = [
        "LLMXIVE_FUNDED_LEDGER_REMOTE", "LLMXIVE_LEDGER_GIT_TOKEN", "GIT_CONFIG_COUNT",
        "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0", "GIT_CONFIG_KEY_1", "GIT_CONFIG_VALUE_1",
    ]
    for index in (preflight, run):
        env = steps[index]["env"]
        assert {k: env[k] for k in ledger_keys} == {k: steps[preflight]["env"][k] for k in ledger_keys}
        assert env["LLMXIVE_FUNDED_LEDGER_REMOTE"].endswith(".git")
        assert "@" not in env["LLMXIVE_FUNDED_LEDGER_REMOTE"] and "token" not in env["LLMXIVE_FUNDED_LEDGER_REMOTE"]
        assert env["LLMXIVE_LEDGER_GIT_TOKEN"] == "${{ github.token }}"
        assert "$LLMXIVE_LEDGER_GIT_TOKEN" in env["GIT_CONFIG_VALUE_1"]
        assert "github.token" not in env["GIT_CONFIG_VALUE_1"]


# --- the funded ledger needs push access; pull-request code never gets it -------
# (final review A10, narrowed by the closing security fix): GitHub does not evaluate
# expressions inside ``permissions:``, so a write token is made unreachable from a
# pull request structurally — only a job whose ``if`` requires a manual dispatch on
# main may hold ``contents: write``.

_WRITE_FILES = ("llmxive-real-call-tests.yml", "llmxive-real-call-nightly.yml",
                "llmxive-reliability-run.yml")
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


@pytest.mark.parametrize("path", sorted(WF.glob("*.yml")), ids=lambda p: p.name)
def test_runner_context_is_used_only_inside_steps(path):
    """GitHub rejects the whole workflow ("Unrecognized named-value: 'runner'") when
    ``runner.*`` appears in a workflow- or job-level ``env``; it exists only in steps."""
    wf = _load(path)
    assert "runner." not in str(wf.get("env", ""))
    for job, body in (wf.get("jobs") or {}).items():
        assert "runner." not in str(body.get("env", "")), job
