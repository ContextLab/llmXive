# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 run-book script(s) missing (plan/impl path mismatch): python code/data/filter_hyperbolic.py; python code/analysis/validate_completeness.py; python code/analysis/correlation.py; 7 command(s) failed: python -c "from code.reproducibility.logs import get_logger; logger = get_logger(); logger.log('test', 'verification')" (rc=1); python code/analysis/precision.py (rc=1); python code/analysis/exploratory.py (rc=1); 4 declared deliverable(s) absent: data/plots/complexity_visualization_examples.png; data/plots/crossing_vs_braid.png; data/processed/knots_cleaned.csv

## Failing / missing run-book commands

- python -c "from code.reproducibility.logs import get_logger; logger = get_logger(); logger.log('test', 'verification')" -> rc=1
    Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'code.reproducibility'; 'code' is not a package
- python code/data/filter_hyperbolic.py -> rc=2 [script missing]
    /opt/homebrew/Cellar/python@3.11/3.11.12/Frameworks/Python.framework/Versions/3.11/Resources/Python.app/Contents/MacOS/Python: can't open file '/Users/jmanning/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/data/filter_hyperbolic.py': [Errno 2] No such file or directory
- python code/analysis/validate_completeness.py -> rc=2 [script missing]
    /opt/homebrew/Cellar/python@3.11/3.11.12/Frameworks/Python.framework/Versions/3.11/Resources/Python.app/Contents/MacOS/Python: can't open file '/Users/jmanning/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/analysis/validate_completeness.py': [Errno 2] No such file or directory
- python code/analysis/precision.py -> rc=1
    -552-quantifying-the-complexity-of-knot-diagr/code/analysis/precision.py", line 441, in main
    result = validate_precision(
             ^^^^^^^^^^^^^^^^^^^
  File "/Users/jmanning/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/analysis/precision.py", line 269, in validate_precision
    log_operation(
TypeError: log_operation() got an unexpected keyword argument 'logger'
- python code/analysis/exploratory.py -> rc=1
    ploratory_plots
    df = load_cleaned_knots(data_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/jmanning/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/analysis/exploratory.py", line 32, in load_cleaned_knots
    raise FileNotFoundError(f"Cleaned data file not found: {data_path}")
FileNotFoundError: Cleaned data file not found: data/processed/knots_cleaned.csv
- python code/reproducibility/tie_breaking_validator.py -> rc=1
    ifying-the-complexity-of-knot-diagr/code/reproducibility/tie_breaking_validator.py", line 318, in <module>
    exit_code = main()
                ^^^^^^
  File "/Users/jmanning/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/reproducibility/tie_breaking_validator.py", line 247, in main
    log_operation(
TypeError: log_operation() got an unexpected keyword argument 'logger'
- python code/analysis/regression.py -> rc=1
    Traceback (most recent call last):
  File "/Users/jmanning/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/analysis/regression.py", line 770, in <module>
    sys.exit(main())
    ^^^
NameError: name 'sys' is not defined
- python code/analysis/residual_analysis.py -> rc=1
    is/residual_analysis.py", line 340, in <module>
    @log_operation(operation="residual_analysis", input_file="data/processed/knots_cleaned.csv", output_file="docs/reproducibility/residual_analysis.md")
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: 'LogEntry' object is not callable
- python code/analysis/correlation.py -> rc=2 [script missing]
    /opt/homebrew/Cellar/python@3.11/3.11.12/Frameworks/Python.framework/Versions/3.11/Resources/Python.app/Contents/MacOS/Python: can't open file '/Users/jmanning/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/analysis/correlation.py': [Errno 2] No such file or directory
- python code/analysis/group_comparison.py -> rc=2 [script missing]
    /opt/homebrew/Cellar/python@3.11/3.11.12/Frameworks/Python.framework/Versions/3.11/Resources/Python.app/Contents/MacOS/Python: can't open file '/Users/jmanning/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/analysis/group_comparison.py': [Errno 2] No such file or directory
- python code/reproducibility/checksums.py -> rc=2 [script missing]
    /opt/homebrew/Cellar/python@3.11/3.11.12/Frameworks/Python.framework/Versions/3.11/Resources/Python.app/Contents/MacOS/Python: can't open file '/Users/jmanning/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/reproducibility/checksums.py': [Errno 2] No such file or directory
- python code/reproducibility/validation_status.py -> rc=2 [script missing]
    /opt/homebrew/Cellar/python@3.11/3.11.12/Frameworks/Python.framework/Versions/3.11/Resources/Python.app/Contents/MacOS/Python: can't open file '/Users/jmanning/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/reproducibility/validation_status.py': [Errno 2] No such file or directory
- python code/reproducibility/quickstart_validator.py -> rc=1
    xity-of-knot-diagr/code/reproducibility/quickstart_validator.py", line 643, in main
    result = validator.validate()
             ^^^^^^^^^^^^^^^^^^^^
  File "/Users/jmanning/llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/reproducibility/quickstart_validator.py", line 73, in validate
    log_operation(
TypeError: log_operation() got an unexpected keyword argument 'logger'

## Declared deliverables still missing

- data/plots/complexity_visualization_examples.png
- data/plots/crossing_vs_braid.png
- data/processed/knots_cleaned.csv
- data/raw/knot_atlas_raw.json
