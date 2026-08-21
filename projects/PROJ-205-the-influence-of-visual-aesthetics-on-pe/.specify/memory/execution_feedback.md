# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python 03_mixed_effects.py --input ../../data/raw/participants.csv --output ../../data/processed/mixed_effects_results.json; 2 command(s) failed: python code/analysis/01_anova.py --input ../../data/raw/participants.csv --output ../../data/processed/anova_results.json (rc=1); python code/analysis/02_pairwise.py --input ../../data/raw/participants.csv --output ../../data/processed/pairwise_results.json (rc=1)

## Failing / missing run-book commands

- python code/analysis/01_anova.py --input ../../data/raw/participants.csv --output ../../data/processed/anova_results.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-205-the-influence-of-visual-aesthetics-on-pe/code/analysis/01_anova.py", line 155, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-205-the-influence-of-visual-aesthetics-on-pe/code/analysis/01_anova.py", line 111, in main
    df = load_wide_data(args.input)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-205-the-influence-of-visual-aesthetics-on-pe/code/analysis/01_anova.py", line 22, in load_wide_data
    raise FileNotFoundError(f"Input file not found: {input_path}")
FileNotFoundError: Input file not found: ../../data/raw/participants.csv
- python code/analysis/02_pairwise.py --input ../../data/raw/participants.csv --output ../../data/processed/pairwise_results.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-205-the-influence-of-visual-aesthetics-on-pe/code/analysis/02_pairwise.py", line 124, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-205-the-influence-of-visual-aesthetics-on-pe/code/analysis/02_pairwise.py", line 92, in main
    parser = argparse.ArgumentParser(description='Run pairwise t-tests with effect sizes')
             ^^^^^^^^
NameError: name 'argparse' is not defined
- python 03_mixed_effects.py --input ../../data/raw/participants.csv --output ../../data/processed/mixed_effects_results.json -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-205-the-influence-of-visual-aesthetics-on-pe/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-205-the-influence-of-visual-aesthetics-on-pe/03_mixed_effects.py': [Errno 2] No such file or directory
