"""GitHub integration for llmXive automation"""

import os
import re
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from github import Github, GithubException
from github.Issue import Issue
from github.Repository import Repository

logger = logging.getLogger(__name__)


class GitHubHandler:
    """Comprehensive GitHub operations handler"""
    
    def __init__(self, token: Optional[str] = None, repo_name: str = "ContextLab/llmXive"):
        """
        Initialize GitHub handler
        
        Args:
            token: GitHub access token (optional - will use gh CLI if not provided)
            repo_name: Repository name (owner/repo format)
        """
        self.repo_name = repo_name
        self.project_id = "PVT_kwDOAVVqQM4A9CYq"  # llmXive project board ID
        self.use_cli = False
        self.cli_handler = None
        
        if token:
            try:
                self.github = Github(token)
                self.repo: Repository = self.github.get_repo(repo_name)
                logger.info("Using GitHub API with token")
            except GithubException as e:
                logger.warning(f"Token authentication failed: {e}")
                self._init_cli_fallback()
        else:
            logger.info("No token provided, using GitHub CLI")
            self._init_cli_fallback()
            
    def _init_cli_fallback(self):
        """Initialize CLI handler as fallback"""
        try:
            from .github_cli_handler import GitHubCLIHandler
            self.cli_handler = GitHubCLIHandler(self.repo_name)
            self.use_cli = True
            logger.info("Successfully initialized GitHub CLI handler")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize GitHub access: {e}")
        
    # === File Operations ===
    
    def get_file_content(self, path: str) -> Optional[str]:
        """Get decoded file content"""
        if self.use_cli:
            return self.cli_handler.get_file_content(path)
            
        try:
            content = self.repo.get_contents(path)
            if content.encoding == 'base64':
                return content.decoded_content.decode('utf-8')
            return None
        except GithubException as e:
            if e.status == 404:
                logger.debug(f"File not found: {path}")
            else:
                logger.error(f"Error reading {path}: {e}")
            return None
            
    def create_file(self, path: str, content: str, message: str) -> bool:
        """Create new file"""
        try:
            self.repo.create_file(
                path=path,
                message=message,
                content=content,
                branch="main"
            )
            logger.info(f"Created file: {path}")
            return True
        except GithubException as e:
            logger.error(f"Error creating {path}: {e}")
            return False
            
    def update_file(self, path: str, new_content: str, message: str) -> bool:
        """Update existing file"""
        if self.use_cli:
            return self.cli_handler.update_file(path, new_content, message)
            
        try:
            file = self.repo.get_contents(path)
            self.repo.update_file(
                path=path,
                message=message,
                content=new_content,
                sha=file.sha,
                branch="main"
            )
            logger.info(f"Updated file: {path}")
            return True
        except GithubException as e:
            logger.error(f"Error updating {path}: {e}")
            return False
            
    def file_exists(self, path: str) -> bool:
        """Check if file exists"""
        if self.use_cli:
            return self.cli_handler.file_exists(path)
            
        try:
            self.repo.get_contents(path)
            return True
        except GithubException:
            return False
            
    # === Issue Operations ===
    
    def create_issue(self, title: str, body: str, labels: List[str] = None) -> Optional[Any]:
        """Create new issue with labels"""
        if self.use_cli:
            issue_data = self.cli_handler.create_issue(title, body, labels)
            if issue_data:
                # Return a mock Issue object
                repo_name = self.repo_name
                class MockIssue:
                    def __init__(self, data):
                        self.number = data["number"]
                        self.title = data["title"]
                        self.body = data.get("body", "")
                        self.html_url = f"https://github.com/{repo_name}/issues/{data['number']}"
                return MockIssue(issue_data)
            return None
            
        try:
            # Ensure labels exist
            if labels:
                existing_labels = [l.name for l in self.repo.get_labels()]
                for label in labels:
                    if label not in existing_labels:
                        try:
                            # Create label with appropriate color
                            color = self._get_label_color(label)
                            self.repo.create_label(label, color)
                            logger.debug(f"Created label: {label}")
                        except GithubException:
                            pass  # Label might already exist
                            
            issue = self.repo.create_issue(
                title=title,
                body=body,
                labels=labels or []
            )
            logger.info(f"Created issue #{issue.number}: {title}")
            return issue
        except GithubException as e:
            logger.error(f"Error creating issue: {e}")
            return None
            
    def get_issue(self, issue_number: int) -> Optional[Any]:
        """Get issue by number"""
        if self.use_cli:
            data = self.cli_handler.get_issue(issue_number)
            if data:
                # Create mock Issue object
                class MockIssue:
                    def __init__(self, data):
                        self.number = data["number"]
                        self.title = data["title"]
                        self.body = data.get("body", "")
                        self.labels = [type('Label', (), {"name": l["name"]})() for l in data.get("labels", [])]
                return MockIssue(data)
            return None
            
        try:
            return self.repo.get_issue(issue_number)
        except GithubException:
            logger.error(f"Issue {issue_number} not found")
            return None
            
    def create_issue_comment(self, issue_number: int, comment: str) -> bool:
        """Add comment to issue"""
        if self.use_cli:
            return self.cli_handler.create_issue_comment(issue_number, comment)
            
        try:
            issue = self.repo.get_issue(issue_number)
            issue.create_comment(comment)
            logger.info(f"Added comment to issue #{issue_number}")
            return True
        except GithubException as e:
            logger.error(f"Error creating comment: {e}")
            return False
            
    def get_open_issues(self, labels: List[str] = None) -> List[Any]:
        """Get open issues, optionally filtered by labels"""
        if self.use_cli:
            # Get all issues from CLI
            cli_issues = self.cli_handler.get_open_issues()
            
            # Filter by labels if requested
            if labels:
                filtered = []
                for issue in cli_issues:
                    if any(label in issue["labels"] for label in labels):
                        filtered.append(issue)
                cli_issues = filtered
                
            # Convert to mock Issue objects
            class MockIssue:
                def __init__(self, data):
                    self.number = data["number"]
                    self.title = data["title"]
                    self.labels = [type('Label', (), {"name": l})() for l in data["labels"]]
                    self.created_at = data["created_at"]
                    self.updated_at = data["updated_at"]
                    self.comments = data["comments"]
                    
            return [MockIssue(issue) for issue in cli_issues]
            
        try:
            if labels:
                return list(self.repo.get_issues(state="open", labels=labels))
            return list(self.repo.get_issues(state="open"))
        except GithubException as e:
            logger.error(f"Error getting issues: {e}")
            return []
            
    # === Label Management ===
    
    def get_issue_score(self, issue_number: int) -> float:
        """Extract score from issue labels"""
        if self.use_cli:
            return self.cli_handler.get_issue_score(issue_number)
            
        issue = self.get_issue(issue_number)
        if not issue:
            return 0.0
            
        for label in issue.labels:
            if label.name.startswith("Score:"):
                try:
                    return float(label.name.split(":")[1].strip())
                except ValueError:
                    pass
                    
        return 0.0
        
    def update_issue_score(self, issue_number: int, new_score: float) -> bool:
        """Update score label on issue"""
        issue = self.get_issue(issue_number)
        if not issue:
            return False
            
        # Remove old score labels
        labels_to_keep = []
        for label in issue.labels:
            if not label.name.startswith("Score:"):
                labels_to_keep.append(label.name)
                
        # Add new score label
        score_label = f"Score: {new_score:.1f}"
        labels_to_keep.append(score_label)
        
        # Ensure label exists
        try:
            self.repo.create_label(score_label, "0066CC")
        except GithubException:
            pass  # Label already exists
            
        # Update issue labels
        issue.set_labels(*labels_to_keep)
        logger.info(f"Updated score for issue #{issue_number} to {new_score}")
        return True
        
    def add_keyword_labels(self, issue_number: int, keywords: List[str]) -> bool:
        """Add keyword labels to issue"""
        issue = self.get_issue(issue_number)
        if not issue:
            return False
            
        current_labels = [l.name for l in issue.labels]
        
        for keyword in keywords[:5]:  # Limit to 5 keywords
            if keyword not in current_labels:
                # Create label if needed
                try:
                    self.repo.create_label(keyword, "FFFF00")
                except GithubException:
                    pass
                current_labels.append(keyword)
                
        issue.set_labels(*current_labels)
        return True
        
    # === Project Board Operations ===
    
    def update_issue_stage(self, issue_number: int, stage: str) -> bool:
        """Update issue stage (backlog/ready/in-progress/done)"""
        if self.use_cli:
            # Get current issue
            issue_data = self.cli_handler.get_issue(issue_number)
            if not issue_data:
                return False
                
            # Get current labels
            labels = [l["name"] for l in issue_data.get("labels", [])]
            
            # Remove other stage labels
            stage_labels = ['backlog', 'ready', 'in-progress', 'done']
            labels = [l for l in labels if l not in stage_labels]
            
            # Add new stage label
            labels.append(stage.lower())
            
            # Update labels
            return self.cli_handler.update_issue_labels(issue_number, labels)
            
        issue = self.get_issue(issue_number)
        if not issue:
            return False
            
        # Get current labels
        labels = [l.name for l in issue.labels]
        
        # Remove other stage labels
        stage_labels = ['backlog', 'ready', 'in-progress', 'done']
        labels = [l for l in labels if l not in stage_labels]
        
        # Add new stage label
        labels.append(stage.lower())
        
        # Update labels
        issue.set_labels(*labels)
        logger.info(f"Updated issue #{issue_number} to stage: {stage}")
        return True
        
    # === Search Operations ===
    
    def get_backlog_ideas(self) -> List[Dict[str, Any]]:
        """Get all ideas in backlog"""
        ideas = []
        
        if self.use_cli:
            # Get issues directly from CLI
            cli_issues = self.cli_handler.get_open_issues()
            for issue in cli_issues:
                if 'backlog' in issue.get('labels', []):
                    # Get full issue details including body
                    full_issue = self.cli_handler.get_issue(issue['number'])
                    if full_issue:
                        body = full_issue.get('body', '')
                        field_match = re.search(r'\*\*Field\*\*:\s*(.+)', body)
                        field = field_match.group(1) if field_match else 'Unknown'
                        
                        ideas.append({
                            'number': issue['number'],
                            'title': issue['title'],
                            'field': field,
                            'score': self.get_issue_score(issue['number']),
                            'created_at': issue['created_at'],
                            'updated_at': issue['updated_at'],
                            'comments': issue.get('comments', 0)
                        })
        else:
            for issue in self.get_open_issues(labels=['backlog']):
                # Extract field from issue body
                field_match = re.search(r'\*\*Field\*\*:\s*(.+)', issue.body or '')
                field = field_match.group(1) if field_match else 'Unknown'
                
                ideas.append({
                    'number': issue.number,
                    'title': issue.title,
                    'field': field,
                    'score': self.get_issue_score(issue.number),
                    'created_at': issue.created_at,
                    'updated_at': issue.updated_at,
                    'comments': issue.comments
                })
            
        return ideas
        
    def find_issue_by_project_id(self, project_id: str) -> Optional[Issue]:
        """Find issue by project ID in body"""
        for issue in self.get_open_issues():
            if project_id in (issue.body or ''):
                return issue
        return None
        
    # === Repository Stats ===
    
    def get_issue_reactions(self, issue_number: int) -> Dict[str, int]:
        """Get thumbsup/thumbsdown counts"""
        if self.use_cli:
            return self.cli_handler.get_issue_reactions(issue_number)
            
        issue = self.get_issue(issue_number)
        if not issue:
            return {'thumbsup': 0, 'thumbsdown': 0}
            
        counts = {'thumbsup': 0, 'thumbsdown': 0}
        
        try:
            reactions = issue.get_reactions()
            for reaction in reactions:
                if reaction.content == '+1':
                    counts['thumbsup'] += 1
                elif reaction.content == '-1':
                    counts['thumbsdown'] += 1
        except GithubException:
            logger.warning(f"Could not get reactions for issue #{issue_number}")
            
        return counts
        
    def get_repository_stats(self) -> Dict[str, int]:
        """Get overall repository statistics"""
        if self.use_cli:
            # Get basic stats from CLI
            stats = self.cli_handler.get_repository_stats()
            
            # Count issues by stage
            open_issues = self.cli_handler.get_open_issues()
            stats.update({
                'total_issues': len(open_issues),
                'backlog_count': len([i for i in open_issues if 'backlog' in i['labels']]),
                'ready_count': len([i for i in open_issues if 'ready' in i['labels']]),
                'in_progress_count': len([i for i in open_issues if 'in-progress' in i['labels']]),
                'done_count': len([i for i in open_issues if 'done' in i['labels']])
            })
            return stats
            
        try:
            open_issues = list(self.repo.get_issues(state='open'))
            
            stats = {
                'total_issues': len(open_issues),
                'stars': self.repo.stargazers_count,
                'forks': self.repo.forks_count,
                'backlog_count': len([i for i in open_issues if any(l.name == 'backlog' for l in i.labels)]),
                'ready_count': len([i for i in open_issues if any(l.name == 'ready' for l in i.labels)]),
                'in_progress_count': len([i for i in open_issues if any(l.name == 'in-progress' for l in i.labels)]),
                'done_count': len([i for i in open_issues if any(l.name == 'done' for l in i.labels)])
            }
            
            return stats
        except GithubException as e:
            logger.error(f"Error getting repository stats: {e}")
            return {}
            
    # === Table Operations ===
    
    def insert_table_row(self, file_path: str, table_identifier: str, 
                        new_row: str, position: str = "end") -> bool:
        """Insert row into markdown table"""
        content = self.get_file_content(file_path)
        if not content:
            return False
            
        lines = content.split('\n')
        
        # Find the table
        table_start = None
        for i, line in enumerate(lines):
            if table_identifier.lower() in line.lower():
                # Look for table after this line
                for j in range(i + 1, min(i + 10, len(lines))):
                    if '|' in lines[j] and j + 1 < len(lines) and '---' in lines[j + 1]:
                        table_start = j
                        break
                        
        if table_start is None:
            logger.error(f"Table '{table_identifier}' not found in {file_path}")
            return False
            
        # Find table end
        table_end = table_start + 2  # Skip header and separator
        while table_end < len(lines) and '|' in lines[table_end]:
            table_end += 1
            
        # Insert row
        if position == "end":
            insert_pos = table_end
        else:
            try:
                insert_pos = int(position)
            except ValueError:
                insert_pos = table_end
                
        lines.insert(insert_pos, new_row)
        
        # Update file
        new_content = '\n'.join(lines)
        return self.update_file(file_path, new_content, 
                               f"Add entry to {table_identifier} table")
                               
    # === Helper Methods ===
    
    def _get_label_color(self, label: str) -> str:
        """Get appropriate color for label type"""
        if label.startswith("Score:"):
            return "0066CC"  # Blue for scores
        elif label in ['backlog', 'ready', 'in-progress', 'done']:
            return "00FF00"  # Green for stages
        elif label in ['bug', 'error']:
            return "FF0000"  # Red for bugs
        elif label in ['enhancement', 'feature']:
            return "00FFFF"  # Cyan for features
        else:
            return "FFFF00"  # Yellow for keywords/default