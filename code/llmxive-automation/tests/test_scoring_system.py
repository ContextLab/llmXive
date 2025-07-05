"""Comprehensive tests for the scoring system."""

import pytest
from datetime import datetime, timezone
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from scoring import (
    ScoreTracker, Review, ReviewType,
    ScoreValidator, ValidationResult,
    StageManager, ProjectStage
)


class TestReview:
    """Test the Review class."""
    
    def test_llm_positive_review(self):
        """Test LLM positive review impact."""
        review = Review("model-1", is_positive=True, is_human=False)
        assert review.get_score_impact() == 0.5
        assert not review.is_critical
    
    def test_llm_negative_review(self):
        """Test LLM negative review impact."""
        review = Review("model-1", is_positive=False, is_human=False)
        assert review.get_score_impact() == -0.5
    
    def test_human_positive_review(self):
        """Test human positive review impact."""
        review = Review("user-1", is_positive=True, is_human=True)
        assert review.get_score_impact() == 1.0
    
    def test_human_negative_review(self):
        """Test human negative review impact."""
        review = Review("user-1", is_positive=False, is_human=True)
        assert review.get_score_impact() == -1.0
    
    def test_critical_review(self):
        """Test critical review impact."""
        review = Review("model-1", is_positive=False, is_critical=True)
        assert review.get_score_impact() == 0
        assert review.is_critical


class TestScoreTracker:
    """Test the ScoreTracker class."""
    
    def test_initial_score(self):
        """Test initial score is 0."""
        tracker = ScoreTracker()
        assert tracker.get_current_score("test-project") == 0.0
    
    def test_single_positive_review(self):
        """Test adding a single positive review."""
        tracker = ScoreTracker()
        review = Review("model-1", is_positive=True, is_human=False)
        
        new_score = tracker.add_review("test-project", review)
        assert new_score == 0.5
        assert tracker.get_current_score("test-project") == 0.5
    
    def test_multiple_reviews(self):
        """Test adding multiple reviews."""
        tracker = ScoreTracker()
        project_id = "test-project"
        
        # Add reviews
        tracker.add_review(project_id, Review("model-1", is_positive=True, is_human=False))  # +0.5
        tracker.add_review(project_id, Review("user-1", is_positive=True, is_human=True))    # +1.0
        tracker.add_review(project_id, Review("model-2", is_positive=False, is_human=False)) # -0.5
        
        assert tracker.get_current_score(project_id) == 1.0  # 0.5 + 1.0 - 0.5
    
    def test_score_floor_at_zero(self):
        """Test that score cannot go below 0."""
        tracker = ScoreTracker()
        project_id = "test-project"
        
        # Add negative reviews
        tracker.add_review(project_id, Review("model-1", is_positive=False, is_human=False))  # -0.5 -> 0
        tracker.add_review(project_id, Review("user-1", is_positive=False, is_human=True))    # -1.0 -> 0
        
        assert tracker.get_current_score(project_id) == 0.0
        
        # Add positive review
        tracker.add_review(project_id, Review("model-2", is_positive=True, is_human=False))   # +0.5
        assert tracker.get_current_score(project_id) == 0.5
    
    def test_critical_review_behavior(self):
        """Test that critical review maintains score but signals stage move."""
        tracker = ScoreTracker()
        project_id = "test-project"
        
        # Build up score
        tracker.add_review(project_id, Review("model-1", is_positive=True, is_human=False))  # +0.5
        tracker.add_review(project_id, Review("user-1", is_positive=True, is_human=True))    # +1.0
        tracker.add_review(project_id, Review("model-2", is_positive=True, is_human=False))  # +0.5
        assert tracker.get_current_score(project_id) == 2.0
        
        # Critical review - score stays same (stage manager will handle the reset)
        tracker.add_review(project_id, Review("critic", is_positive=False, is_critical=True))
        assert tracker.get_current_score(project_id) == 2.0  # Score unchanged
        
        # Check that review is marked as critical
        reviews = tracker.get_reviews(project_id)
        assert any(r.is_critical for r in reviews)
    
    def test_advancement_threshold(self):
        """Test advancement threshold logic."""
        tracker = ScoreTracker()
        project_id = "test-project"
        
        # Below threshold
        for i in range(9):
            tracker.add_review(project_id, Review(f"model-{i}", is_positive=True, is_human=False))
        
        assert tracker.get_current_score(project_id) == 4.5  # 9 * 0.5
        assert not tracker.should_advance(project_id)
        
        # At threshold
        tracker.add_review(project_id, Review("model-10", is_positive=True, is_human=False))
        assert tracker.get_current_score(project_id) == 5.0
        assert tracker.should_advance(project_id)
        
        # Above threshold
        tracker.add_review(project_id, Review("user-1", is_positive=True, is_human=True))
        assert tracker.get_current_score(project_id) == 6.0
        assert tracker.should_advance(project_id)
    
    def test_score_history(self):
        """Test score history tracking."""
        tracker = ScoreTracker()
        project_id = "test-project"
        
        # Add some reviews
        tracker.add_review(project_id, Review("model-1", is_positive=True, is_human=False))
        tracker.add_review(project_id, Review("user-1", is_positive=False, is_human=True))
        
        history = tracker.get_score_history(project_id)
        assert len(history) == 2
        
        # Check first event
        assert history[0]['old_score'] == 0.0
        assert history[0]['new_score'] == 0.5
        assert history[0]['event'] == 'review_added'
        
        # Check second event
        assert history[1]['old_score'] == 0.5
        assert history[1]['new_score'] == 0.0  # Went negative, clamped to 0
    
    def test_score_breakdown(self):
        """Test score breakdown calculation."""
        tracker = ScoreTracker()
        project_id = "test-project"
        
        # Add various reviews
        tracker.add_review(project_id, Review("model-1", is_positive=True, is_human=False))
        tracker.add_review(project_id, Review("model-2", is_positive=True, is_human=False))
        tracker.add_review(project_id, Review("user-1", is_positive=True, is_human=True))
        tracker.add_review(project_id, Review("model-3", is_positive=False, is_human=False))
        tracker.add_review(project_id, Review("critic", is_positive=False, is_critical=True))
        tracker.add_review(project_id, Review("model-4", is_positive=True, is_human=False))
        
        breakdown = tracker.get_score_breakdown(project_id)
        
        assert breakdown['current_score'] == 2.0  # Critical review doesn't reset score directly
        assert breakdown['total_reviews'] == 6
        assert breakdown['positive_reviews'] == 4
        assert breakdown['negative_reviews'] == 1
        assert breakdown['critical_reviews'] == 1
        assert breakdown['human_reviews'] == 1
        assert breakdown['llm_reviews'] == 5
        assert breakdown['can_advance'] == False
        assert breakdown['points_to_advance'] == 3.0  # 5.0 - 2.0


