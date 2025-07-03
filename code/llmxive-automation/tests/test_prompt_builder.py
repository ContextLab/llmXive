"""Unit tests for prompt engineering system"""

import pytest
from llmxive_automation.prompt_builder import (
    PromptBuilder, 
    PromptContext,
    BrainstormIdeasTemplate,
    TechnicalDesignTemplate
)


class TestPromptBuilder:
    """Test cases for PromptBuilder class"""
    
    def test_init(self):
        """Test PromptBuilder initialization"""
        builder = PromptBuilder(max_context_length=2048)
        assert builder.max_context_length == 2048
        assert len(builder.templates) > 0
        assert "brainstorm_ideas" in builder.templates
    
    def test_build_task_prompt_brainstorm(self):
        """Test brainstorming prompt generation"""
        builder = PromptBuilder()
        
        context = {
            "project_state": {
                "Backlog": [
                    {"title": "Existing Idea 1"},
                    {"title": "Existing Idea 2"}
                ]
            }
        }
        
        prompt = builder.build_task_prompt("brainstorm_ideas", context)
        
        assert "Generate novel, creative research ideas" in prompt
        assert "Current backlog size: 2" in prompt
        assert "Existing Idea 1" in prompt
    
    def test_build_task_prompt_technical_design(self):
        """Test technical design prompt generation"""
        builder = PromptBuilder()
        
        context = {
            "target_issue": {
                "title": "Test Research Idea",
                "body": "This is a test idea description"
            }
        }
        
        prompt = builder.build_task_prompt("develop_technical_design", context)
        
        assert "technical design document" in prompt
        assert "Test Research Idea" in prompt
        assert "test idea description" in prompt
    
    def test_compress_text(self):
        """Test text compression"""
        builder = PromptBuilder()
        
        text = """
        This is a test.
        
        
        With extra    spaces.
        And multiple newlines.
        """
        
        compressed = builder._compress_text(text)
        lines = compressed.split('\n')
        
        assert len(lines) == 3  # Should remove empty lines
        assert "extra    spaces" in compressed  # Preserves internal spacing
    
    def test_truncate_prompt(self):
        """Test prompt truncation"""
        builder = PromptBuilder(max_context_length=100)
        
        # Create a long prompt
        long_prompt = "A" * 500
        
        truncated = builder._truncate_prompt(long_prompt)
        
        assert len(truncated) < len(long_prompt)
        assert "[... context truncated for length ...]" in truncated
        assert truncated.startswith("A" * 280)  # 70% of 400
        assert truncated.endswith("A" * 100)  # 25% of 400
    
    def test_cached_instructions(self):
        """Test instruction caching"""
        builder = PromptBuilder()
        
        # First call should populate cache
        instructions1 = builder._get_cached_instructions()
        assert "overview" in instructions1
        
        # Second call should use cache
        instructions2 = builder._get_cached_instructions()
        assert instructions1 is instructions2  # Same object


class TestPromptTemplates:
    """Test cases for specific prompt templates"""
    
    def test_brainstorm_template(self):
        """Test brainstorm ideas template"""
        template = BrainstormIdeasTemplate()
        
        context = PromptContext(
            task_type="brainstorm_ideas",
            project_state={"Backlog": [{"title": "Idea 1"}]},
            repository_instructions={},
            recent_activity=[],
            constraints={}
        )
        
        prompt = template.build(context)
        
        assert "AI research scientist" in prompt
        assert "3-5 highly creative" in prompt
        assert "- Idea 1" in prompt
    
    def test_technical_design_template(self):
        """Test technical design template"""
        template = TechnicalDesignTemplate()
        
        context = PromptContext(
            task_type="develop_technical_design",
            project_state={},
            repository_instructions={},
            recent_activity=[],
            constraints={
                "target_issue": {
                    "title": "Research Title",
                    "body": "Research description"
                }
            }
        )
        
        prompt = template.build(context)
        
        assert "technical design document" in prompt
        assert "Research Title" in prompt
        assert "Methodology" in prompt
        assert "Risk Assessment" in prompt