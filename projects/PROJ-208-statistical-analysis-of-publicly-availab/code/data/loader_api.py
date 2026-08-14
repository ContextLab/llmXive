import json
import logging
import sys
import time
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import requests
import pandas as pd

from utils.config import get_config

# Configuration constants
RATE_LIMIT_WAIT_SECONDS = 60
MIN_REPOS_TARGET = 100
DEFAULT_SINCE_DATE = "2020-01-01"

# Curated list of high-star repositories to fetch from
# This list is curated to ensure high-quality, active repositories with significant issue volume
CURATED_REPO_LIST = [
    "facebook/react",
    "tensorflow/tensorflow",
    "microsoft/vscode",
    "torvalds/linux",
    "nodejs/node",
    "python/cpython",
    "django/django",
    "pallets/flask",
    "spring-projects/spring-boot",
    "elastic/elasticsearch",
    "apache/spark",
    "kubernetes/kubernetes",
    "grafana/grafana",
    "prometheus/prometheus",
    "home-assistant/core",
    "redis/redis",
    "mongodb/mongodb-community-server",
    "postmanlabs/postman-app",
    "git/git",
    "openssl/openssl",
    "nginx/nginx",
    "golang/go",
    "rust-lang/rust",
    "rust-lang/cargo",
    "microsoft/TypeScript",
    "microsoft/PowerToys",
    "electron/electron",
    "vercel/next.js",
    "vuejs/vue",
    "angular/angular",
    "tailwindlabs/tailwindcss",
    "facebook/create-react-app",
    "facebook/react-native",
    "pytorch/pytorch",
    "huggingface/transformers",
    "langchain-ai/langchain",
    "streamlit/streamlit",
    "fastapi/fastapi",
    "pandas-dev/pandas",
    "scikit-learn/scikit-learn",
    "keras-team/keras",
    "opencv/opencv",
    "psf/requests",
    "urllib3/urllib3",
    "psycopg/psycopg",
    "sqlalchemy/sqlalchemy",
    "celery/celery",
    "airflow/apache-airflow",
    "dbt-labs/dbt-core",
    "dbt-labs/dbt-postgres",
    "hashicorp/terraform",
    "hashicorp/vault",
    "hashicorp/consul",
    "grafana/loki",
    "moby/moby",
    "helm/helm",
    "k3s-io/k3s",
    "rancher/rancher",
    "istio/istio",
    "linkerd/linkerd2",
    "cilium/cilium",
    "cncf/kubeflow",
    "apache/flink",
    "apache/kafka",
    "apache/pulsar",
    "apache/rocketmq",
    "apache/nifi",
    "apache/beam",
    "apache/arrow",
    "apache/iceberg",
    "apache/hudi",
    "apache/kylin",
    "apache/druid",
    "apache/superset",
    "apache/airflow",
    "apache/atlas",
    "apache/cassandra",
    "apache/hbase",
    "apache/hive",
    "apache/impala",
    "apache/spark",
    "apache/storm",
    "apache/zookeeper",
    "apache/accumulo",
    "apache/drill",
    "apache/beam",
    "apache/flink",
    "apache/kafka",
    "apache/pulsar",
    "apache/rocketmq",
    "apache/nifi",
    "apache/beam",
    "apache/arrow",
    "apache/iceberg",
    "apache/hudi",
    "apache/kylin",
    "apache/druid",
    "apache/superset",
    "apache/airflow",
    "apache/atlas",
    "apache/cassandra",
    "apache/hbase",
    "apache/hive",
    "apache/impala",
    "apache/spark",
    "apache/storm",
    "apache/zookeeper",
    "apache/accumulo",
    "apache/drill"
]

def load_config():
    cfg = get_config()
    return cfg

def get_api_token(config):
    token = config.get("github_api_token")
    if not token:
        raise ValueError("GitHub API token not found in config. Set GITHUB_TOKEN env var or config key.")
    return token

def fetch_rate_limit_status(api_token):
    url = "https://api.github.com/rate_limit"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return {
            "limit": data.get("resources", {}).get("core", {}).get("limit", 0),
            "remaining": data.get("resources", {}).get("core", {}).get("remaining", 0),
            "reset": data.get("resources", {}).get("core", {}).get("reset", 0)
        }
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch rate limit status: {e}")
        return {"limit": 0, "remaining": 0, "reset": 0}

def handle_rate_limit(rate_limit_info, wait_time=RATE_LIMIT_WAIT_SECONDS):
    if rate_limit_info["remaining"] <= 0:
        reset_time = rate_limit_info.get("reset", 0)
        if reset_time > 0:
            current_time = int(time.time())
            wait_duration = max(wait_time, reset_time - current_time + 5)
            logging.warning(f"Rate limit exhausted. Waiting {wait_duration} seconds until reset.")
        else:
            logging.warning(f"Rate limit hit. Waiting {wait_time} seconds.")
        time.sleep(wait_time)
        return True
    return False

