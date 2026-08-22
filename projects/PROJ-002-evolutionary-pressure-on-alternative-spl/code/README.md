# Evolutionary Pressure on Alternative Splicing in Primates

## Project Overview

This project analyzes evolutionary pressure on alternative splicing events across
primate species (Human, Chimp, Macaque, Marmoset) using RNA-seq data, phylogenetic
conservation scores, and statistical modeling.

## Project Structure

```
code/
├── data_models/ # Data model definitions
│ └── models.py
├── pipeline/ # Pipeline scripts
│ ├── download.py
│ ├── align.py
│ ├── quantify.py
│ ├── detect_events.py
│ ├── hash_manifest.py
│ ├── lifecycle.py
│ └──...
├── utils/ # Utility modules
│ ├── logger.py
│ ├── hash.py
│ └── config_loader.py
├── tests/ # Test suite
│ ├── unit/
│ ├── integration/
│ └── contract/
├── config/ # Configuration files
│ └── genomes.yaml
├── data/ # Data storage (gitignored)
│ ├── raw/
│ └── processed/
└── figures/ # Output figures (gitignored)
```

## Setup

1. Create Python 3.11 virtual environment:
 ```bash
 python3.11 -m venv venv
 source venv/bin/activate
 ```

2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

3. Install R dependencies (if using R scripts):
 ```R
 install.packages(c("phylolm", "ape", "data.table", "ggplot2"))
 ```

4. Initialize pre-commit hooks:
 ```bash
 pre-commit install
 ```

## Running the Pipeline

Execute the full pipeline:
```bash
python code/pipeline/main.py --config config/genomes.yaml
```

## Testing

Run all tests:
```bash
pytest code/tests/
```

Run specific test categories:
```bash
pytest code/tests/unit/
pytest code/tests/integration/
pytest code/tests/contract/
```

## Linting and Formatting

Check code style:
```bash
flake8 code/
black --check code/
```

Format code:
```bash
black code/
```

## Artifact Hashing

All intermediate and final files are hashed using SHA-256. Hashes are:
- Logged to `pipeline.log` at each step
- Stored in `artifacts_manifest.json`
- Verified before downstream processing

## License

MIT License
