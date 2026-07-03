# PROJ-729: Empirical Analysis of Twin Prime Gaps up to 10⁹

This project investigates whether normalized twin-prime gaps follow an exponential distribution,
testing hypotheses derived from Cramér's probabilistic model of primes.

## Project Structure

```
projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/
├── code/ # Implementation scripts
│ ├── config.py # Configuration loader
│ ├── utils.py # Utility functions
│ ├── setup_data_dirs.py # Data directory setup
│ └── generate_primes.py # Prime generation (to be implemented)
├── data/ # Data storage
│ ├── raw/ # Raw generated data
│ ├── results/ # Analysis results
│ └── figures/ # Generated plots
├── contracts/ # Data schemas
│ └── twin_prime_schema.schema.yaml
├── tests/ # Test suite
│ ├── unit/
│ └── integration/
├── specs/ # Feature specifications
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Quick Start

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. Setup data directories:
 ```bash
 python code/setup_data_dirs.py
 ```

3. Run tests:
 ```bash
 pytest tests/
 ```

## License

MIT License
