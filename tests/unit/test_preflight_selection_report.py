"""Spec 027 Task 18: the preflight selection report is pure and prints no rating."""

from __future__ import annotations

import llmxive.preflight as preflight
from llmxive.model_selection.profiles import PROFILES
from llmxive.preflight import selection_report
from tests.helpers.funded import CODING, REASONING, B, snapshot
from tests.helpers.replay_server import ReplayServer


def test_report_names_backends_allowance_leaderboard_and_top_candidates():
    lines = selection_report(snapshot(dartmouth=(), sources={"catalog": ("unavailable", 0.0)}))
    assert lines[0] == "backends: dartmouth=unavailable huggingface=live local=live"
    assert lines[1] == "funded allowance: $50.00/month, spent $10.00 this month, $5.00 available now (2026-11)"
    assert lines[2] == "leaderboard: live, published 2026-11-22, reasoning 20 models, coding 20 models"
    # at _REPORT_BUDGET: 8000*1e-7 + 4096*4e-7 = 0.0024384
    assert f"top candidate [cheap_structured] reasoning/economy: {B} (huggingface, funded, worst case $0.0024)" in lines
    assert f"top candidate [deep_code] coding/strong: {B} (huggingface, funded, worst case $0.0024)" in lines
    assert sum(line.startswith("top candidate [") for line in lines) == len(PROFILES)


def test_report_says_unavailable_and_none_without_raising():
    lines = selection_report(snapshot(local=False, available_usd=None))
    assert lines[1] == "funded allowance: unavailable"
    assert any(line.startswith("top candidate [deep_review] reasoning/strong: none — ") for line in lines)


def test_report_makes_no_request_and_prints_no_rating():
    with ReplayServer({}) as srv:
        lines = selection_report(snapshot())
        lines += selection_report(snapshot(local=False, available_usd=None))
    assert srv.requests == []
    ratings = {int(r[i]) for table in (REASONING, CODING) for r in table.values() for i in range(3)}
    for line in lines:
        for rating in ratings:
            assert str(rating) not in line, (rating, line)


def test_main_survives_a_snapshot_failure(monkeypatch, capsys):
    monkeypatch.setenv("DARTMOUTH_CHAT_API_KEY", "x" * 8)

    def boom(**_kw):
        raise RuntimeError("no network")

    monkeypatch.setattr(preflight, "runtime_snapshot", boom)
    preflight.main()
    out = capsys.readouterr().out
    assert "[preflight] info: selection report unavailable: RuntimeError" in out
