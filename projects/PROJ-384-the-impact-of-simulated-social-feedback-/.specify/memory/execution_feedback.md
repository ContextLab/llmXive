# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python 03_analysis.py; python 04_report.py; 3 command(s) failed: python code/01_ingest.py (rc=1); python code/01_ingest.py (rc=1); python code/02_metrics.py (rc=1); 2 declared deliverable(s) absent: data/processed/user_metrics.csv; data/processed/valence_sequence.csv

## Failing / missing run-book commands

- python code/01_ingest.py -> rc=1
84-the-impact-of-simulated-social-feedback-/code/01_ingest.py", line 18, in <module>
    from utils.data_validation import validate_dataframe
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/code/utils/data_validation.py", line 11, in <module>
    from utils.config import SCHEMA_FILE
ImportError: cannot import name 'SCHEMA_FILE' from 'utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/code/utils/config.py)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/code/01_ingest.py", line 25, in <module>
    from utils.data_validation import validate_dataframe
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/code/utils/data_validation.py", line 11, in <module>
    from utils.config import SCHEMA_FILE
ImportError: cannot import name 'SCHEMA_FILE' from 'utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/code/utils/config.py)

- python code/01_ingest.py -> rc=1
84-the-impact-of-simulated-social-feedback-/code/01_ingest.py", line 18, in <module>
    from utils.data_validation import validate_dataframe
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/code/utils/data_validation.py", line 11, in <module>
    from utils.config import SCHEMA_FILE
ImportError: cannot import name 'SCHEMA_FILE' from 'utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/code/utils/config.py)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/code/01_ingest.py", line 25, in <module>
    from utils.data_validation import validate_dataframe
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/code/utils/data_validation.py", line 11, in <module>
    from utils.config import SCHEMA_FILE
ImportError: cannot import name 'SCHEMA_FILE' from 'utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/code/utils/config.py)

- python code/02_metrics.py -> rc=1

[transformers] `torch_dtype` is deprecated! Use `dtype` instead!
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.

Loading weights:   0%|          | 0/201 [00:00<?, ?it/s]
Loading weights: 100%|██████████| 201/201 [00:00<00:00, 30019.05it/s]
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/code/02_metrics.py", line 310, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/code/02_metrics.py", line 248, in main
    lexicon = get_rosenberg_lexicon()
              ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/code/utils/model_loader.py", line 74, in get_rosenberg_lexicon
    raise FileNotFoundError(f"Lexicon file not found: {lexicon_path}")
FileNotFoundError: Lexicon file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/data/raw/lexicons/rosenberg_words.txt

- python 03_analysis.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/03_analysis.py': [Errno 2] No such file or directory

- python 04_report.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-384-the-impact-of-simulated-social-feedback-/04_report.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/user_metrics.csv
- data/processed/valence_sequence.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/user_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_metrics.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/user_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/valence_sequence.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_ingest.py` — IS a run-book command
    - `code/02_metrics.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/valence_sequence.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
