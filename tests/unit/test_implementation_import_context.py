"""Implementation context exposes real local contracts and package collisions."""
import os
import subprocess
import sys

from llmxive.speckit.implement_cmd import _inline_referenced_files, _summarize_existing_code


def test_context_exposes_the_dependency_hidden_by_a_duplicate_package(tmp_path):
    project = tmp_path/'projects/PROJ-901-imports'
    files = {
        'src/__init__.py': '# root src package\n',
        'src/utils/__init__.py': '# root utils package\n',
        'src/analysis.py': 'from .utils.tv import tv\nprint(tv([2, 3], 5))\n',
        'code/src/__init__.py': '# code src package\n',
        'code/src/utils/__init__.py': '# code utils package\n',
        'code/src/utils/tv.py': 'def tv(residue_counts, denominator):\n    """Input contains residue COUNTS, never raw per-observation residues."""\n    return sum(residue_counts) / denominator\n',
    }
    for name, body in files.items():
        path = project/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
    # Confirm the real interpreter failure: PYTHONPATH alone does not make the
    # two ordinary src.utils packages merge when project-root cwd comes first.
    result = subprocess.run([sys.executable, '-m', 'src.analysis'], cwd=project,
        env={'PATH': os.environ['PATH'], 'PYTHONPATH': str(project/'code')},
        capture_output=True, text=True, timeout=15)
    assert result.returncode != 0 and "No module named 'src.utils.tv'" in result.stderr
    api = _summarize_existing_code(project)
    assert 'tv(residue_counts, denominator)' in api
    assert 'never raw per-observation residues' in api
    assert 'IMPORT COLLISION: `src.utils`' in api
    context = _inline_referenced_files(project, '- [ ] T006 Repair src/analysis.py')
    for body in files.values():
        assert body.strip() in context


def test_absolute_import_inlines_local_module_but_not_unrelated_source(tmp_path):
    project = tmp_path/'projects/PROJ-901-absolute'
    (project/'code').mkdir(parents=True)
    (project/'code/main.py').write_text('import numpy\nfrom helper import result\nprint(result())\n')
    (project/'code/helper.py').write_text('def result():\n    return 42\n')
    (project/'code/unrelated.py').write_text('UNRELATED_SENTINEL = 99\n')
    context = _inline_referenced_files(project, 'Repair code/main.py')
    assert 'return 42' in context
    assert 'UNRELATED_SENTINEL' not in context