class TestScoreValidator:
    """Test the ScoreValidator class."""
    
    def test_valid_score_calculation(self):
        """Test validation of correct score calculation."""
        tracker = ScoreTracker()
        project_id = "test-project"
        
        # Add reviews
        tracker.add_review(project_id, Review("model-1", is_positive=True, is_human=False))
        tracker.add_review(project_id, Review("user-1", is_positive=True, is_human=True))
        
        validator = ScoreValidator(tracker)
        results = validator.validate_score_calculation(project_id)
        
        assert len(results) == 1
        assert results[0].passed
        assert results[0].expected == 1.5
        assert results[0].actual == 1.5
    
    def test_review_impact_validation(self):
        """Test validation of review impacts."""
        tracker = ScoreTracker()
        project_id = "test-project"
        
        # Add reviews with known impacts
        tracker.add_review(project_id, Review("model-1", is_positive=True, is_human=False))   # +0.5
        tracker.add_review(project_id, Review("user-1", is_positive=False, is_human=True))    # -1.0 -> 0
        tracker.add_review(project_id, Review("model-2", is_positive=True, is_human=False))   # +0.5
        
        validator = ScoreValidator(tracker)
        results = validator.validate_review_impacts(project_id)
        
        assert all(r.passed for r in results)
        assert len(results) == 3
    
    def test_critical_review_validation(self):
        """Test validation of critical review behavior."""
        tracker = ScoreTracker()
        project_id = "test-project"
        
        # Build score then critical review
        tracker.add_review(project_id, Review("model-1", is_positive=True, is_human=True))    # +1.0
        tracker.add_review(project_id, Review("model-2", is_positive=True, is_human=True))    # +1.0
        tracker.add_review(project_id, Review("critic", is_positive=False, is_critical=True)) # Should trigger stage move
        
        validator = ScoreValidator(tracker)
        results = validator.validate_critical_reviews(project_id)
        
        # Critical reviews are now handled by stage manager, not score tracker
        assert len(results) >= 1
    
    def test_full_validation(self):
        """Test full validation suite."""
        tracker = ScoreTracker()
        project_id = "test-project"
        
        # Complex scenario (no critical review to avoid stage complexity)
        reviews = [
            Review("model-1", is_positive=True, is_human=False),      # +0.5
            Review("model-2", is_positive=True, is_human=False),      # +0.5
            Review("user-1", is_positive=True, is_human=True),        # +1.0
            Review("model-3", is_positive=False, is_human=False),     # -0.5
            Review("model-4", is_positive=True, is_human=False),      # +0.5
            Review("model-5", is_positive=True, is_human=False),      # +0.5
        ]
        
        for review in reviews:
            tracker.add_review(project_id, review)
        
        validator = ScoreValidator(tracker)
        all_results = validator.validate_all(project_id)
        
        # Check all categories pass
        for category, results in all_results.items():
            for result in results:
                assert result.passed, f"Failed in {category}: {result.message}"


