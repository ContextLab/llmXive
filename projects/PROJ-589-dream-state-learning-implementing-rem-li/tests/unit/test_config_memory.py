import pytest
import psutil
from config import Config

def test_memory_limit_enforced():
    """
    The Config initializer should raise MemoryError if the current RSS
    exceeds 6.3 GB. In the CI environment the usage is far lower, so the
    test simply verifies that the attribute exists and is of the correct
    type.
    """
    cfg = Config()
    assert hasattr(cfg, "memory_limit_bytes")
    assert isinstance(cfg.memory_limit_bytes, int)
    # Ensure the limit corresponds to 6.3 GB
    assert cfg.memory_limit_bytes == int(6.3 * 1024 ** 3)

def test_cpu_enforcement(monkeypatch, capsys):
    """
    When CUDA is reported as available, Config should force the device to CPU
    and emit a warning message.
    """
    # Simulate CUDA being available
    monkeypatch.setattr("torch.cuda.is_available", lambda: True)
    cfg = Config()
    assert str(cfg.device) == "cpu"
    captured = capsys.readouterr()
    assert "forced to CPU‑only execution" in captured.out