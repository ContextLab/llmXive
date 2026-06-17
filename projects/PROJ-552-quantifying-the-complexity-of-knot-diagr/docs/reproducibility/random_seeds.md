# Random Seeds

All stochastic operations in the codebase use the following fixed seeds to ensure reproducibility (per FR‑007):

```json
{
 "numpy": 42,
 "random": 12345,
 "torch": 20220617
}
```

The seeds are set at the start of each script via `numpy.random.seed`, `random.seed`, and, where applicable, `torch.manual_seed`.
