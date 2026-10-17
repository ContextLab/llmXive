# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python -m src.curators.curate_failed_figures --num-tasks 50 --output-dir data/ (rc=-1); python -m src.utils.check_retention --log-dir data/logs/ --min-valid 25 (rc=1); python -m src.analysis.wilcoxon_analysis  --validation-dir data/validation/  --output-dir outputs/ (rc=1)

## Failing / missing run-book commands

- python -m src.curators.curate_failed_figures --num-tasks 50 --output-dir data/ -> rc=-1
0498071 [01:44<56:00, 49108.69it/s]    3%|▎         | 5505024/170498071 [01:45<1:03:53, 43041.74it/s]  3%|▎         | 5537792/170498071 [01:46<54:58, 50018.13it/s]    3%|▎         | 5570560/170498071 [01:46<51:12, 53681.60it/s]  3%|▎         | 5603328/170498071 [01:47<52:10, 52677.56it/s]  3%|▎         | 5636096/170498071 [01:47<52:54, 51938.78it/s]  3%|▎         | 5668864/170498071 [01:48<53:19, 51524.52it/s]  3%|▎         | 5701632/170498071 [01:49<56:11, 48877.17it/s]  3%|▎         | 5734400/170498071 [01:49<52:50, 51965.16it/s]  3%|▎         | 5767168/170498071 [01:50<53:08, 51657.95it/s]  3%|▎         | 5799936/170498071 [01:51<53:17, 51515.70it/s]  3%|▎         | 5832704/170498071 [01:51<57:27, 47768.56it/s]  3%|▎         | 5865472/170498071 [01:52<56:18, 48731.60it/s]  3%|▎         | 5898240/170498071 [01:53<1:04:38, 42442.92it/s]  3%|▎         | 5931008/170498071 [01:53<54:02, 50746.41it/s]    3%|▎         | 5963776/170498071 [01:54<51:31, 53218.94it/s]  4%|▎         | 5996544/170498071 [01:55<51:50, 52890.18it/s]  4%|▎         | 6029312/170498071 [01:56<59:14, 46275.12it/s]  4%|▎         | 6062080/170498071 [01:56<49:59, 54816.68it/s]
[TIMEOUT after 120s]
- python -m src.utils.check_retention --log-dir data/logs/ --min-valid 25 -> rc=1

Error processing validation file: "Successful validation record missing session identifier: {'figure_id': '0', 'vector_match': True, 'semantic_pass': True, 'similarity_score': 1.0}"

- python -m src.analysis.wilcoxon_analysis  --validation-dir data/validation/  --output-dir outputs/ -> rc=1

2026-10-17 02:49:51,711 ERROR __main__: Validation records missing required columns: {'iteration_count', 'interface', 'time_to_success_ms', 'participant_id'}

- python -m pytest -q tests/contract -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract


