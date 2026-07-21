import time
import requests
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin
import os

class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "llmXive-Research-Agent"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        url = urljoin(self.base_url, endpoint)
        max_retries = 3
        delay = 1
        
        for attempt in range(max_retries):
            try:
                response = requests.request(method, url, headers=self.headers, **kwargs)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
                elif response.status_code == 403:
                    # Rate limit
                    reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                    wait_time = max(reset_time - int(time.time()), 0) + 1
                    time.sleep(wait_time)
                    continue
                else:
                    response.raise_for_status()
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(delay)
                delay *= 2
        return None

    def get_repo(self, owner: str, name: str) -> Optional[Dict[str, Any]]:
        return self._request("GET", f"/repos/{owner}/{name}")

    def get_pull_requests(self, owner: str, name: str, state: str = "closed", per_page: int = 100) -> List[Dict[str, Any]]:
        endpoint = f"/repos/{owner}/{name}/pulls?state={state}&per_page={per_page}"
        return self._request("GET", endpoint) or []

    def get_commits(self, owner: str, name: str, per_page: int = 50) -> List[Dict[str, Any]]:
        endpoint = f"/repos/{owner}/{name}/commits?per_page={per_page}"
        return self._request("GET", endpoint) or []

    def get_contents(self, owner: str, name: str, path: str = "") -> List[Dict[str, Any]]:
        endpoint = f"/repos/{owner}/{name}/contents/{path}"
        return self._request("GET", endpoint) or []

    def get_file_content(self, owner: str, name: str, path: str) -> str:
        endpoint = f"/repos/{owner}/{name}/contents/{path}"
        data = self._request("GET", endpoint)
        if data and "content" in data:
            import base64
            return base64.b64decode(data["content"]).decode("utf-8")
        return ""

    def get_languages(self, owner: str, name: str) -> Dict[str, int]:
        endpoint = f"/repos/{owner}/{name}/languages"
        return self._request("GET", endpoint) or {}
