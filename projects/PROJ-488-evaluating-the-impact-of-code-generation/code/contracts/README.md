# Contracts Module

This module provides a contract-based validation system for the llmXive pipeline,
ensuring data integrity, API consistency, and runtime correctness.

## Overview

The contracts system implements three types of validations:

1. **Data Contracts**: Validate data structures against defined schemas
2. **API Contracts**: Validate function signatures and CLI arguments
3. **Validation Contracts**: Validate preconditions and postconditions

## Usage

### Data Contracts

```python
from contracts import validate_data_contract

# Validate a code snippet
snippet_data = {
 'id': '123',
 'source': 'codesearchnet',
 'code': 'def foo(): pass',
 'length': 15,
 'language': 'python'
}

is_valid = validate_data_contract('code_snippet', snippet_data)
```

### API Contracts

```python
from contracts import CLIContract

contract = CLIContract(
 stage_name='metric_extraction',
 required_args=['input_path', 'output_path'],
 optional_args={'verbose': bool}
)

parser = contract.create_parser()
args = parser.parse_args()
is_valid = contract.validate(args)
```

### Validation Contracts

```python
from contracts import run_contract_check, file_exists

def process_data():
 # Processing logic
 return result

preconditions = {
 'input_file_exists': lambda: file_exists('/path/to/input')
}

postconditions = {
 'output_created': lambda: file_exists('/path/to/output')
}

result = run_contract_check(
 contract_name='process_data',
 preconditions=preconditions,
 postconditions=postconditions,
 execution_func=process_data
)
```

## Contract Violations

When a contract is violated, a `ContractViolationError` is raised with:
- Contract name
- Error message
- Details dictionary
- Timestamp

## Configuration

Contract behavior can be configured via `contracts_config.py`:

```python
from contracts import update_contract_config

update_contract_config({
 'strict_mode': False,
 'raise_on_violation': False
})
```
