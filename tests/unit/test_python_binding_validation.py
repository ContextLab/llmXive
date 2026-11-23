"""The pre-write guard must agree with Python's binding scopes."""
import subprocess
import sys

import pytest

from llmxive.speckit.implement_cmd import _find_unresolved_names


@pytest.mark.parametrize('source', [
    'try:\n    raise ValueError("example")\nexcept ValueError as exc:\n    print(str(exc))\n',
    'for name, value in [("example", 1)]:\n    print(name, value)\nprint(name)\n',
    'from contextlib import nullcontext\nwith nullcontext(42) as value:\n    print(value)\nprint(value)\n',
    'print([name for name in range(3) if name > 0])\n',
    'print({name for name in range(3)})\n',
    'print({name: name + 1 for name in range(3)})\n',
    'print(list(name for name in range(3)))\n',
    'print([(x, y) for x in range(3) for y in range(x)])\n',
    'print([[y for y in range(x)] for x in range(3)])\n',
])
def test_valid_bindings_execute_and_pass_guard(source):
    result = subprocess.run([sys.executable, '-c', source], capture_output=True,
                            text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert _find_unresolved_names(source) == set()


@pytest.mark.parametrize(('source', 'missing'), [
    ('print([name for name in missing])\n', 'missing'),
    ('print([name for name in name])\n', 'name'),
    ('print([name for name in range(3)]); print(name)\n', 'name'),
    ('try:\n    raise ValueError()\nexcept ValueError as exc:\n    print(exc)\nprint(exc)\n', 'exc'),
    ('try:\n    raise ValueError()\nexcept missing as exc:\n    print(exc)\n', 'missing'),
    ('print([missing for name in range(3)])\n', 'missing'),
    ('for name in missing:\n    print(name)\n', 'missing'),
])
def test_real_name_errors_remain_rejected(source, missing):
    result = subprocess.run([sys.executable, '-c', source], capture_output=True,
                            text=True, timeout=10)
    assert result.returncode != 0
    assert 'NameError' in result.stderr
    assert _find_unresolved_names(source) == {missing}
