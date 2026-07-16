# Quick Start Guide

## Prerequisites

- Python 3.9+
- R 4.0+ (with Bioconductor)
- Make

## Setup

1. Clone the repository.
2. Install Python dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Install R dependencies (see `T003` implementation).

## Running the Pipeline

```bash
make all
```

## Validation

Ensure all output files match the defined schemas:
```bash
make validate
```
