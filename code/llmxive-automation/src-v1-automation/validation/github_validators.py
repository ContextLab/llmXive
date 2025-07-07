"""GitHub validators for llmXive project state."""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
import logging
from dataclasses import dataclass
from datetime import datetime

from .base import BaseValidator, ValidationResult
from scoring.stage_manager import ProjectStage

logger = logging.getLogger(__name__)


@dataclass
class GitHubIssue:
    """Representation of a GitHub issue."""
    number: int
    title: str
    state: str  # open, closed
    labels: List[str]
    body: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    assignees: List[str] = None
    milestone: Optional[str] = None
    
    def has_label(self, label: str) -> bool:
        """Check if issue has a specific label."""
        return label.lower() in [l.lower() for l in self.labels]


@dataclass
class ProjectCard:
    """Representation of a GitHub project card."""
    id: int
    column: str
    issue_number: Optional[int] = None
    note: Optional[str] = None


class GitHubIssueValidator(BaseValidator):
    """Validator for GitHub issues."""
    
    # Expected labels for each stage
    STAGE_LABELS = {
        ProjectStage.BACKLOG: ["backlog"],
        ProjectStage.READY: ["ready"],
        ProjectStage.IN_PROGRESS: ["in-progress", "in progress"],
        ProjectStage.IN_REVIEW: ["in-review", "in review"],
        ProjectStage.DONE: ["done", "completed"]
    }
    
    def validate(self, item_id: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate a GitHub issue.
        
        Args:
            item_id: Issue number as string
            context: Must contain 'issue' (GitHubIssue) and optionally 'expected_stage'
            
        Returns:
            ValidationResult
        """
        result = ValidationResult("github_issue", item_id)
        
        if not context or 'issue' not in context:
            result.add_check(
                name="issue_provided",
                passed=False,
                message="No issue data provided in context",
                severity="error"
            )
            return result
        
        issue = context['issue']
        expected_stage = context.get('expected_stage')
        
        # Check issue state
        is_open = issue.state == "open"
        severity = "error" if expected_stage != ProjectStage.DONE else "info"
        
        result.add_check(
            name="issue_state",
            passed=is_open or expected_stage == ProjectStage.DONE,
            message=f"Issue is {issue.state}",
            severity=severity
        )
        
        # Check title format
        has_valid_title = len(issue.title) > 10 and not issue.title.isspace()
        result.add_check(
            name="title_format",
            passed=has_valid_title,
            message="Title " + ("is valid" if has_valid_title else "is too short or empty"),
            severity="warning"
        )
        
        # Check body content
        has_body = bool(issue.body and len(issue.body.strip()) > 50)
        result.add_check(
            name="has_description",
            passed=has_body,
            message="Description " + ("present" if has_body else "missing or too short"),
            severity="warning"
        )
        
        # Check stage label
        if expected_stage:
            expected_labels = self.STAGE_LABELS.get(expected_stage, [])
            has_stage_label = any(issue.has_label(label) for label in expected_labels)
            
            result.add_check(
                name="stage_label",
                passed=has_stage_label,
                message=f"Stage label for {expected_stage.value} " + ("found" if has_stage_label else "missing"),
                severity="error"
            )
        
        # Check for project ID in title or body
        project_id_pattern = r'\b[a-zA-Z0-9_-]+-[a-zA-Z0-9]+\b'
        has_project_id = False
        
        if re.search(project_id_pattern, issue.title):
            has_project_id = True
        elif issue.body and re.search(project_id_pattern, issue.body):
            has_project_id = True
        
        result.add_check(
            name="has_project_id",
            passed=has_project_id,
            message="Project ID " + ("found" if has_project_id else "not found"),
            severity="info"
        )
        
        # Check assignees for active projects
        if expected_stage in [ProjectStage.IN_PROGRESS, ProjectStage.IN_REVIEW]:
            has_assignees = bool(issue.assignees)
            result.add_check(
                name="has_assignees",
                passed=has_assignees,
                message="Assignees " + ("present" if has_assignees else "missing for active project"),
                severity="warning"
            )
        
        return result


class GitHubLabelValidator(BaseValidator):
    """Validator for GitHub labels on a repository."""
    
    REQUIRED_LABELS = [
        "backlog",
        "ready", 
        "in-progress",
        "in-review",
        "done",
        "needs-review",
        "critical-review",
        "blocked"
    ]
    
    RECOMMENDED_LABELS = [
        "bug",
        "enhancement",
        "documentation",
        "help-wanted",
        "question",
        "wontfix"
    ]
    
    def validate(self, item_id: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate repository labels.
        
        Args:
            item_id: Repository name
            context: Must contain 'labels' (List[str])
            
        Returns:
            ValidationResult
        """
        result = ValidationResult("github_labels", item_id)
        
        if not context or 'labels' not in context:
            result.add_check(
                name="labels_provided",
                passed=False,
                message="No label data provided in context",
                severity="error"
            )
            return result
        
        labels = [label.lower() for label in context['labels']]
        
        # Check required labels
        for required in self.REQUIRED_LABELS:
            has_label = required.lower() in labels
            result.add_check(
                name=f"has_label_{required}",
                passed=has_label,
                message=f"Required label '{required}' " + ("exists" if has_label else "missing"),
                severity="error" if not has_label else "info"
            )
        
        # Check recommended labels
        for recommended in self.RECOMMENDED_LABELS:
            has_label = recommended.lower() in labels
            result.add_check(
                name=f"has_label_{recommended}",
                passed=has_label,
                message=f"Recommended label '{recommended}' " + ("exists" if has_label else "missing"),
                severity="info"
            )
        
        # Check for duplicate labels (case-insensitive)
        seen = set()
        duplicates = []
        for label in context['labels']:  # Use original case
            lower = label.lower()
            if lower in seen:
                duplicates.append(label)
            seen.add(lower)
        
        result.add_check(
            name="no_duplicate_labels",
            passed=len(duplicates) == 0,
            message=f"Duplicate labels: {duplicates}" if duplicates else "No duplicate labels",
            severity="warning"
        )
        
        return result


class ProjectBoardValidator(BaseValidator):
    """Validator for GitHub project board state."""
    
    EXPECTED_COLUMNS = [
        "Backlog",
        "Ready",
        "In Progress",
        "In Review",
        "Done"
    ]
    
    def validate(self, item_id: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate project board configuration and state.
        
        Args:
            item_id: Project board name/ID
            context: Must contain 'columns' and 'cards'
            
        Returns:
            ValidationResult
        """
        result = ValidationResult("project_board", item_id)
        
        if not context:
            result.add_check(
                name="context_provided",
                passed=False,
                message="No context provided",
                severity="error"
            )
            return result
        
        # Check columns
        columns = context.get('columns', [])
        cards = context.get('cards', [])
        
        # Validate column structure
        for expected in self.EXPECTED_COLUMNS:
            has_column = expected.lower() in [col.lower() for col in columns]
            result.add_check(
                name=f"has_column_{expected.lower().replace(' ', '_')}",
                passed=has_column,
                message=f"Column '{expected}' " + ("exists" if has_column else "missing"),
                severity="error" if not has_column else "info"
            )
        
        # Check card distribution
        column_counts = {col: 0 for col in columns}
        orphaned_cards = []
        
        for card in cards:
            if card.column in columns:
                column_counts[card.column] += 1
            else:
                orphaned_cards.append(card.id)
        
        result.add_check(
            name="no_orphaned_cards",
            passed=len(orphaned_cards) == 0,
            message=f"Orphaned cards: {orphaned_cards}" if orphaned_cards else "All cards in valid columns",
            severity="warning"
        )
        
        # Check for empty important columns
        for col in ["Ready", "In Progress", "In Review"]:
            if col in column_counts:
                is_empty = column_counts[col] == 0
                result.add_check(
                    name=f"column_{col.lower().replace(' ', '_')}_status",
                    passed=True,  # Not an error to be empty
                    message=f"Column '{col}' has {column_counts[col]} cards",
                    severity="info",
                    details={"count": column_counts[col], "empty": is_empty}
                )
        
        # Validate card-issue linkage
        if 'issues' in context:
            issues = context['issues']
            issue_numbers = {issue.number for issue in issues}
            
            unlinked_cards = []
            for card in cards:
                if card.issue_number and card.issue_number not in issue_numbers:
                    unlinked_cards.append(card.id)
            
            result.add_check(
                name="card_issue_linkage",
                passed=len(unlinked_cards) == 0,
                message=f"Cards linked to non-existent issues: {unlinked_cards}" if unlinked_cards else "All cards properly linked",
                severity="warning"
            )
        
        # Check column order
        if columns:
            expected_order = [col for col in self.EXPECTED_COLUMNS if col in columns]
            actual_order = [col for col in columns if col in self.EXPECTED_COLUMNS]
            
            correct_order = expected_order == actual_order
            result.add_check(
                name="column_order",
                passed=correct_order,
                message="Column order " + ("correct" if correct_order else f"incorrect: {actual_order}"),
                severity="info"
            )
        
        return result


class StageConsistencyValidator(BaseValidator):
    """Validator for consistency between issue labels, project board, and score."""
    
    def validate(self, item_id: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate stage consistency across GitHub elements.
        
        Args:
            item_id: Project ID
            context: Must contain 'issue', 'card_column', 'stage', 'score'
            
        Returns:
            ValidationResult
        """
        result = ValidationResult("stage_consistency", item_id)
        
        if not context:
            result.add_check(
                name="context_provided",
                passed=False,
                message="No context provided",
                severity="error"
            )
            return result
        
        issue = context.get('issue')
        card_column = context.get('card_column')
        stage = context.get('stage')
        score = context.get('score', 0)
        
        if not all([issue, stage]):
            result.add_check(
                name="required_data",
                passed=False,
                message="Missing required data (issue or stage)",
                severity="error"
            )
            return result
        
        # Map columns to stages
        column_stage_map = {
            "backlog": ProjectStage.BACKLOG,
            "ready": ProjectStage.READY,
            "in progress": ProjectStage.IN_PROGRESS,
            "in review": ProjectStage.IN_REVIEW,
            "done": ProjectStage.DONE
        }
        
        # Check label consistency
        stage_labels = GitHubIssueValidator.STAGE_LABELS.get(stage, [])
        has_correct_label = any(issue.has_label(label) for label in stage_labels)
        
        result.add_check(
            name="label_stage_match",
            passed=has_correct_label,
            message=f"Issue label matches stage {stage.value}: {has_correct_label}",
            severity="error" if not has_correct_label else "info"
        )
        
        # Check column consistency if provided
        if card_column:
            expected_stage = column_stage_map.get(card_column.lower())
            column_matches = expected_stage == stage
            
            result.add_check(
                name="column_stage_match",
                passed=column_matches,
                message=f"Project column '{card_column}' " + 
                       (f"matches stage {stage.value}" if column_matches else f"doesn't match stage {stage.value}"),
                severity="error" if not column_matches else "info"
            )
        
        # Check score consistency
        score_thresholds = {
            ProjectStage.BACKLOG: (0, 5),
            ProjectStage.READY: (0, 5),
            ProjectStage.IN_PROGRESS: (0, 1),  # Lower threshold for review
            ProjectStage.IN_REVIEW: (0, 5),
            ProjectStage.DONE: (0, float('inf'))  # No upper limit
        }
        
        min_score, max_score = score_thresholds.get(stage, (0, 5))
        score_valid = min_score <= score < max_score
        
        # Special case: transitioning stages
        if score >= max_score and stage != ProjectStage.DONE:
            result.add_check(
                name="ready_to_advance",
                passed=True,
                message=f"Score {score} indicates readiness to advance from {stage.value}",
                severity="info"
            )
        else:
            result.add_check(
                name="score_stage_consistency",
                passed=score_valid or score >= max_score,
                message=f"Score {score} is " + 
                       ("appropriate" if score_valid else f"unusual") + f" for stage {stage.value}",
                severity="warning" if not score_valid and score < max_score else "info"
            )
        
        # Check for blocked label with low score
        if issue.has_label("blocked") and score < 2:
            result.add_check(
                name="blocked_with_low_score",
                passed=False,
                message="Project is blocked but has low score - may need attention",
                severity="warning"
            )
        
        # Check done stage requirements
        if stage == ProjectStage.DONE:
            should_be_closed = issue.state == "closed"
            result.add_check(
                name="done_issue_closed",
                passed=should_be_closed,
                message="Done project issue " + ("is closed" if should_be_closed else "should be closed"),
                severity="warning" if not should_be_closed else "info"
            )
        
        return result


class MilestoneValidator(BaseValidator):
    """Validator for GitHub milestones."""
    
    def validate(self, item_id: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate milestone configuration.
        
        Args:
            item_id: Milestone title
            context: Must contain milestone data
            
        Returns:
            ValidationResult
        """
        result = ValidationResult("milestone", item_id)
        
        if not context or 'milestone' not in context:
            result.add_check(
                name="milestone_provided",
                passed=False,
                message="No milestone data provided",
                severity="error"
            )
            return result
        
        milestone = context['milestone']
        
        # Check basic properties
        has_description = bool(milestone.get('description'))
        result.add_check(
            name="has_description",
            passed=has_description,
            message="Milestone description " + ("present" if has_description else "missing"),
            severity="warning"
        )
        
        # Check due date
        has_due_date = bool(milestone.get('due_on'))
        result.add_check(
            name="has_due_date",
            passed=has_due_date,
            message="Due date " + ("set" if has_due_date else "not set"),
            severity="info"
        )
        
        # Check progress
        open_issues = milestone.get('open_issues', 0)
        closed_issues = milestone.get('closed_issues', 0)
        total_issues = open_issues + closed_issues
        
        if total_issues > 0:
            progress = (closed_issues / total_issues) * 100
            result.add_check(
                name="progress",
                passed=True,
                message=f"Progress: {progress:.1f}% ({closed_issues}/{total_issues} issues closed)",
                severity="info",
                details={"progress_percent": progress, "open": open_issues, "closed": closed_issues}
            )
        else:
            result.add_check(
                name="has_issues",
                passed=False,
                message="Milestone has no associated issues",
                severity="warning"
            )
        
        # Check if overdue
        if has_due_date and milestone.get('state') == 'open':
            due_date = datetime.fromisoformat(milestone['due_on'].replace('Z', '+00:00'))
            is_overdue = due_date < datetime.now(due_date.tzinfo)
            
            result.add_check(
                name="due_date_status",
                passed=not is_overdue,
                message="Milestone " + ("is overdue" if is_overdue else "is on track"),
                severity="warning" if is_overdue else "info"
            )
        
        return result