"""Score tracking system for llmXive projects."""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ReviewType(Enum):
    """Types of reviews and their score impacts."""
    LLM_POSITIVE = 0.5
    LLM_NEGATIVE = -0.5  # Note: Negative reviews don't actually subtract in llmXive
    HUMAN_POSITIVE = 1.0
    HUMAN_NEGATIVE = -1.0  # Note: Negative reviews don't actually subtract in llmXive
    CRITICAL = 0  # Moves back to previous stage with score reset


class Review:
    """Represents a single review."""
    
    def __init__(self, reviewer: str, is_positive: bool, 
                 is_human: bool = False, is_critical: bool = False,
                 comment: str = "", timestamp: Optional[datetime] = None):
        """Initialize a review.
        
        Args:
            reviewer: Name/ID of the reviewer
            is_positive: Whether this is a positive review
            is_human: Whether this is a human review (vs LLM)
            is_critical: Whether this is a critical review (resets score)
            comment: Review comment/content
            timestamp: When the review was made
        """
        self.reviewer = reviewer
        self.is_positive = is_positive
        self.is_human = is_human
        self.is_critical = is_critical
        self.comment = comment
        self.timestamp = timestamp or datetime.now(timezone.utc)
    
    def get_score_impact(self) -> float:
        """Get the score impact of this review."""
        if self.is_critical:
            return ReviewType.CRITICAL.value
        
        if self.is_positive:
            return ReviewType.HUMAN_POSITIVE.value if self.is_human else ReviewType.LLM_POSITIVE.value
        else:
            return ReviewType.HUMAN_NEGATIVE.value if self.is_human else ReviewType.LLM_NEGATIVE.value
    
    def __repr__(self) -> str:
        """String representation."""
        review_type = "CRITICAL" if self.is_critical else (
            "POSITIVE" if self.is_positive else "NEGATIVE"
        )
        reviewer_type = "HUMAN" if self.is_human else "LLM"
        return f"Review({self.reviewer}, {review_type}, {reviewer_type}, impact={self.get_score_impact()})"


