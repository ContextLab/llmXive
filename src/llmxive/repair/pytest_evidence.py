"""Trusted pytest plugin emitting baseline exception/frame evidence in the log.

Mounted read-only separately from model-authored source by the repair runner.
No candidate code is imported in the host process.
"""
import json
from pathlib import Path

_failures: list[dict] = []


def pytest_runtest_makereport(item, call):
    if call.excinfo is None:
        return
    root = Path(item.config.rootpath).resolve()
    frames = []
    for entry in call.excinfo.traceback:
        path = Path(entry.path).resolve()
        frames.append(str(path.relative_to(root)) if path.is_relative_to(root) else str(path))
    error = call.excinfo.value
    _failures.append({"phase": call.when, "exception": call.excinfo.typename,
                      "import_error": isinstance(error, ImportError), "frames": frames,
                      "os_errno": error.errno if isinstance(error, OSError) else None,
                      "filename": str(error.filename) if isinstance(error, OSError)
                      and error.filename is not None else None})


def pytest_terminal_summary(terminalreporter):
    terminalreporter.write_line("REPAIR_PYTEST_FAILURES=" + json.dumps(_failures))