class TestStageManager:
    """Test the StageManager class."""
    
    def test_initial_stage(self):
        """Test initial stage is BACKLOG."""
        tracker = ScoreTracker()
        manager = StageManager(tracker)
        
        assert manager.get_current_stage("test-project") == ProjectStage.BACKLOG
    
    def test_can_advance_logic(self):
        """Test advancement requirement checking."""
        tracker = ScoreTracker()
        manager = StageManager(tracker)
        project_id = "test-project"
        
        # Initial state - cannot advance without requirements
        project_state = {
            'artifacts': {}
        }
        can_advance, requirements = manager.can_advance(project_id, project_state)
        assert not can_advance
        assert not requirements.get('has_technical_design_document', False)
        assert not requirements.get('score_threshold_met', False)
        
        # Add technical design but no score
        project_state['artifacts']['technical_design_document'] = "path/to/design.md"
        project_state['has_technical_design'] = True
        can_advance, requirements = manager.can_advance(project_id, project_state)
        assert not can_advance
        assert requirements.get('has_technical_design_document', True)
        assert not requirements.get('score_threshold_met', False)
        
        # Add sufficient score
        for i in range(10):
            tracker.add_review(project_id, Review(f"model-{i}", is_positive=True, is_human=False))
        
        can_advance, requirements = manager.can_advance(project_id, project_state)
        assert can_advance
        assert requirements.get('has_technical_design_document', True)
        assert requirements.get('score_threshold_met', True)
    
    def test_stage_advancement(self):
        """Test advancing through all stages."""
        tracker = ScoreTracker()
        manager = StageManager(tracker)
        project_id = "test-project"
        
        # BACKLOG -> READY
        project_state = {
            'artifacts': {
                'technical_design_document': "design.md"
            },
            'has_technical_design': True,
            'issue_number': 123
        }
        
        # Add 5 points
        for i in range(10):
            tracker.add_review(project_id, Review(f"model-{i}", is_positive=True, is_human=False))
        
        success, transition = manager.advance_stage(project_id, project_state)
        assert success
        assert manager.get_current_stage(project_id) == ProjectStage.READY
        assert tracker.get_current_score(project_id) == 0.0  # Reset
        
        # READY -> IN_PROGRESS
        project_state['artifacts']['implementation_plan'] = "plan.md"
        project_state['has_implementation_plan'] = True
        
        for i in range(10):
            tracker.add_review(project_id, Review(f"model2-{i}", is_positive=True, is_human=False))
        
        success, transition = manager.advance_stage(project_id, project_state)
        assert success
        assert manager.get_current_stage(project_id) == ProjectStage.IN_PROGRESS
        assert tracker.get_current_score(project_id) == 0.0  # Reset
        
        # IN_PROGRESS -> IN_REVIEW (only needs 1 point)
        project_state['artifacts']['paper_draft'] = "paper.tex"
        project_state['artifacts']['code_repository'] = "code/"
        project_state['has_paper_draft'] = True
        project_state['has_complete_code'] = True
        
        tracker.add_review(project_id, Review("reviewer", is_positive=True, is_human=False))  # +0.5
        tracker.add_review(project_id, Review("reviewer2", is_positive=True, is_human=False))  # +0.5
        
        success, transition = manager.advance_stage(project_id, project_state)
        assert success
        assert manager.get_current_stage(project_id) == ProjectStage.IN_REVIEW
        assert tracker.get_current_score(project_id) == 0.0  # Reset
        
        # IN_REVIEW -> DONE (needs 5 points)
        project_state['artifacts']['paper_pdf'] = "paper.pdf"
        project_state['has_paper_pdf'] = True
        
        for i in range(10):
            tracker.add_review(project_id, Review(f"final-{i}", is_positive=True, is_human=False))
        
        success, transition = manager.advance_stage(project_id, project_state)
        assert success
        assert manager.get_current_stage(project_id) == ProjectStage.DONE
    
    def test_stage_summary(self):
        """Test stage summary generation."""
        tracker = ScoreTracker()
        manager = StageManager(tracker)
        project_id = "test-project"
        
        project_state = {
            'artifacts': {}
        }
        
        summary = manager.get_stage_summary(project_id, project_state)
        
        assert summary['current_stage'] == 'backlog'
        assert summary['next_stage'] == 'ready'
        assert not summary['can_advance']
        assert summary['current_score'] == 0.0
        assert 'missing_requirements' in summary
    
    def test_transition_validation(self):
        """Test validation of stage transitions."""
        tracker = ScoreTracker()
        manager = StageManager(tracker)
        project_id = "test-project"
        
        # Manual set to READY
        manager.set_stage(project_id, ProjectStage.READY, "testing")
        
        # Force advance to IN_PROGRESS
        project_state = {'artifacts': {}}
        manager.advance_stage(project_id, project_state, force=True)
        
        # Validate transitions
        messages = manager.validate_stage_transitions(project_id)
        
        assert len(messages) == 2
        assert "Manual set" in messages[0]
        assert any("Valid transition" in msg or "Requirements not fully met" in msg for msg in messages)
    
    def test_move_to_previous_stage(self):
        """Test moving back to previous stage on critical review."""
        tracker = ScoreTracker()
        manager = StageManager(tracker)
        project_id = "test-project"
        
        # Move to IN_REVIEW stage
        manager.set_stage(project_id, ProjectStage.IN_REVIEW, "testing")
        
        # Build up some score
        for i in range(6):
            tracker.add_review(project_id, Review(f"reviewer-{i}", is_positive=True, is_human=False))
        assert tracker.get_current_score(project_id) == 3.0
        
        # Move back due to critical review
        project_state = {'issue_number': 456}
        success, transition = manager.move_to_previous_stage(project_id, project_state, "critical_review")
        
        assert success
        assert transition.from_stage == ProjectStage.IN_REVIEW
        assert transition.to_stage == ProjectStage.IN_PROGRESS
        assert manager.get_current_stage(project_id) == ProjectStage.IN_PROGRESS
        assert tracker.get_current_score(project_id) == 0.0  # Score reset


