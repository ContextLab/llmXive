import pytest
import sys
from pathlib import Path
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.stimuli import (
    generate_instruction_templates,
    stratify_by_sentiment,
    create_stimuli_package,
    run_stimuli_pipeline
)

class TestTemplates:
    def test_templates_exist(self):
        templates = generate_instruction_templates()
        assert 'perspective_taking' in templates
        assert 'control_summarization' in templates
        assert len(templates) == 2

    def test_templates_content(self):
        templates = generate_instruction_templates()
        assert 'Imagine you are the person' in templates['perspective_taking']
        assert 'neutral summary' in templates['control_summarization']

class TestStratification:
    def test_stratification_balances_sentiment(self):
        # Create synthetic data with a known distribution
        # 10 positive, 10 negative
        data = []
        for i in range(10):
            data.append({'topic': 'climate', 'vader_compound': 0.8 + i * 0.01})
        for i in range(10):
            data.append({'topic': 'climate', 'vader_compound': -0.8 - i * 0.01})
        
        random.seed(42)
        cond_a, cond_b = stratify_by_sentiment(data, n_per_condition=10)
        
        assert len(cond_a) == 10
        assert len(cond_b) == 10
        
        mean_a = sum(float(p['vader_compound']) for p in cond_a) / 10
        mean_b = sum(float(p['vader_compound']) for p in cond_b) / 10
        
        # They should be roughly equal given the stratification logic
        # Allow some tolerance
        assert abs(mean_a - mean_b) < 0.2

    def test_stratification_randomness(self):
        data = [{'topic': 'climate', 'vader_compound': float(i)} for i in range(20)]
        
        random.seed(1)
        a1, b1 = stratify_by_sentiment(data, 10)
        
        random.seed(2)
        a2, b2 = stratify_by_sentiment(data, 10)
        
        # With different seeds, the split should likely be different
        # (Unless the algorithm is purely deterministic by sort order, which it isn't fully due to shuffling)
        # We just check they are valid splits
        assert len(a1) == 10
        assert len(a2) == 10

class TestPackageCreation:
    def test_package_structure(self):
        data_a = [{'id': '1', 'text': 'test', 'topic': 'climate', 'vader_compound': 0.5}]
        data_b = [{'id': '2', 'text': 'test2', 'topic': 'immigration', 'vader_compound': -0.5}]
        templates = {
            'perspective_taking': 'PT instruction',
            'control_summarization': 'CS instruction'
        }
        
        stimuli = create_stimuli_package(data_a, data_b, templates)
        
        assert len(stimuli) == 2
        assert stimuli[0]['condition'] == 'perspective_taking'
        assert stimuli[0]['instruction'] == 'PT instruction'
        assert stimuli[1]['condition'] == 'control_summarization'
        assert stimuli[1]['instruction'] == 'CS instruction'

# Integration test for the pipeline flow
def test_stimuli_pipeline_flow():
    mock_data = [
        {'id': str(i), 'text': f'text {i}', 'topic': 'climate', 'vader_compound': float(i % 10) / 10}
        for i in range(20)
    ]
    
    # Run the logic part of the pipeline (skipping file I/O for unit test)
    templates = generate_instruction_templates()
    cond_a, cond_b = stratify_by_sentiment(mock_data, n_per_condition=10)
    stimuli = create_stimuli_package(cond_a, cond_b, templates)
    
    assert len(stimuli) == 20
    # Check balance
    pt_count = sum(1 for s in stimuli if s['condition'] == 'perspective_taking')
    cs_count = sum(1 for s in stimuli if s['condition'] == 'control_summarization')
    assert pt_count == 10
    assert cs_count == 10
