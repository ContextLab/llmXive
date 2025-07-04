"""GitHub CLI handler - uses gh commands as fallback when token isn't available"""

import os
import json
import subprocess
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class GitHubCLIHandler:
    """GitHub operations using gh CLI commands"""
    
    def __init__(self, repo_name: str = "ContextLab/llmXive"):
        """
        Initialize GitHub CLI handler
        
        Args:
            repo_name: Repository name (owner/repo format)
        """
        self.repo_name = repo_name
        self.owner, self.repo = repo_name.split('/')
        
        # Test if gh is available and authenticated
        if not self._test_gh_cli():
            raise RuntimeError("GitHub CLI (gh) is not available or not authenticated. Run 'gh auth login' first.")
            
    def _test_gh_cli(self) -> bool:
        """Test if gh CLI is available and authenticated"""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            logger.error("GitHub CLI (gh) not found. Please install it: https://cli.github.com/")
            return False
            
    def _run_gh_command(self, args: List[str]) -> Optional[str]:
        """Run a gh command and return output"""
        try:
            result = subprocess.run(
                ["gh"] + args,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"gh command failed: {e.stderr}")
            return None
            
    # === File Operations ===
    
    def get_file_content(self, path: str) -> Optional[str]:
        """Get decoded file content using gh"""
        output = self._run_gh_command([
            "api",
            f"repos/{self.repo_name}/contents/{path}",
            "--jq", ".content"
        ])
        
        if output:
            # Decode base64 content
            import base64
            try:
                # Remove quotes and decode
                content_b64 = output.strip('"').replace('\\n', '')
                return base64.b64decode(content_b64).decode('utf-8')
            except Exception as e:
                logger.error(f"Error decoding file content: {e}")
                return None
        return None
        
    def create_file(self, path: str, content: str, message: str) -> bool:
        """Create new file using gh"""
        import base64
        content_b64 = base64.b64encode(content.encode()).decode()
        
        data = {
            "message": message,
            "content": content_b64
        }
        
        output = self._run_gh_command([
            "api",
            f"repos/{self.repo_name}/contents/{path}",
            "-X", "PUT",
            "--input", "-"
        ], input=json.dumps(data))
        
        return output is not None
        
    def update_file(self, path: str, content: str, message: str) -> bool:
        """Update existing file using gh"""
        # First get the file SHA
        output = self._run_gh_command([
            "api",
            f"repos/{self.repo_name}/contents/{path}",
            "--jq", ".sha"
        ])
        
        if not output:
            logger.error(f"Could not get SHA for file: {path}")
            return False
            
        sha = output.strip('"')
        
        import base64
        content_b64 = base64.b64encode(content.encode()).decode()
        
        data = {
            "message": message,
            "content": content_b64,
            "sha": sha
        }
        
        output = self._run_gh_command([
            "api",
            f"repos/{self.repo_name}/contents/{path}",
            "-X", "PUT",
            "--input", "-"
        ], input=json.dumps(data))
        
        return output is not None
        
    def file_exists(self, path: str) -> bool:
        """Check if file exists using gh"""
        output = self._run_gh_command([
            "api",
            f"repos/{self.repo_name}/contents/{path}",
            "--silent"
        ])
        return output is not None
        
    # === Issue Operations ===
    
    def get_open_issues(self) -> List[Dict[str, Any]]:
        """Get all open issues using gh"""
        output = self._run_gh_command([
            "issue", "list",
            "--repo", self.repo_name,
            "--state", "open",
            "--json", "number,title,labels,createdAt,updatedAt,comments,reactionGroups",
            "--limit", "100"
        ])
        
        if output:
            try:
                issues_data = json.loads(output)
                # Convert to expected format
                issues = []
                for issue in issues_data:
                    issues.append({
                        "number": issue["number"],
                        "title": issue["title"],
                        "labels": [label["name"] for label in issue.get("labels", [])],
                        "created_at": datetime.fromisoformat(issue["createdAt"].replace('Z', '+00:00')),
                        "updated_at": datetime.fromisoformat(issue["updatedAt"].replace('Z', '+00:00')),
                        "comments": issue.get("comments", 0),
                        "reactions": self._parse_reaction_groups(issue.get("reactionGroups", []))
                    })
                return issues
            except Exception as e:
                logger.error(f"Error parsing issues: {e}")
                return []
        return []
        
    def get_issue(self, issue_number: int) -> Optional[Dict[str, Any]]:
        """Get specific issue using gh"""
        output = self._run_gh_command([
            "issue", "view",
            str(issue_number),
            "--repo", self.repo_name,
            "--json", "number,title,body,labels,createdAt,updatedAt"
        ])
        
        if output:
            try:
                return json.loads(output)
            except Exception as e:
                logger.error(f"Error parsing issue: {e}")
                return None
        return None
        
    def create_issue(self, title: str, body: str, labels: List[str] = None) -> Optional[Dict[str, Any]]:
        """Create new issue using gh"""
        cmd = [
            "issue", "create",
            "--repo", self.repo_name,
            "--title", title,
            "--body", body
        ]
        
        if labels:
            cmd.extend(["--label", ",".join(labels)])
            
        output = self._run_gh_command(cmd)
        
        if output:
            # Parse issue number from output (format: "https://github.com/owner/repo/issues/123")
            import re
            match = re.search(r'/issues/(\d+)$', output.strip())
            if match:
                issue_number = int(match.group(1))
                return self.get_issue(issue_number)
        return None
        
    def create_issue_comment(self, issue_number: int, comment: str) -> bool:
        """Add comment to issue using gh"""
        output = self._run_gh_command([
            "issue", "comment",
            str(issue_number),
            "--repo", self.repo_name,
            "--body", comment
        ])
        return output is not None
        
    def update_issue_labels(self, issue_number: int, labels: List[str]) -> bool:
        """Update issue labels using gh"""
        # Remove all existing labels first
        self._run_gh_command([
            "issue", "edit",
            str(issue_number),
            "--repo", self.repo_name,
            "--remove-label", "*"
        ])
        
        # Add new labels
        if labels:
            output = self._run_gh_command([
                "issue", "edit",
                str(issue_number),
                "--repo", self.repo_name,
                "--add-label", ",".join(labels)
            ])
            return output is not None
        return True
        
    def get_issue_reactions(self, issue_number: int) -> Dict[str, int]:
        """Get issue reactions using gh"""
        output = self._run_gh_command([
            "api",
            f"repos/{self.repo_name}/issues/{issue_number}/reactions",
            "--jq", '[.[] | .content] | group_by(.) | map({(.[0]): length}) | add'
        ])
        
        if output:
            try:
                reactions = json.loads(output) if output != "null" else {}
                # Convert GitHub reaction names to our format
                return {
                    "thumbsup": reactions.get("+1", 0),
                    "thumbsdown": reactions.get("-1", 0),
                    "heart": reactions.get("heart", 0),
                    "rocket": reactions.get("rocket", 0)
                }
            except Exception as e:
                logger.error(f"Error parsing reactions: {e}")
        
        return {"thumbsup": 0, "thumbsdown": 0, "heart": 0, "rocket": 0}
        
    def get_issue_score(self, issue_number: int) -> float:
        """Calculate issue score based on labels"""
        issue = self.get_issue(issue_number)
        if not issue:
            return 0.0
            
        score = 0.0
        labels = [label["name"] for label in issue.get("labels", [])]
        
        # Parse review scores from labels
        for label in labels:
            if label.startswith("score:"):
                try:
                    value = float(label.split(":")[-1])
                    score += value
                except ValueError:
                    pass
                    
        return score
        
    # === Repository Operations ===
    
    def get_repository_stats(self) -> Dict[str, Any]:
        """Get repository statistics using gh"""
        output = self._run_gh_command([
            "api",
            f"repos/{self.repo_name}",
            "--jq", '{"open_issues": .open_issues_count, "size": .size, "updated_at": .updated_at}'
        ])
        
        if output:
            try:
                return json.loads(output)
            except Exception as e:
                logger.error(f"Error parsing repo stats: {e}")
                
        return {"open_issues": 0, "size": 0, "updated_at": None}
        
    # === Utility Methods ===
    
    def _parse_reaction_groups(self, reaction_groups: List[Dict[str, Any]]) -> Dict[str, int]:
        """Parse reaction groups from gh CLI format"""
        reactions = {}
        for group in reaction_groups:
            content = group.get("content", "")
            count = len(group.get("users", []))
            if content == "THUMBS_UP":
                reactions["thumbsup"] = count
            elif content == "THUMBS_DOWN":
                reactions["thumbsdown"] = count
            elif content == "HEART":
                reactions["heart"] = count
            elif content == "ROCKET":
                reactions["rocket"] = count
        return reactions
    
    def _run_gh_command(self, args: List[str], input: Optional[str] = None) -> Optional[str]:
        """Run a gh command with optional input"""
        try:
            result = subprocess.run(
                ["gh"] + args,
                capture_output=True,
                text=True,
                input=input,
                check=True
            )
            return result.stdout.strip() if result.stdout else ""
        except subprocess.CalledProcessError as e:
            if "--silent" not in args:  # Don't log errors for existence checks
                logger.error(f"gh command failed: {' '.join(args)}")
                logger.error(f"Error: {e.stderr}")
            return None