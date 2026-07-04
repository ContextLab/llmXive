# Statistical Analysis of Publicly Available Election Poll Aggregates

## Project Structure

- `src/`: Source code for data processing, modeling, and evaluation
- `data/`: Raw and processed data files
- `state/`: Project state and artifact hashes
- `tests/`: Unit and integration tests
- `specs/`: Feature specifications and contracts

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Run the pipeline:
 ```bash
 python src/main.py
 ```

## Data Sources

- **FiveThirtyEight**: Primary source for poll data
- **MEDSL/FEC**: Election outcomes
- **RCP**: Excluded per project plan (see `research.md`)

## License

MIT License