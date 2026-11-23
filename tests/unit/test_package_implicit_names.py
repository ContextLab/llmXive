"""Python supplies package globals before executing __init__.py."""
import os
import subprocess
import sys

from llmxive.speckit.implement_cmd import _find_unresolved_names


def test_real_package_path_is_not_a_missing_import(tmp_path):
    source = 'from pkgutil import extend_path\n__path__ = extend_path(__path__, __name__)\n'
    package = tmp_path/'example_package'
    package.mkdir()
    (package/'__init__.py').write_text(source)
    result = subprocess.run([sys.executable, '-c', 'import example_package; assert example_package.__path__'],
                            cwd=tmp_path, capture_output=True, text=True, timeout=15,
                            env={'PATH': os.environ['PATH']})
    assert result.returncode == 0, result.stderr
    assert _find_unresolved_names(source, filename='__init__.py') == set()
    assert _find_unresolved_names('print(__path__)\n', filename='ordinary.py') == {'__path__'}
    assert _find_unresolved_names('print(missing_module)\n', filename='__init__.py') == {'missing_module'}
