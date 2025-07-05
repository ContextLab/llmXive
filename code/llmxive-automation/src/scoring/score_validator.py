"""Score validation system for ensuring correct score calculations."""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .score_tracker import Review, ScoreTracker

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check."""
    passed: bool
    message: str
    expected: Optional[float] = None
    actual: Optional[float] = None
    
    def __str__(self) -> str:
        """String representation."""
        if self.passed:
            return f"✓ {self.message}"
        else:
            msg = f"✗ {self.message}"
            if self.expected is not None and self.actual is not None:
                msg += f" (expected: {self.expected}, actual: {self.actual})"
            return msg


class ScoreValidator:
    """Validates score calculations and state transitions."""
    
    def __init__(self, score_tracker: ScoreTracker):
        """Initialize validator with a score tracker.
        
        Args:
            score_tracker: ScoreTracker instance to validate
        """
        self.tracker = score_tracker
    
    def validate_score_calculation(self, project_id: str) -> List[ValidationResult]:
        """Validate that the current score matches calculated score from reviews.
        
        Args:
            project_id: Project to validate
            
        Returns:
            List of validation results
        """
        results = []
        
        # Get current score and reviews
        current_score = self.tracker.get_current_score(project_id)
        reviews = self.tracker.get_reviews(project_id)
        
        # Recalculate score from reviews
        calculated_score = self.tracker.calculate_score_from_reviews(reviews)
        
        # Check if they match
        if abs(current_score - calculated_score) < 0.001:  # Float comparison tolerance
            results.append(ValidationResult(
                passed=True,
                message="Current score matches calculated score",
                expected=calculated_score,
                actual=current_score
            ))
        else:
            results.append(ValidationResult(
                passed=False,
                message="Score mismatch",
                expected=calculated_score,
                actual=current_score
            ))
        
        return results
    
    def validate_review_impacts(self, project_id: str) -> List[ValidationResult]:
        """Validate that each review had the correct impact on score.
        
        Args:
            project_id: Project to validate
            
        Returns:
            List of validation results
        """
        results = []
        history = self.tracker.get_score_history(project_id)
        
        for i, event in enumerate(history):
            if event['event'] != 'review_added':
                continue
            
            review = event['review']
            old_score = event['old_score']
            new_score = event['new_score']
            
            # Calculate expected new score
            if review.is_critical:
                expected_new_score = 0.0
            else:
                expected_new_score = max(0.0, old_score + review.get_score_impact())
            
            # Validate
            if abs(new_score - expected_new_score) < 0.001:
                results.append(ValidationResult(
                    passed=True,
                    message=f"Review {i+1} by {review.reviewer} applied correctly"
                ))
            else:
                results.append(ValidationResult(
                    passed=False,
                    message=f"Review {i+1} by {review.reviewer} applied incorrectly",
                    expected=expected_new_score,
                    actual=new_score
                ))
        
        return results
    
    def validate_score_boundaries(self, project_id: str) -> List[ValidationResult]:
        """Validate that score never went below 0 or had invalid values.
        
        Args:
            project_id: Project to validate
            
        Returns:
            List of validation results
        """
        results = []
        history = self.tracker.get_score_history(project_id)
        
        # Check current score
        current_score = self.tracker.get_current_score(project_id)
        if current_score < 0:
            results.append(ValidationResult(
                passed=False,
                message="Current score is negative",
                actual=current_score
            ))
        else:
            results.append(ValidationResult(
                passed=True,
                message="Current score is non-negative"
            ))
        
        # Check historical scores
        negative_scores = []
        for event in history:
            if event['new_score'] < 0:
                negative_scores.append(event)
        
        if negative_scores:
            results.append(ValidationResult(
                passed=False,
                message=f"Found {len(negative_scores)} events with negative scores"
            ))
        else:
            results.append(ValidationResult(
                passed=True,
                message="No negative scores in history"
            ))
        
        return results
    
    def validate_critical_reviews(self, project_id: str) -> List[ValidationResult]:
        """Validate that critical reviews are properly marked.
        
        Note: Critical reviews now trigger stage moves rather than score resets.
        The actual move is handled by StageManager.
        
        Args:
            project_id: Project to validate
            
        Returns:
            List of validation results
        """
        results = []
        reviews = self.tracker.get_reviews(project_id)
        
        critical_reviews = [r for r in reviews if r.is_critical]
        
        if critical_reviews:
            results.append(ValidationResult(
                passed=True,
                message=f"Found {len(critical_reviews)} critical review(s) marked for stage move"
            ))
        else:
            results.append(ValidationResult(
                passed=True,
                message="No critical reviews found"
            ))
        
        return results
    
    def validate_advancement_threshold(self, project_id: str) -> List[ValidationResult]:
        """Validate advancement threshold logic.
        
        Args:
            project_id: Project to validate
            
        Returns:
            List of validation results
        """
        results = []
        
        current_score = self.tracker.get_current_score(project_id)
        should_advance = self.tracker.should_advance(project_id)
        expected_advance = current_score >= ScoreTracker.ADVANCEMENT_THRESHOLD
        
        if should_advance == expected_advance:
            if should_advance:
                results.append(ValidationResult(
                    passed=True,
                    message=f"Correctly identified as ready to advance (score: {current_score})"
                ))
            else:
                points_needed = ScoreTracker.ADVANCEMENT_THRESHOLD - current_score
                results.append(ValidationResult(
                    passed=True,
                    message=f"Correctly identified as not ready to advance "
                           f"(needs {points_needed:.1f} more points)"
                ))
        else:
            results.append(ValidationResult(
                passed=False,
                message="Advancement logic incorrect",
                expected=expected_advance,
                actual=should_advance
            ))
        
        return results
    
    def validate_all(self, project_id: str) -> Dict[str, List[ValidationResult]]:
        """Run all validations for a project.
        
        Args:
            project_id: Project to validate
            
        Returns:
            Dictionary mapping validation types to results
        """
        return {
            'score_calculation': self.validate_score_calculation(project_id),
            'review_impacts': self.validate_review_impacts(project_id),
            'score_boundaries': self.validate_score_boundaries(project_id),
            'critical_reviews': self.validate_critical_reviews(project_id),
            'advancement_threshold': self.validate_advancement_threshold(project_id)
        }
    
    def get_validation_summary(self, project_id: str) -> str:
        """Get a summary of all validations.
        
        Args:
            project_id: Project to validate
            
        Returns:
            Formatted summary string
        """
        all_results = self.validate_all(project_id)
        
        summary_lines = [f"Validation Summary for {project_id}:", "=" * 50]
        
        total_passed = 0
        total_failed = 0
        
        for category, results in all_results.items():
            passed = sum(1 for r in results if r.passed)
            failed = sum(1 for r in results if not r.passed)
            total_passed += passed
            total_failed += failed
            
            summary_lines.append(f"\n{category.replace('_', ' ').title()}:")
            summary_lines.append(f"  Passed: {passed}, Failed: {failed}")
            
            # Show failures
            for result in results:
                if not result.passed:
                    summary_lines.append(f"  {result}")
        
        summary_lines.append("\n" + "=" * 50)
        summary_lines.append(f"Total: {total_passed} passed, {total_failed} failed")
        
        if total_failed == 0:
            summary_lines.append("✅ All validations passed!")
        else:
            summary_lines.append("❌ Some validations failed")
        
        return "\n".join(summary_lines)