def fetch_issues_for_repo(repo_name, api_token, since_date):
    """
    Fetches closed issues for a specific repository from GitHub API.
    Returns a list of issue dictionaries.
    """
    issues = []
    page = 1
    per_page = 100
    url = f"https://api.github.com/repos/{repo_name}/issues"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    params = {
        "state": "closed",
        "since": since_date,
        "per_page": per_page,
        "page": page,
        "sort": "updated",
        "direction": "desc"
    }

    logging.info(f"Fetching issues from {repo_name} since {since_date}")

    while True:
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            
            # Check for rate limit
            rate_info = fetch_rate_limit_status(api_token)
            if handle_rate_limit(rate_info):
                # Retry after waiting
                continue
            
            if resp.status_code == 404:
                logging.warning(f"Repository {repo_name} not found (404). Skipping.")
                break
            elif resp.status_code == 403:
                logging.error(f"Access denied to {repo_name} (403). Check token permissions.")
                break
            elif resp.status_code != 200:
                logging.error(f"Error fetching issues from {repo_name}: HTTP {resp.status_code}")
                break
            
            resp.raise_for_status()
            data = resp.json()
            
            if not data:
                break
            
            # Filter out pull requests (GitHub API returns PRs in issues endpoint)
            for item in data:
                if "pull_request" not in item:
                    issues.append({
                        "repo": repo_name,
                        "issue_number": item.get("number"),
                        "title": item.get("title"),
                        "state": item.get("state"),
                        "created_at": item.get("created_at"),
                        "closed_at": item.get("closed_at"),
                        "updated_at": item.get("updated_at"),
                        "labels": [label.get("name") for label in item.get("labels", [])],
                        "assignee": item.get("assignee", {}).get("login") if item.get("assignee") else None,
                        "user": item.get("user", {}).get("login") if item.get("user") else None,
                        "comments_count": item.get("comments", 0),
                        "body": item.get("body", "")[:500] if item.get("body") else None, # Truncate body
                        "url": item.get("html_url")
                    })
            
            # Check if we have more pages
            if len(data) < per_page:
                break
            
            page += 1
            params["page"] = page
            
            # Small delay to be polite to the API
            time.sleep(1)
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error fetching issues from {repo_name}: {e}")
            break
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error for {repo_name}: {e}")
            break

    return issues

def fetch_issues_from_curated_list(repo_list, api_token, since_date, target_repos=MIN_REPOS_TARGET):
    """
    Fetches issues from a curated list of repositories until target_repos are reached
    or the list is exhausted.
    """
    all_issues = []
    unique_repos = set()
    
    # Shuffle list to avoid bias if we stop early (optional, but good practice)
    # For deterministic testing, we keep order.
    
    for repo in repo_list:
        if len(unique_repos) >= target_repos:
            logging.info(f"Reached target of {target_repos} unique repositories. Stopping fetch.")
            break
        
        try:
            issues = fetch_issues_for_repo(repo, api_token, since_date)
            if issues:
                all_issues.extend(issues)
                unique_repos.add(repo)
                logging.info(f"Fetched {len(issues)} issues from {repo}. Total unique repos: {len(unique_repos)}")
            else:
                logging.info(f"No issues found for {repo} matching criteria.")
        except Exception as e:
            logging.error(f"Critical error fetching issues from {repo}: {e}")
            # Continue to next repo instead of failing completely
            continue

    return all_issues, list(unique_repos)

def validate_and_save(data, output_path):
    """
    Validates the fetched data and saves it to a Parquet file.
    """
    if not data:
        logging.warning("No data to save.")
        return
    
    df = pd.DataFrame(data)
    
    # Basic validation: ensure required columns exist
    required_cols = ["repo", "created_at", "closed_at"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in fetched data: {missing_cols}")
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df.to_parquet(output_path, index=False)
    logging.info(f"Saved {len(df)} issues to {output_path}")

def main():
    config = load_config()
    api_token = get_api_token(config)
    
    logging.info("Starting GitHub API Fallback Loader")
    
    # Check initial rate limit
    rate_limit_info = fetch_rate_limit_status(api_token)
    logging.info(f"Initial Rate Limit - Limit: {rate_limit_info['limit']}, Remaining: {rate_limit_info['remaining']}")
    
    # Handle rate limit before starting
    if handle_rate_limit(rate_limit_info):
        # Re-fetch rate limit after waiting
        rate_limit_info = fetch_rate_limit_status(api_token)
    
    since_date = DEFAULT_SINCE_DATE
    
    # Fetch issues from curated list
    issues, unique_repos = fetch_issues_from_curated_list(
        CURATED_REPO_LIST, 
        api_token, 
        since_date,
        target_repos=MIN_REPOS_TARGET
    )
    
    if not issues:
        raise RuntimeError("Failed to fetch any issues from the curated repository list.")
    
    output_path = "data/raw/github_issues_raw_api.parquet"
    validate_and_save(issues, output_path)
    
    logging.info(f"Completed. Fetched {len(issues)} issues from {len(unique_repos)} unique repositories.")
    logging.info(f"Unique repositories: {unique_repos}")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    main()
