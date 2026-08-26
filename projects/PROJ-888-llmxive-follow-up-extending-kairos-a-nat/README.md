# llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

This project implements a discrete world model stack for Physical AI, extending the
"Kairos" architecture to evaluate the impact of quantization and noise on physical
simulation stability.

## Quickstart

1. **Setup**: Ensure Python 3.10+ and install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
2. **Data**: Run the data pipeline to fetch and process the LIBERO subset:
 ```bash
 python code/main.py --stage download --subset 50
 python code/main.py --stage process
 ```
3. **Train**: Execute the CPU-only training loop:
 ```bash
 python code/main.py --stage train
 ```
4. **Analyze**: Run stability analysis and generate reports:
 ```bash
 python code/main.py --stage analyze
 ```

## Project Structure

- `code/`: Source code for data processing, models, and analysis.
- `data/`: Raw and processed datasets, model weights.
- `results/`: Generated reports, metrics, and visualizations.
- `tests/`: Unit, contract, and integration tests.
- `logs/`: Execution logs and validation reports.

## Verification

To verify the setup, run:
```bash
python -m pytest tests/
```

## License

This project is part of the llmXive research initiative.