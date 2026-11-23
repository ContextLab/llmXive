"""
CI Trigger Script for llmXive Project

This script triggers the GitHub Actions workflow via the API (workflow_dispatch)
and polls for completion with a timeout.

Usage:
    GITHUB_TOKEN=<token> GITHUB_REPO=<owner/repo> python code/utils/ci_trigger.py

Environment Variables:
    GITHUB_TOKEN: GitHub Personal Access Token with 'repo' scope
    GITHUB_REPO:  Repository identifier (e.g., 'llmXive/predicting-plant-disease-resistance')
    WORKFLOW_ID:  (Optional) Workflow filename or ID. Defaults to 'ci.yml'
    TIMEOUT_MINUTES: (Optional) Polling timeout in minutes. Defaults to 15.
"""

import os
import sys
import time
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

# Configuration defaults
DEFAULT_TIMEOUT_MINUTES = 15
DEFAULT_POLL_INTERVAL_SECONDS = 30
DEFAULT_WORKFLOW_FILE = "ci.yml"


class CITriggerError(Exception):
    """Custom exception for CI trigger failures."""
    pass


def get_env_var(name: str) -> str:
    """Retrieve a required environment variable."""
    value = os.getenv(name)
    if not value:
        raise CITriggerError(f"Missing required environment variable: {name}")
    return value


def make_api_request(url: str, token: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Make an authenticated request to the GitHub API.

    Args:
        url: The API endpoint URL
        token: GitHub Personal Access Token
        data: Optional JSON payload for POST requests

    Returns:
        Parsed JSON response as a dictionary

    Raises:
        CITriggerError: If the request fails or returns an error status
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
        "User-Agent": "llmXive-ci-trigger"
    }

    request_data = None
    if data:
        request_data = json.dumps(data).encode('utf-8')
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=request_data, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise CITriggerError(f"GitHub API Error {e.code}: {e.reason}. Body: {error_body}")
    except urllib.error.URLError as e:
        raise CITriggerError(f"Network error connecting to GitHub API: {e.reason}")


def trigger_workflow(owner: str, repo: str, workflow_id: str, token: str) -> int:
    """
    Trigger a workflow_dispatch event for the specified workflow.

    Args:
        owner: Repository owner
        repo: Repository name
        workflow_id: Workflow filename (e.g., 'ci.yml') or ID
        token: GitHub API token

    Returns:
        The run ID of the triggered workflow
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches"

    # Trigger with minimal payload (empty ref uses default branch)
    payload = {
        "ref": os.getenv("GITHUB_REF", "main"),
        "inputs": {
            "triggered_by": "ci_trigger.py",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
    }

    print(f"Triggering workflow: {workflow_id} on {owner}/{repo}...")
    response = make_api_request(url, token, payload)

    # The dispatch endpoint returns 204 No Content on success, so we need to fetch the run ID
    # by listing recent runs or checking the response headers if available.
    # Since 204 has no body, we'll list runs to find the new one.
    runs_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
    params = f"?workflow_id={workflow_id}&per_page=1&status=queued"
    list_url = f"{runs_url}{params}"

    # Give GitHub a moment to register the run
    time.sleep(3)

    runs_data = make_api_request(list_url, token)
    runs = runs_data.get("workflow_runs", [])

    if not runs:
        # Fallback: list all runs and filter manually if status filter fails
        all_runs_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs?workflow_id={workflow_id}&per_page=5"
        runs_data = make_api_request(all_runs_url, token)
        runs = runs_data.get("workflow_runs", [])

    if not runs:
        raise CITriggerError("Workflow triggered but no run ID could be found immediately.")

    # Assume the first run is the one we just triggered (most recent)
    run_id = runs[0]["id"]
    print(f"Workflow triggered successfully. Run ID: {run_id}")
    return run_id


def poll_run_status(owner: str, repo: str, run_id: int, token: str, timeout_seconds: int) -> str:
    """
    Poll the GitHub API for the status of a specific workflow run.

    Args:
        owner: Repository owner
        repo: Repository name
        run_id: The workflow run ID
        token: GitHub API token
        timeout_seconds: Maximum time to wait in seconds

    Returns:
        The final status string ('completed', 'failure', 'cancelled', etc.)

    Raises:
        CITriggerError: If the timeout is exceeded
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}"
    start_time = time.time()
    elapsed = 0

    print(f"Polling run {run_id} for completion (timeout: {timeout_seconds}s)...")

    while elapsed < timeout_seconds:
        try:
            response = make_api_request(url, token)
            status = response.get("status")
            conclusion = response.get("conclusion")

            print(f"  Status: {status}, Conclusion: {conclusion} (Elapsed: {int(elapsed)}s)")

            if status == "completed":
                if conclusion == "success":
                    print("✅ Workflow completed successfully.")
                    return "success"
                else:
                    print(f"❌ Workflow completed with conclusion: {conclusion}")
                    return conclusion
            elif status in ["queued", "in_progress", "waiting", "pending"]:
                time.sleep(DEFAULT_POLL_INTERVAL_SECONDS)
                elapsed = time.time() - start_time
                continue
            else:
                # Handle unexpected status
                print(f"⚠️ Unexpected status: {status}. Waiting...")
                time.sleep(DEFAULT_POLL_INTERVAL_SECONDS)
                elapsed = time.time() - start_time

        except CITriggerError as e:
            print(f"⚠️ Polling error: {e}. Retrying in {DEFAULT_POLL_INTERVAL_SECONDS}s...")
            time.sleep(DEFAULT_POLL_INTERVAL_SECONDS)
            elapsed = time.time() - start_time

    raise CITriggerError(f"Timeout reached ({timeout_seconds}s) while waiting for run {run_id} to complete.")


def main():
    """Main entry point for the CI trigger script."""
    try:
        # Configuration
        token = get_env_var("GITHUB_TOKEN")
        repo_full_name = get_env_var("GITHUB_REPO")  # e.g., "owner/repo"

        if "/" not in repo_full_name:
            raise CITriggerError("GITHUB_REPO must be in format 'owner/repo'")

        owner, repo = repo_full_name.split("/", 1)
        workflow_id = os.getenv("WORKFLOW_ID", DEFAULT_WORKFLOW_FILE)
        timeout_minutes = int(os.getenv("TIMEOUT_MINUTES", DEFAULT_TIMEOUT_MINUTES))
        timeout_seconds = timeout_minutes * 60

        print(f"--- CI Trigger Configuration ---")
        print(f"Repository: {repo_full_name}")
        print(f"Workflow: {workflow_id}")
        print(f"Timeout: {timeout_minutes} minutes")
        print(f"-----------------------------\n")

        # Step 1: Trigger the workflow
        run_id = trigger_workflow(owner, repo, workflow_id, token)

        # Step 2: Poll for completion
        final_status = poll_run_status(owner, repo, run_id, token, timeout_seconds)

        # Step 3: Exit with appropriate code
        if final_status == "success":
            sys.exit(0)
        else:
            print(f"Pipeline failed or was cancelled. Final status: {final_status}")
            sys.exit(1)

    except CITriggerError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()