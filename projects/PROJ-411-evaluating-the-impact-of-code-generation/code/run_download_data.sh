#!/usr/bin/env bash
set -e
python code/download_data.py --repo-list code/repo_list.txt --output data/raw/
