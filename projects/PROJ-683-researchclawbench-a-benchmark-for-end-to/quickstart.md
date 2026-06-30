# ResearchClawBench Scoring Engine Demo

This demo reproduces the core quantitative evaluation logic of the **ResearchClawBench** paper. Instead of running the full autonomous agent loop (which requires LLM APIs and hours of time), it:

1.  Loads a real benchmark task (`Astronomy_000`) with real data.
2.  Simulates a "Perfect Agent" that generates a report and figures satisfying the target checklist.
3.  Runs the **Scoring Engine** to calculate the score based on the rubric.
4.  Outputs the real quantitative result (Score) and a breakdown.

## Prerequisites

- Python 3.9+
- `pip install pyyaml` (if not already installed)

## Run Commands

```bash
python code/score_demo.py
```

## Expected Output

The script will print the calculated score (expected ~100.00 for the perfect simulation) and save a detailed JSON report to `data/score_Astronomy_000.json`.
