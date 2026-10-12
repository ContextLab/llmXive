# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/cli.py compute_entropy  --input data/raw/molecules.csv  --output data/processed/molecules_entropy.csv`
  - script usage: `cli.py [-h]`
  - argparse error: `cli.py: error: unrecognized arguments: --input --output`
- run-book command: `python code/cli.py train_model  --input data/processed/molecules_entropy.csv  --target logS  --output-dir results/`
  - script usage: `cli.py [-h]`
  - argparse error: `cli.py: error: unrecognized arguments: --input --target --output-dir results/`
- run-book command: `python code/cli.py train_model  --input data/processed/molecules_entropy.csv  --target logP  --output-dir results/`
  - script usage: `cli.py [-h]`
  - argparse error: `cli.py: error: unrecognized arguments: --input --target --output-dir results/`
- run-book command: `python code/cli.py plot_correlation  --input data/processed/molecules_entropy.csv  --property logS  --output results/plots/entropy_vs_logS.png`
  - script usage: `cli.py [-h]`
  - argparse error: `cli.py: error: unrecognized arguments: --input --property --output results/plots/entropy_vs_logS.png`
- run-book command: `python code/cli.py plot_correlation  --input data/processed/molecules_entropy.csv  --property logP  --output results/plots/entropy_vs_logP.png`
  - script usage: `cli.py [-h]`
  - argparse error: `cli.py: error: unrecognized arguments: --input --property --output results/plots/entropy_vs_logP.png`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python -c " (rc=-1); python code/cli.py compute_entropy  --input data/raw/molecules.csv  --output data/processed/molecules_entropy.csv (rc=2); python code/cli.py train_model  --input data/processed/molecules_entropy.csv  --target logS  --output-dir results/ (rc=2)

## Failing / missing run-book commands

- python -c " -> rc=-1
unparseable command (shlex)
- python code/cli.py compute_entropy  --input data/raw/molecules.csv  --output data/processed/molecules_entropy.csv -> rc=2

usage: cli.py [-h]
              {compute_entropy,join_metadata,train_model,plot_correlation} ...
cli.py: error: unrecognized arguments: --input --output

- python code/cli.py train_model  --input data/processed/molecules_entropy.csv  --target logS  --output-dir results/ -> rc=2

usage: cli.py [-h]
              {compute_entropy,join_metadata,train_model,plot_correlation} ...
cli.py: error: unrecognized arguments: --input --target --output-dir results/

- python code/cli.py train_model  --input data/processed/molecules_entropy.csv  --target logP  --output-dir results/ -> rc=2

usage: cli.py [-h]
              {compute_entropy,join_metadata,train_model,plot_correlation} ...
cli.py: error: unrecognized arguments: --input --target --output-dir results/

- python code/cli.py plot_correlation  --input data/processed/molecules_entropy.csv  --property logS  --output results/plots/entropy_vs_logS.png -> rc=2

usage: cli.py [-h]
              {compute_entropy,join_metadata,train_model,plot_correlation} ...
cli.py: error: unrecognized arguments: --input --property --output results/plots/entropy_vs_logS.png

- python code/cli.py plot_correlation  --input data/processed/molecules_entropy.csv  --property logP  --output results/plots/entropy_vs_logP.png -> rc=2

usage: cli.py [-h]
              {compute_entropy,join_metadata,train_model,plot_correlation} ...
cli.py: error: unrecognized arguments: --input --property --output results/plots/entropy_vs_logP.png

