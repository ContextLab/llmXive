#!/usr/bin/env bash
set -e
black --check .
ruff .
