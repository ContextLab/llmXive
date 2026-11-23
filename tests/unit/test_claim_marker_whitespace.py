"""Marker cleanup must not corrupt executable examples elsewhere in a document."""
import subprocess
import sys

import pytest

from llmxive.claims.gate import strip_claim_artifacts
from llmxive.execution.analysis_runner import extract_run_commands


@pytest.mark.parametrize('marker', ['[UNRESOLVED-CLAIM: c_deadbeef — missing source]', '{{claim:c_deadbeef}}'])
def test_marker_removal_preserves_real_cli_arguments(tmp_path, marker):
    script=tmp_path/'run.py'
    script.write_text('import argparse\np=argparse.ArgumentParser()\np.add_argument("--output-dir")\na=p.parse_args()\nassert a.output_dir == "./example_output"\n')
    command=f'python {script} --output-dir ./example_output'
    text=f'Prose {marker}.\n\n```bash\n{command}\n```\n'
    cleaned=strip_claim_artifacts(text)
    assert cleaned.startswith('Prose.\n')
    assert extract_run_commands(cleaned)==[command]
    import shlex
    args=shlex.split(extract_run_commands(cleaned)[0])
    subprocess.run([sys.executable,*args[1:]],check=True,capture_output=True)


def test_unrelated_python_indentation_and_alignment_are_untouched(tmp_path):
    code='if True:\n    x = "a  b"\n    assert x == "a  b"\n'
    table='name    count\nalpha   100\n'
    text='Fact [UNRESOLVED-CLAIM: c_deadbeef — missing].\n```python\n'+code+'```\n'+table
    cleaned=strip_claim_artifacts(text)
    assert code in cleaned and table in cleaned
    subprocess.run([sys.executable,'-c',code],check=True,capture_output=True)


def test_inline_command_on_marker_line_retains_argument_space():
    text='Run `python tool.py --output-dir ./out` [UNRESOLVED-CLAIM: c_deadbeef — missing].'
    assert strip_claim_artifacts(text)=='Run `python tool.py --output-dir ./out`.'


def test_newly_adjacent_relative_path_keeps_separator():
    text='Run with [UNRESOLVED-CLAIM: c_deadbeef — missing]./out'
    assert strip_claim_artifacts(text)=='Run with ./out'