class ScoreTracker:
    """Tracks and manages project scores."""
    
    ADVANCEMENT_THRESHOLD = 5.0
    SCORE_LABEL_PREFIX = "score:"
    
    def __init__(self, github_handler=None):
        """Initialize score tracker.
        
        Args:
            github_handler: Optional GitHub handler for label management
        """
        self.github = github_handler
        self.score_history = {}  # project_id -> list of score events
        self.current_scores = {}  # project_id -> current score
        self.reviews = {}  # project_id -> list of reviews
    
    def add_review(self, project_id: str, review: Review) -> float:
        """Add a review and update the project score.
        
        Args:
            project_id: Project identifier
            review: Review to add
            
        Returns:
            New score after applying review
        """
        # Initialize if needed
        if project_id not in self.reviews:
            self.reviews[project_id] = []
            self.current_scores[project_id] = 0.0
            self.score_history[project_id] = []
        
        # Get current score
        old_score = self.current_scores[project_id]
        
        # Add review
        self.reviews[project_id].append(review)
        
        # Calculate new score
        if review.is_critical:
            # Critical review should trigger moving back to previous stage
            # The stage manager will handle the actual move and score reset
            new_score = old_score  # Keep current score for now
            logger.warning(f"Critical review by {review.reviewer} for {project_id} - should move to previous stage")
        else:
            # Add/subtract review impact
            score_delta = review.get_score_impact()
            new_score = old_score + score_delta
            
            # Score cannot go below 0
            new_score = max(0.0, new_score)
        
        # Update current score
        self.current_scores[project_id] = new_score
        
        # Record in history
        self.score_history[project_id].append({
            'timestamp': review.timestamp,
            'old_score': old_score,
            'new_score': new_score,
            'review': review,
            'event': 'review_added'
        })
        
        logger.info(f"Score updated for {project_id}: {old_score} -> {new_score} "
                   f"(Review by {review.reviewer}: {review.get_score_impact()})")
        
        return new_score
    
    def get_current_score(self, project_id: str) -> float:
        """Get the current score for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Current score (0.0 if project not found)
        """
        return self.current_scores.get(project_id, 0.0)
    
    def should_advance(self, project_id: str) -> bool:
        """Check if a project should advance to the next stage.
        
        Args:
            project_id: Project identifier
            
        Returns:
            True if score >= advancement threshold
        """
        return self.get_current_score(project_id) >= self.ADVANCEMENT_THRESHOLD
    
    def reset_score(self, project_id: str, reason: str = "stage_transition") -> None:
        """Reset a project's score to 0.
        
        Args:
            project_id: Project identifier
            reason: Reason for reset
        """
        if project_id not in self.current_scores:
            self.current_scores[project_id] = 0.0
            self.score_history[project_id] = []
            return
        
        old_score = self.current_scores[project_id]
        self.current_scores[project_id] = 0.0
        
        self.score_history[project_id].append({
            'timestamp': datetime.now(timezone.utc),
            'old_score': old_score,
            'new_score': 0.0,
            'event': 'score_reset',
            'reason': reason
        })
        
        logger.info(f"Score reset for {project_id}: {old_score} -> 0.0 (reason: {reason})")
    
    def get_reviews(self, project_id: str) -> List[Review]:
        """Get all reviews for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            List of reviews (empty if project not found)
        """
        return self.reviews.get(project_id, [])
    
    def get_score_history(self, project_id: str) -> List[Dict]:
        """Get the score history for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            List of score events
        """
        return self.score_history.get(project_id, [])
    
    def calculate_score_from_reviews(self, reviews: List[Review]) -> float:
        """Calculate total score from a list of reviews.
        
        Args:
            reviews: List of reviews
            
        Returns:
            Calculated score
        """
        score = 0.0
        
        for review in reviews:
            if review.is_critical:
                # Critical review resets score
                score = 0.0
            else:
                # Add/subtract review impact
                score += review.get_score_impact()
                # Cannot go below 0
                score = max(0.0, score)
        
        return score
    
    def get_score_breakdown(self, project_id: str) -> Dict[str, any]:
        """Get detailed breakdown of score calculation.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Dictionary with score breakdown
        """
        reviews = self.get_reviews(project_id)
        
        breakdown = {
            'current_score': self.get_current_score(project_id),
            'total_reviews': len(reviews),
            'positive_reviews': sum(1 for r in reviews if r.is_positive and not r.is_critical),
            'negative_reviews': sum(1 for r in reviews if not r.is_positive and not r.is_critical),
            'critical_reviews': sum(1 for r in reviews if r.is_critical),
            'human_reviews': sum(1 for r in reviews if r.is_human),
            'llm_reviews': sum(1 for r in reviews if not r.is_human),
            'can_advance': self.should_advance(project_id),
            'points_to_advance': max(0, self.ADVANCEMENT_THRESHOLD - self.get_current_score(project_id))
        }
        
        return breakdown
    
    # GitHub integration methods
    
    def update_score_label(self, issue_number: int, project_id: str) -> None:
        """Update the score label on a GitHub issue.
        
        Args:
            issue_number: GitHub issue number
            project_id: Project identifier
        """
        if not self.github:
            logger.warning("No GitHub handler configured, skipping label update")
            return
        
        current_score = self.get_current_score(project_id)
        
        try:
            # Get current labels
            issue = self.github.get_issue(issue_number)
            current_labels = [label['name'] for label in issue.get('labels', [])]
            
            # Remove old score labels
            labels_to_remove = [l for l in current_labels if l.startswith(self.SCORE_LABEL_PREFIX)]
            for label in labels_to_remove:
                self.github.remove_label(issue_number, label)
            
            # Add new score label
            score_label = f"{self.SCORE_LABEL_PREFIX} {current_score}"
            self.github.add_label(issue_number, score_label)
            
            # Add advancement label if applicable
            if self.should_advance(project_id):
                self.github.add_label(issue_number, "ready-to-advance")
            else:
                # Remove advancement label if it exists
                if "ready-to-advance" in current_labels:
                    self.github.remove_label(issue_number, "ready-to-advance")
            
            logger.info(f"Updated score label for issue #{issue_number}: {score_label}")
            
        except Exception as e:
            logger.error(f"Failed to update score label: {e}")
    
    def get_score_from_labels(self, labels: List[str]) -> Optional[float]:
        """Extract score from issue labels.
        
        Args:
            labels: List of label names
            
        Returns:
            Score if found, None otherwise
        """
        for label in labels:
            if label.startswith(self.SCORE_LABEL_PREFIX):
                try:
                    score_str = label.replace(self.SCORE_LABEL_PREFIX, "").strip()
                    return float(score_str)
                except ValueError:
                    logger.warning(f"Invalid score label format: {label}")
        
        return None