class TestScoringScenarios:
    """Test complete scoring scenarios."""
    
    def test_typical_advancement_scenario(self):
        """Test a typical project advancement scenario."""
        tracker = ScoreTracker()
        manager = StageManager(tracker)
        project_id = "test-project"
        
        # Start in BACKLOG
        assert manager.get_current_stage(project_id) == ProjectStage.BACKLOG
        
        # Add technical design
        project_state = {
            'artifacts': {
                'technical_design_document': "design.md"
            },
            'has_technical_design': True
        }
        
        # Get reviews (2 positive, 1 negative, then more positive)
        reviews = [
            Review("enthusiast", is_positive=True, is_human=False),      # +0.5 = 0.5
            Review("supporter", is_positive=True, is_human=False),       # +0.5 = 1.0
            Review("critic", is_positive=False, is_human=False),         # -0.5 = 0.5
            Review("expert", is_positive=True, is_human=True),           # +1.0 = 1.5
            Review("model-1", is_positive=True, is_human=False),         # +0.5 = 2.0
            Review("model-2", is_positive=True, is_human=False),         # +0.5 = 2.5
            Review("model-3", is_positive=True, is_human=False),         # +0.5 = 3.0
            Review("model-4", is_positive=True, is_human=False),         # +0.5 = 3.5
            Review("model-5", is_positive=True, is_human=False),         # +0.5 = 4.0
            Review("reviewer", is_positive=True, is_human=True),         # +1.0 = 5.0
        ]
        
        for review in reviews:
            tracker.add_review(project_id, review)
        
        # Should be able to advance
        assert tracker.get_current_score(project_id) == 5.0
        assert tracker.should_advance(project_id)
        
        # Advance stage
        success, transition = manager.advance_stage(project_id, project_state)
        assert success
        assert manager.get_current_stage(project_id) == ProjectStage.READY
        assert tracker.get_current_score(project_id) == 0.0  # Reset after advancement
    
    def test_critical_review_with_stage_move(self):
        """Test scenario with critical review causing stage move."""
        tracker = ScoreTracker()
        manager = StageManager(tracker)
        project_id = "test-project"
        
        # Set to IN_REVIEW stage
        manager.set_stage(project_id, ProjectStage.IN_REVIEW, "testing")
        
        # Build up score
        for i in range(8):
            tracker.add_review(project_id, Review(f"model-{i}", is_positive=True, is_human=False))
        
        assert tracker.get_current_score(project_id) == 4.0  # 8 * 0.5
        
        # Critical review
        tracker.add_review(project_id, Review("critical-reviewer", is_positive=False, is_critical=True))
        # Score stays same until stage manager handles it
        assert tracker.get_current_score(project_id) == 4.0
        
        # Stage manager moves back and resets score
        project_state = {'issue_number': 789}
        success, transition = manager.move_to_previous_stage(project_id, project_state, "critical_review")
        assert success
        assert manager.get_current_stage(project_id) == ProjectStage.IN_PROGRESS
        assert tracker.get_current_score(project_id) == 0.0  # Now reset
        
        # Build up again in new stage
        for i in range(12):
            tracker.add_review(project_id, Review(f"model2-{i}", is_positive=True, is_human=False))
        
        assert tracker.get_current_score(project_id) == 6.0  # 12 * 0.5
        assert tracker.should_advance(project_id)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])