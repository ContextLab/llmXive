"""GitHub integration layer for managing issues, projects, and commits"""

import os
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from github import Github, GithubException
from github.Issue import Issue
from github.Repository import Repository
import base64

logger = logging.getLogger(__name__)


class GitHubManager:
    """Manages all interactions with GitHub API"""
    
    PROJECT_ID = "PVT_kwDOAVVqQM4A9CYq"
    STATUS_FIELD_ID = "PVTSSF_lADOAVVqQM4A9CYqzgw2-6c"
    
    STATUS_OPTIONS = {
        "Backlog": "f75ad846",
        "Ready": "61e4505c",
        "In progress": "47fc9ee4",
        "In review": "df73e18b",
        "Done": "98236657"
    }
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub manager
        
        Args:
            token: GitHub API token (uses GITHUB_TOKEN env var if not provided)
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GitHub token required")
            
        self.github = Github(self.token)
        self.repo = self.github.get_repo("ContextLab/llmXive")
        
    def get_project_state(self) -> Dict[str, List[Dict]]:
        """
        Get current state of the project board
        
        Returns:
            Dict mapping status to list of issues
        """
        state = {status: [] for status in self.STATUS_OPTIONS.keys()}
        
        try:
            # Get all open issues
            issues = self.repo.get_issues(state="open")
            
            for issue in issues:
                issue_data = {
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "labels": [label.name for label in issue.labels],
                    "created_at": issue.created_at,
                    "updated_at": issue.updated_at,
                    "comments": issue.comments
                }
                
                # Determine status (would need GraphQL for actual project status)
                # For now, use labels as a proxy
                if "done" in [l.lower() for l in issue_data["labels"]]:
                    state["Done"].append(issue_data)
                elif "in-review" in [l.lower() for l in issue_data["labels"]]:
                    state["In review"].append(issue_data)
                elif "in-progress" in [l.lower() for l in issue_data["labels"]]:
                    state["In progress"].append(issue_data)
                elif "ready" in [l.lower() for l in issue_data["labels"]]:
                    state["Ready"].append(issue_data)
                else:
                    state["Backlog"].append(issue_data)
                    
        except GithubException as e:
            logger.error(f"Error fetching project state: {e}")
            
        return state
    
    def create_issue(self, title: str, body: str, labels: Optional[List[str]] = None) -> Optional[Issue]:
        """
        Create a new issue and add to project board
        
        Args:
            title: Issue title
            body: Issue body (markdown)
            labels: Optional list of label names
            
        Returns:
            Created Issue object or None if failed
        """
        try:
            issue = self.repo.create_issue(
                title=title,
                body=body,
                labels=labels or []
            )
            logger.info(f"Created issue #{issue.number}: {title}")
            
            # Add to project board (would use GraphQL API)
            self._add_issue_to_project(issue)
            
            return issue
            
        except GithubException as e:
            logger.error(f"Error creating issue: {e}")
            return None
    
    def update_issue_status(self, issue_number: int, new_status: str) -> bool:
        """
        Update issue status on project board
        
        Args:
            issue_number: Issue number
            new_status: New status (must be in STATUS_OPTIONS)
            
        Returns:
            True if successful
        """
        if new_status not in self.STATUS_OPTIONS:
            logger.error(f"Invalid status: {new_status}")
            return False
            
        try:
            issue = self.repo.get_issue(issue_number)
            
            # Update labels to reflect status (simplified approach)
            # In production, would use GraphQL to update project field
            current_labels = [l.name for l in issue.labels]
            
            # Remove old status labels
            status_labels = ["backlog", "ready", "in-progress", "in-review", "done"]
            new_labels = [l for l in current_labels if l.lower() not in status_labels]
            
            # Add new status label
            new_labels.append(new_status.lower().replace(" ", "-"))
            
            issue.set_labels(*new_labels)
            logger.info(f"Updated issue #{issue_number} status to {new_status}")
            return True
            
        except GithubException as e:
            logger.error(f"Error updating issue status: {e}")
            return False
    
    def commit_files(self, files: Dict[str, str], message: str, branch: str = "main") -> bool:
        """
        Commit multiple files to repository
        
        Args:
            files: Dict mapping file paths to contents
            message: Commit message
            branch: Branch name (default: main)
            
        Returns:
            True if successful
        """
        try:
            # Get the branch
            branch_ref = self.repo.get_branch(branch)
            
            # Get the tree of the latest commit
            base_tree = self.repo.get_git_tree(branch_ref.commit.sha)
            
            # Create tree elements for new/modified files
            tree_elements = []
            for file_path, content in files.items():
                blob = self.repo.create_git_blob(content, "utf-8")
                element = {
                    "path": file_path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob.sha
                }
                tree_elements.append(element)
            
            # Create new tree
            new_tree = self.repo.create_git_tree(tree_elements, base_tree)
            
            # Create commit
            commit_message = f"{message}\n\n🤖 Generated with llmXive Automation"
            new_commit = self.repo.create_git_commit(
                message=commit_message,
                tree=new_tree,
                parents=[branch_ref.commit.commit]
            )
            
            # Update branch reference
            branch_ref.edit(sha=new_commit.sha)
            
            logger.info(f"Committed {len(files)} files: {message}")
            return True
            
        except GithubException as e:
            logger.error(f"Error committing files: {e}")
            return False
    
    def get_file_content(self, path: str, branch: str = "main") -> Optional[str]:
        """
        Get content of a file from repository
        
        Args:
            path: File path in repository
            branch: Branch name
            
        Returns:
            File content as string or None if not found
        """
        try:
            content = self.repo.get_contents(path, ref=branch)
            if content.encoding == "base64":
                return base64.b64decode(content.content).decode("utf-8")
            else:
                return content.decoded_content.decode("utf-8")
                
        except GithubException as e:
            logger.debug(f"File not found: {path}")
            return None
    
    def list_directory(self, path: str = "", branch: str = "main") -> List[Dict[str, str]]:
        """
        List contents of a directory
        
        Args:
            path: Directory path (empty for root)
            branch: Branch name
            
        Returns:
            List of dicts with name, path, and type
        """
        try:
            contents = self.repo.get_contents(path, ref=branch)
            
            if not isinstance(contents, list):
                contents = [contents]
                
            return [
                {
                    "name": item.name,
                    "path": item.path,
                    "type": item.type
                }
                for item in contents
            ]
            
        except GithubException as e:
            logger.error(f"Error listing directory {path}: {e}")
            return []
    
    def add_review_score(self, issue_number: int, reviewer: str, score: float) -> bool:
        """
        Add review score to an issue (LLM: 0.5 points, Human: 1.0 points)
        
        Args:
            issue_number: Issue number
            reviewer: Reviewer identifier
            score: Review score
            
        Returns:
            True if successful
        """
        try:
            issue = self.repo.get_issue(issue_number)
            
            # Add comment with review score
            comment_body = f"**Review Score**: {score} points\n**Reviewer**: {reviewer}\n**Type**: {'Automated (LLM)' if score == 0.5 else 'Manual (Human)'}"
            issue.create_comment(comment_body)
            
            # Update labels to track score
            current_labels = [l.name for l in issue.labels]
            
            # Calculate total score from existing labels
            total_score = 0
            score_labels = [l for l in current_labels if l.startswith("score:")]
            for label in score_labels:
                try:
                    total_score = float(label.split(":")[1])
                except:
                    pass
            
            # Add new score
            total_score += score
            
            # Update labels
            new_labels = [l for l in current_labels if not l.startswith("score:")]
            new_labels.append(f"score:{total_score}")
            
            issue.set_labels(*new_labels)
            
            logger.info(f"Added review score {score} to issue #{issue_number}, total: {total_score}")
            return True
            
        except GithubException as e:
            logger.error(f"Error adding review score: {e}")
            return False
    
    def _add_issue_to_project(self, issue: Issue) -> bool:
        """Add issue to project board (simplified - would use GraphQL)"""
        # This is a placeholder - actual implementation would use GraphQL API
        # to add the issue to the project board with proper status
        return True
    
    def search_issues(self, query: str) -> List[Issue]:
        """
        Search issues in the repository
        
        Args:
            query: Search query
            
        Returns:
            List of matching issues
        """
        try:
            # Construct search query
            full_query = f"repo:ContextLab/llmXive is:issue {query}"
            return list(self.github.search_issues(full_query))
        except GithubException as e:
            logger.error(f"Error searching issues: {e}")
            return []