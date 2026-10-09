"""Static implementation guards must agree with actual Python package imports."""
import os
import subprocess
import sys

import pytest
from llmxive.speckit.implement_cmd import _find_bad_sibling_imports


@pytest.mark.parametrize('files,statement,expected', [
    ({'pkg/__init__.py': '', 'pkg/validation.py': 'VALUE = 42\n'},
     'from pkg import validation\nprint(validation.VALUE)', '42'),
    ({'pkg/__init__.py': '', 'pkg/child/__init__.py': 'VALUE = 43\n'},
     'from pkg import child\nprint(child.VALUE)', '43'),
    ({'pkg/__init__.py': '', 'pkg/child/module.py': 'VALUE = 44\n'},
     'from pkg import child\nprint(child.__name__)', 'pkg.child'),
    ({'pkg/__init__.py': '__all__ = ["public"]\npublic = 1\nprivate = 45\n'},
     'from pkg import private\nprint(private)', '45'),
])
def test_valid_explicit_package_imports_pass_guard_and_real_interpreter(tmp_path, files, statement, expected):
    for name, body in files.items():
        path = tmp_path/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
    target = tmp_path/'check.py'
    target.write_text(statement)
    actual = subprocess.run([sys.executable, str(target)], cwd=tmp_path,
        env={'PATH': os.environ.get('PATH','')}, capture_output=True, text=True, timeout=10)
    assert actual.returncode == 0, actual.stderr
    assert actual.stdout.strip() == expected
    assert _find_bad_sibling_imports(statement, tmp_path, target) == []


def test_genuinely_missing_package_member_still_rejected(tmp_path):
    (tmp_path/'pkg').mkdir()
    (tmp_path/'pkg/__init__.py').write_text('__all__ = ["imagined"]\n')
    statement = 'from pkg import imagined'
    actual = subprocess.run([sys.executable,'-c',statement], cwd=tmp_path,
        env={'PATH': os.environ.get('PATH','')}, capture_output=True, text=True, timeout=10)
    assert actual.returncode != 0 and 'ImportError' in actual.stderr
    bad = _find_bad_sibling_imports(statement,tmp_path,tmp_path/'check.py')
    assert len(bad) == 1 and bad[0][:2] == ('pkg', 'imagined')
