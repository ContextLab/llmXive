# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --phase generate --seed 42 --count 500`
  - script usage: `main.py [-h] [--seed SEED] [--count COUNT] [--resume]`
  - argparse error: `main.py: error: unrecognized arguments: --phase generate`
- run-book command: `python code/main.py --phase simulate --corruption-rates 0.05,0.10,0.20 --architectures event_log,session_first`
  - script usage: `main.py [-h] [--seed SEED] [--count COUNT] [--resume]`
  - argparse error: `main.py: error: unrecognized arguments: --phase simulate --corruption-rates 0.05,0.10,0.20 --architectures event_log,session_first`
- run-book command: `python code/main.py --phase reconstruct --architectures event_log,session_first`
  - script usage: `main.py [-h] [--seed SEED] [--count COUNT] [--resume]`
  - argparse error: `main.py: error: unrecognized arguments: --phase reconstruct --architectures event_log,session_first`
- run-book command: `python code/main.py --phase analyze --test cochrans_q`
  - script usage: `main.py [-h] [--seed SEED] [--count COUNT] [--resume]`
  - argparse error: `main.py: error: unrecognized arguments: --phase analyze --test cochrans_q`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --phase generate --seed 42 --count 500 (rc=2); python code/main.py --phase simulate --corruption-rates 0.05,0.10,0.20 --architectures event_log,session_first (rc=2); python code/main.py --phase reconstruct --architectures event_log,session_first (rc=2)

## Failing / missing run-book commands

- python code/main.py --phase generate --seed 42 --count 500 -> rc=2
    usage: main.py [-h] [--seed SEED] [--count COUNT] [--resume]
               [--corruption-rate CORRUPTION_RATE] [--sweep]
main.py: error: unrecognized arguments: --phase generate
- python code/main.py --phase simulate --corruption-rates 0.05,0.10,0.20 --architectures event_log,session_first -> rc=2
    usage: main.py [-h] [--seed SEED] [--count COUNT] [--resume]
               [--corruption-rate CORRUPTION_RATE] [--sweep]
main.py: error: unrecognized arguments: --phase simulate --corruption-rates 0.05,0.10,0.20 --architectures event_log,session_first
- python code/main.py --phase reconstruct --architectures event_log,session_first -> rc=2
    usage: main.py [-h] [--seed SEED] [--count COUNT] [--resume]
               [--corruption-rate CORRUPTION_RATE] [--sweep]
main.py: error: unrecognized arguments: --phase reconstruct --architectures event_log,session_first
- python code/main.py --phase analyze --test cochrans_q -> rc=2
    usage: main.py [-h] [--seed SEED] [--count COUNT] [--resume]
               [--corruption-rate CORRUPTION_RATE] [--sweep]
main.py: error: unrecognized arguments: --phase analyze --test cochrans_q
