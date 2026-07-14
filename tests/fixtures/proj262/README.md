# Frozen PROJ-262 evidence (data-contract regression)

The REAL code + produced `results/metrics.csv` from PROJ-262's failing execution run
at commit `404a05f434` (2026-06-28) — the run whose producer wrote
`seed,model_type,MAE,RMSE` while its consumers required `mae,rmse,model`, the schema
mismatch the implementer thrashed on for 12 fix rounds.

`tests/unit/test_data_contract.py` used to read this evidence from LIVE state
(`state/execution_status/…json` + the live project tree). The pipeline rewrites both
on every execution attempt, so the evidence moved underneath the test and it failed
while the code it guards was fine. A regression test must not depend on mutable
production state — so the evidence is frozen here, verbatim and unmodified.
