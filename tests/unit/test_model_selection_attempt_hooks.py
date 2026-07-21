from llmxive.model_selection.execute import ExecutionResult
from llmxive.model_selection.types import ModelRef


def _ref() -> ModelRef:
    return ModelRef(backend="dartmouth", serving_endpoint="dartmouth",
                    model_id="qwen.qwen3.5-122b", model_family="qwen3.5", vendor="qwen")


def test_execution_result_carries_reservation_id():
    r = ExecutionResult(response=None, model_ref=_ref(), reserved_credits=0.0,
                        notes=(), reservation_id="qwen-qwen3-5-122b-abc123")
    assert r.reservation_id == "qwen-qwen3-5-122b-abc123"


def test_execution_result_reservation_id_defaults_none():
    r = ExecutionResult(response=None, model_ref=_ref(), reserved_credits=0.0, notes=())
    assert r.reservation_id is None
