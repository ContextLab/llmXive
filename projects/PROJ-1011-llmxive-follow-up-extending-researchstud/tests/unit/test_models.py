"""
Unit tests for data models.

Tests the Abstract, PatternCard, Proposal, and Rating models
to ensure proper validation and serialization.
"""

import pytest
from datetime import datetime
from code.models import Abstract, PatternCard, Proposal, Rating


class TestAbstract:
    def test_create_valid_abstract(self):
        """Test creating a valid abstract."""
        abstract = Abstract(
            id="test-123",
            title="Test Paper",
            text="This is a test abstract.",
            domain="ML",
            acceptance_status="accepted"
        )
        assert abstract.id == "test-123"
        assert abstract.title == "Test Paper"
        assert abstract.domain == "ML"
    
    def test_empty_text_raises_error(self):
        """Test that empty text raises ValueError."""
        with pytest.raises(ValueError, match="Abstract text cannot be empty"):
            Abstract(
                id="test-456",
                title="Test",
                text=""
            )
    
    def test_empty_title_raises_error(self):
        """Test that empty title raises ValueError."""
        with pytest.raises(ValueError, match="Title cannot be empty"):
            Abstract(
                id="test-789",
                title="",
                text="Some text"
            )
    
    def test_serialization_roundtrip(self):
        """Test that to_dict and from_dict work correctly."""
        original = Abstract(
            id="test-roundtrip",
            title="Serialization Test",
            text="Testing serialization.",
            domain="Health",
            acceptance_status="rejected",
            year=2024
        )
        data = original.to_dict()
        restored = Abstract.from_dict(data)
        
        assert restored.id == original.id
        assert restored.title == original.title
        assert restored.text == original.text
        assert restored.domain == original.domain
        assert restored.year == original.year


class TestPatternCard:
    def test_create_valid_pattern(self):
        """Test creating a valid pattern card."""
        pattern = PatternCard(
            id="pattern-001",
            name="Attention Mechanism",
            description="Using attention to focus on relevant parts.",
            problem_statement="How to handle long sequences?",
            solution_approach="Self-attention layers",
            domain_origin="ML",
            confidence_score=0.85
        )
        assert pattern.id == "pattern-001"
        assert pattern.confidence_score == 0.85
    
    def test_invalid_confidence_score(self):
        """Test that confidence_score outside [0, 1] raises error."""
        with pytest.raises(ValueError, match="confidence_score must be between 0.0 and 1.0"):
            PatternCard(
                id="pattern-bad",
                name="Bad",
                description="Desc",
                problem_statement="Prob",
                solution_approach="Sol",
                domain_origin="ML",
                confidence_score=1.5
            )
    
    def test_empty_required_field(self):
        """Test that empty required fields raise error."""
        with pytest.raises(ValueError):
            PatternCard(
                id="pattern-empty",
                name="",
                description="Desc",
                problem_statement="Prob",
                solution_approach="Sol",
                domain_origin="ML"
            )
    
    def test_serialization_roundtrip(self):
        """Test serialization roundtrip."""
        original = PatternCard(
            id="pattern-serial",
            name="Serial Test",
            description="Testing.",
            problem_statement="Problem?",
            solution_approach="Solution.",
            domain_origin="Climate",
            keywords=["test", "serial"],
            confidence_score=0.9
        )
        data = original.to_dict()
        restored = PatternCard.from_dict(data)
        
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.keywords == original.keywords


class TestProposal:
    def test_create_baseline_proposal(self):
        """Test creating a baseline proposal."""
        proposal = Proposal(
            id="prop-base-001",
            title="Baseline Proposal",
            text="This is a baseline proposal.",
            problem_statement="What is the problem?",
            proposal_type="baseline"
        )
        assert proposal.proposal_type == "baseline"
        assert len(proposal.pattern_ids) == 0
    
    def test_create_pattern_guided_proposal(self):
        """Test creating a pattern-guided proposal."""
        proposal = Proposal(
            id="prop-pattern-001",
            title="Pattern Guided",
            text="Guided by patterns.",
            problem_statement="Problem statement",
            proposal_type="pattern_guided",
            pattern_ids=["pattern-001", "pattern-002"]
        )
        assert proposal.proposal_type == "pattern_guided"
        assert len(proposal.pattern_ids) == 2
    
    def test_invalid_proposal_type(self):
        """Test that invalid proposal_type raises error."""
        with pytest.raises(ValueError, match="proposal_type must be"):
            Proposal(
                id="prop-bad",
                title="Bad",
                text="Text",
                problem_statement="Prob",
                proposal_type="invalid_type"
            )
    
    def test_pattern_guided_without_patterns(self):
        """Test that pattern_guided without patterns raises error."""
        with pytest.raises(ValueError, match="pattern_guided proposals must have"):
            Proposal(
                id="prop-no-patterns",
                title="No Patterns",
                text="Text",
                problem_statement="Prob",
                proposal_type="pattern_guided"
            )
    
    def test_serialization_roundtrip(self):
        """Test serialization roundtrip."""
        original = Proposal(
            id="prop-serial",
            title="Serial Test",
            text="Testing serialization.",
            problem_statement="Problem?",
            proposal_type="pattern_guided",
            pattern_ids=["p1"],
            generation_model="test-model",
            generation_params={"temp": 0.7}
        )
        data = original.to_dict()
        restored = Proposal.from_dict(data)
        
        assert restored.id == original.id
        assert restored.proposal_type == original.proposal_type
        assert restored.generation_params == original.generation_params


class TestRating:
    def test_create_valid_rating(self):
        """Test creating a valid rating."""
        rating = Rating(
            id="rating-001",
            proposal_id="prop-001",
            expert_orcid="0000-0000-0000-0001",
            feasibility_score=4,
            bottleneck_score=3,
            alignment_score=5
        )
        assert rating.feasibility_score == 4
        assert rating.get_mean_score() == 4.0
    
    def test_invalid_score_range(self):
        """Test that scores outside 1-5 raise error."""
        with pytest.raises(ValueError, match="must be an integer between 1 and 5"):
            Rating(
                id="rating-bad",
                proposal_id="prop-001",
                expert_orcid="0000-0000-0000-0001",
                feasibility_score=6,
                bottleneck_score=3,
                alignment_score=5
            )
    
    def test_zero_score_raises_error(self):
        """Test that score of 0 raises error."""
        with pytest.raises(ValueError, match="must be an integer between 1 and 5"):
            Rating(
                id="rating-zero",
                proposal_id="prop-001",
                expert_orcid="0000-0000-0000-0001",
                feasibility_score=0,
                bottleneck_score=3,
                alignment_score=5
            )
    
    def test_missing_proposal_id(self):
        """Test that missing proposal_id raises error."""
        with pytest.raises(ValueError, match="proposal_id cannot be empty"):
            Rating(
                id="rating-no-proposal",
                proposal_id="",
                expert_orcid="0000-0000-0000-0001",
                feasibility_score=3,
                bottleneck_score=3,
                alignment_score=3
            )
    
    def test_serialization_roundtrip(self):
        """Test serialization roundtrip."""
        original = Rating(
            id="rating-serial",
            proposal_id="prop-serial",
            expert_orcid="0000-0000-0000-0002",
            feasibility_score=5,
            bottleneck_score=4,
            alignment_score=5,
            comments="Good proposal."
        )
        data = original.to_dict()
        restored = Rating.from_dict(data)
        
        assert restored.id == original.id
        assert restored.expert_orcid == original.expert_orcid
        assert restored.comments == original.comments
        assert restored.get_mean_score() == original.get_mean_score()