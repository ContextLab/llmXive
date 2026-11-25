"""Every chat request asks for English, and a task list in another script is refused.

Run 5 (2026-11-25): one reviewer answered in Chinese with translated field names,
and a tasks.md revision came back in Chinese and was accepted.
"""

from __future__ import annotations

import pytest

from llmxive.backends.base import ChatMessage, ChatResponse
from llmxive.backends.router import OUTPUT_LANGUAGE_RULE, chat_one_candidate, with_output_language
from llmxive.speckit.task_lines import TaskFormatError, refuse_non_english, validate_open_tasks


class _Recorder:
    """Backend that keeps the messages it was sent."""

    name = "prov-a"

    def __init__(self) -> None:
        self.seen: list[list[ChatMessage]] = []

    def chat(self, messages, *, model=None, max_tokens=None, temperature=None, deadline_s=None):
        self.seen.append(list(messages))
        return ChatResponse(text="ok", model=model, backend=self.name)


def test_the_rule_closes_the_last_user_message_and_leaves_the_system_message_alone():
    messages = [
        ChatMessage(role="system", content="You review plans."),
        ChatMessage(role="user", content="First."),
        ChatMessage(role="assistant", content="Reply."),
        ChatMessage(role="user", content="Go."),
    ]
    out = with_output_language(messages)
    assert out[:3] == messages[:3]  # a system-message format contract stays last and unaltered
    assert out[3] == ChatMessage(role="user", content=f"Go.\n\n{OUTPUT_LANGUAGE_RULE}")
    assert messages[3].content == "Go."  # the caller's list is untouched


def test_a_request_without_a_text_user_message_gets_a_system_message():
    parts = ChatMessage(role="user", content=())
    out = with_output_language([parts])
    assert out == [ChatMessage(role="system", content=OUTPUT_LANGUAGE_RULE), parts]


def test_the_rule_is_added_once():
    once = with_output_language([ChatMessage(role="user", content="Go.")])
    assert with_output_language(once) is once


@pytest.mark.parametrize("model", ["acme/alpha-large", None])
def test_every_candidate_call_carries_the_rule(model):
    backend = _Recorder()
    chat_one_candidate(backend, [ChatMessage(role="user", content="Go.")], model=model)
    (sent,) = backend.seen
    assert sent[-1].role == "user" and sent[-1].content.endswith(OUTPUT_LANGUAGE_RULE)


ENGLISH = """# Tasks

- [ ] T001 Sieve φ(n) for 1 ≤ n ≤ 10⁶ in `code/sieve.py` (Erdős-Kac check, π(x) table).
- [ ] T002 Quote the title 素数定理 verbatim in `paper/paper.md`.
"""

CHINESE = """# 任务

- [ ] T001 在 `code/sieve.py` 中实现整数筛法 计算每个 n 的 φ(n) 并写入 `data/phi.csv`。
- [ ] T002 在 `paper/paper.md` 中记录结果 并说明验证步骤与可重现性要求。
"""


def test_an_english_task_list_with_mathematics_and_a_short_quotation_is_accepted():
    refuse_non_english(ENGLISH)
    validate_open_tasks(ENGLISH)


def test_a_task_list_written_in_chinese_is_refused_by_the_shared_validator():
    with pytest.raises(TaskFormatError, match="not written in English"):
        validate_open_tasks(CHINESE)
