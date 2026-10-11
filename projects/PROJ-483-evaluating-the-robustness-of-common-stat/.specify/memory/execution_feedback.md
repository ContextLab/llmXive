# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --action download (rc=1); python code/main.py --action simulate --config data/dependency_manifest.yaml (rc=1); python code/main.py --action plot --input results/type1_error_rates.csv (rc=1)

## Failing / missing run-book commands

- python code/main.py --action download -> rc=1
datasets()  # Ensures data/raw/ exists and is valid
                ^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-483-evaluating-the-robustness-of-common-stat/code/data_loader.py", line 246, in load_datasets
    json.dump(power_reports, f, indent=2)
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/__init__.py", line 179, in dump
    for chunk in iterable:
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 430, in _iterencode
    yield from _iterencode_list(o, _current_indent_level)
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 326, in _iterencode_list
    yield from chunks
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 406, in _iterencode_dict
    yield from chunks
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 439, in _iterencode
    o = _default(o)
        ^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 180, in default
    raise TypeError(f'Object of type {o.__class__.__name__} '
TypeError: Object of type bool_ is not JSON serializable

- python code/main.py --action simulate --config data/dependency_manifest.yaml -> rc=1
datasets()  # Ensures data/raw/ exists and is valid
                ^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-483-evaluating-the-robustness-of-common-stat/code/data_loader.py", line 246, in load_datasets
    json.dump(power_reports, f, indent=2)
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/__init__.py", line 179, in dump
    for chunk in iterable:
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 430, in _iterencode
    yield from _iterencode_list(o, _current_indent_level)
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 326, in _iterencode_list
    yield from chunks
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 406, in _iterencode_dict
    yield from chunks
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 439, in _iterencode
    o = _default(o)
        ^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 180, in default
    raise TypeError(f'Object of type {o.__class__.__name__} '
TypeError: Object of type bool_ is not JSON serializable

- python code/main.py --action plot --input results/type1_error_rates.csv -> rc=1
datasets()  # Ensures data/raw/ exists and is valid
                ^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-483-evaluating-the-robustness-of-common-stat/code/data_loader.py", line 246, in load_datasets
    json.dump(power_reports, f, indent=2)
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/__init__.py", line 179, in dump
    for chunk in iterable:
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 430, in _iterencode
    yield from _iterencode_list(o, _current_indent_level)
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 326, in _iterencode_list
    yield from chunks
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 406, in _iterencode_dict
    yield from chunks
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 439, in _iterencode
    o = _default(o)
        ^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 180, in default
    raise TypeError(f'Object of type {o.__class__.__name__} '
TypeError: Object of type bool_ is not JSON serializable

- python code/main.py --action verify -> rc=1
datasets()  # Ensures data/raw/ exists and is valid
                ^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-483-evaluating-the-robustness-of-common-stat/code/data_loader.py", line 246, in load_datasets
    json.dump(power_reports, f, indent=2)
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/__init__.py", line 179, in dump
    for chunk in iterable:
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 430, in _iterencode
    yield from _iterencode_list(o, _current_indent_level)
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 326, in _iterencode_list
    yield from chunks
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 406, in _iterencode_dict
    yield from chunks
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 439, in _iterencode
    o = _default(o)
        ^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 180, in default
    raise TypeError(f'Object of type {o.__class__.__name__} '
TypeError: Object of type bool_ is not JSON serializable

