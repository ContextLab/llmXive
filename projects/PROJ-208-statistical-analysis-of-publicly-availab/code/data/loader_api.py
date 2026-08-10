import json
import logging
import sys
import time
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.config import get_config

def load_config():
    cfg = get_config()
    return cfg

def get_api_token(config):
    return config["github_api_token"]


def fetch_rate_limit_status(api_token):
    # Placeholder - in a real implementation, make an API call to check rate limit.
    # Returning dummy values for now.
    return {"limit": 5000, "remaining": 4900}

def handle_rate_limit(rate_limit_info, wait_time):
  logging.warning(f"Rate limit hit.  Remaining: {rate_limit_info['remaining']}. Waiting {wait_time} seconds.")
  time.sleep(wait_time)

def fetch_issues_for_repo(repo_name, api_token, since_date):
    # Placeholder - in a real implementation, call the GitHub API to get issues.
    # Returning dummy data for now.  The date is unused here because it's only a demonstration.
    logging.info(f"Fetching issues from {repo_name}")

    if repo_name == "error_repo":
      raise Exception("Simulating API error") # Simulate an error to test exception handling

    issues = [
        {"repo": repo_name, "created_at": "2023-01-01T00:00:00Z", "closed_at": "2023-01-05T00:00:00Z"},
        {"repo": repo_name, "created_at": "2023-02-10T00:00:00Z", "closed_at": "2023-02-15T00:00:00Z"}
    ]
    return issues

def fetch_issues_from_curated_list(repo_list, api_token, since_date):
    all_issues = []
    unique_repos = set()
    for repo in repo_list:
        try:
            issues = fetch_issues_for_repo(repo, api_token, since_date)
            if repo not in unique_repos:
                all_issues.extend(issues)
                unique_repos.add(repo)

        except Exception as e:
            logging.error(f"Error fetching issues from {repo}: {e}")


    return all_issues, list(unique_repos)

def validate_and_save(data, output_path):
    # Placeholder - in a real implementation, validate the data and save it to Parquet.
    logging.info(f"Saving data to {output_path}")
    import pandas as pd
    df = pd.DataFrame(data)
    df.to_parquet(output_path)

def main():
    config = load_config()
    api_token = get_api_token(config)
    rate_limit_info = fetch_rate_limit_status(api_token)
    logging.info(f"Rate limit: {rate_limit_info}")

    curated_repo_list = ["octocat/Spoon-Knife", "google/zxnmysqlclient", "pallets/flask"] # Limited for testing
    since_date = "2020-01-01"

    issues, unique_repos = fetch_issues_from_curated_list(curated_repo_list, api_token, since_date)

    output_path = "data/raw/github_issues_raw_api.parquet"
    validate_and_save(issues, output_path)

    logging.info(f"Fetched {len(issues)} issues from {len(unique_repos)} unique repositories.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()