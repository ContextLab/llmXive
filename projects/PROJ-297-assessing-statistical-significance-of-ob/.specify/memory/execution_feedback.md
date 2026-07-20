# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --permutations [variable] --threshold 0.3 --sweep`
  - script usage: `main.py [-h] [--permutations PERMUTATIONS] [--threshold THRESHOLD]`
  - argparse error: `main.py: error: argument --permutations: invalid int value: '[variable]'`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/loaders.py --output data/processed/ (rc=1); python code/main.py --permutations [variable] --threshold 0.3 --sweep (rc=2); 1 declared deliverable(s) absent: data/raw/checksums.json

## Failing / missing run-book commands

- python code/loaders.py --output data/processed/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-297-assessing-statistical-significance-of-ob/code/loaders.py", line 218, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-297-assessing-statistical-significance-of-ob/code/loaders.py", line 198, in main
    parser = argparse.ArgumentParser(description="Load and process datasets")
             ^^^^^^^^
NameError: name 'argparse' is not defined
- python code/main.py --permutations [variable] --threshold 0.3 --sweep -> rc=2
    INFO:matplotlib.font_manager:Failed to extract font properties from /usr/share/fonts/truetype/noto/NotoColorEmoji.ttf: Non-scalable fonts are not supported
INFO:matplotlib.font_manager:generated new fontManager
usage: main.py [-h] [--permutations PERMUTATIONS] [--threshold THRESHOLD]
               [--sweep] [--min-datasets MIN_DATASETS] [--output OUTPUT]
main.py: error: argument --permutations: invalid int value: '[variable]'

## Declared deliverables still missing

- data/raw/checksums.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/loaders.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
