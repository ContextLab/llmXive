#!/usr/bin/env bash
set -e
# Run only the contract test suite.
pytest -q tests/contract
