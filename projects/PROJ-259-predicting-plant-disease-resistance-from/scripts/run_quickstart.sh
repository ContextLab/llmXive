#!/usr/bin/env bash
set -e
# Execute the quickstart target defined in the Makefile
make quickstart
# Verify that the output file was created
if [[ -f quickstart_output.txt ]]; then
    echo "quickstart_output.txt generated successfully."
else
    echo "Error: quickstart_output.txt was not created."
    exit 1
fi