"""
Unit tests for survey randomization logic (within-subject constraint).

This module tests the core randomization engine used in User Story 2 to ensure
that no scenario appears twice with the same salience level for a single participant.

Dependencies:
- code/survey_sim.py: Contains the randomization logic to be tested.
- code/models.py: Contains data models (Scenario, StimulusVariant).
"""
import pytest
import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from survey_sim import (
    SurveyRandomizationError,
    load_scenarios,
    load_stimulus_variants,
    build_variant_map,
    generate_latin_square_order,
    create_participant_sequences,
)
from models import Scenario, StimulusVariant, SalienceLevel


class MockVariantMap:
    """
    Mock variant map for testing purposes to avoid file I/O dependencies.
    Maps scenario_id -> list of StimulusVariant objects.
    """
    def __init__(self, variants: List[StimulusVariant]):
        self._map = {}
        for v in variants:
            if v.scenario_id not in self._map:
                self._map[v.scenario_id] = []
            self._map[v.scenario_id].append(v)
    
    def get_variants(self, scenario_id: str) -> List[StimulusVariant]:
        return self._map.get(scenario_id, [])
    
    def get_scenario_ids(self) -> List[str]:
        return list(self._map.keys())


def create_test_variants() -> List[StimulusVariant]:
    """
    Create a deterministic set of StimulusVariants for testing.
    Creates 3 scenarios, each with Low, Medium, High salience.
    """
    variants = []
    scenarios = ["SCN001", "SCN002", "SCN003"]
    salience_levels = [SalienceLevel.LOW, SalienceLevel.MEDIUM, SalienceLevel.HIGH]
    
    idx = 0
    for scn_id in scenarios:
        for sal in salience_levels:
            variants.append(
                StimulusVariant(
                    id=f"VAR_{idx:03d}",
                    scenario_id=scn_id,
                    salience_level=sal,
                    image_path=f"data/processed/{scn_id}_{sal.value}.jpg"
                )
            )
            idx += 1
    return variants


class TestWithinSubjectConstraint:
    """
    Test suite for the within-subject randomization constraint.
    
    The core requirement (FR-002/US2) is that a participant sees each scenario
    exactly once, but with a different salience level each time they encounter
    that scenario in the full study design (or rather, in a single session,
    they see a specific scenario only once).
    
    Wait, re-reading the task: "no scenario appears twice with the same salience level".
    Actually, in a standard within-subject design for this study:
    - Each participant sees a subset of scenarios.
    - If a scenario is repeated (which shouldn't happen in a single session usually),
      it must be with a DIFFERENT salience level.
    - However, the task description says: "generate sequences where no scenario 
      appears twice with the same salience level for a participant."
    - This implies that if a scenario ID appears multiple times in the sequence,
      the salience_level must differ.
    - In a standard Latin Square design for N conditions, each participant sees
      each condition once. If we have 3 scenarios and 3 salience levels, 
      a participant might see SCN001 (Low), SCN002 (Med), SCN003 (High).
      They should NOT see SCN001 (Low) again.
    
    The test verifies:
    1. No duplicate (scenario_id, salience_level) pairs in a single participant's sequence.
    2. (Optional but good) If the design allows repeated scenarios, they must have different salience.
    """

    def test_no_duplicate_scenario_salience_pairs(self):
        """
        Verify that no scenario appears twice with the same salience level 
        in a generated participant sequence.
        """
        variants = create_test_variants()
        variant_map = MockVariantMap(variants)
        
        # Generate sequences for 10 participants
        participant_ids = [f"P{str(i).zfill(3)}" for i in range(1, 11)]
        
        # We need to call create_participant_sequences. 
        # Since it expects file paths, we will mock the loading or use the logic directly.
        # The function create_participant_sequences relies on load_scenarios/load_stimulus_variants.
        # To test the logic in isolation, we will call generate_latin_square_order 
        # and create_participant_sequences logic manually or mock the file system.
        
        # Let's assume we have a way to generate the sequence.
        # We'll simulate the core logic of create_participant_sequences here 
        # to ensure the constraint holds, as the real function depends on file I/O.
        
        # Simulate the logic:
        # 1. Get all scenarios
        # 2. For each participant, assign a permutation of salience levels to scenarios
        #    such that no (scenario, salience) is repeated.
        
        scenarios = variant_map.get_scenario_ids()
        all_salience = list(SalienceLevel)
        
        for pid in participant_ids:
            # Simulate the assignment logic found in survey_sim
            # We need to ensure that for a given participant, 
            # if we list (scenario, salience), all pairs are unique.
            
            # Since we are testing the *logic* of the randomization,
            # we will invoke the actual function if possible, or test the helper.
            # The helper generate_latin_square_order is key.
            
            # Let's test generate_latin_square_order directly first
            order = generate_latin_square_order(scenarios, all_salience, seed=42)
            
            # Verify the order
            seen_pairs = set()
            for item in order:
                # item should be a dict or object with scenario_id and salience_level
                # Based on typical implementation, let's assume it returns a list of dicts
                # or we construct the sequence manually.
                pass

        # Since the real function depends on file I/O, let's test the core algorithm
        # by mocking the data loading.
        
        # Re-implement the core constraint check logic here to be tested against
        # the output of the actual function if we can mock the files.
        # But the task asks for a unit test for the *randomization logic*.
        
        # Let's create a test that directly exercises the logic without file I/O
        # by calling the internal logic of create_participant_sequences if exposed,
        # or by mocking the load functions.
        
        # Strategy: Mock load_scenarios and load_stimulus_variants to return our test data.
        # Then call create_participant_sequences.
        
        # However, since we cannot easily mock module-level functions in the imported module
        # without patching, let's test the helper function `generate_latin_square_order`
        # which is pure logic.
        
        # Test 1: generate_latin_square_order produces unique (scenario, salience) pairs
        scenarios = ["S1", "S2", "S3"]
        saliences = [SalienceLevel.LOW, SalienceLevel.MEDIUM, SalienceLevel.HIGH]
        
        # Run multiple times with different seeds to ensure robustness
        for seed in range(100):
            order = generate_latin_square_order(scenarios, saliences, seed=seed)
            
            # Verify structure
            assert len(order) == len(scenarios), f"Order length mismatch for seed {seed}"
            
            # Verify uniqueness of (scenario, salience)
            pairs = set()
            for item in order:
                # item is expected to be a dict: {'scenario_id': ..., 'salience_level': ...}
                # or similar. Let's assume the structure based on typical implementation.
                # If the function returns a list of (scenario, salience) tuples:
                if isinstance(item, tuple):
                    scn, sal = item
                elif isinstance(item, dict):
                    scn = item['scenario_id']
                    sal = item['salience_level']
                else:
                    # Fallback: assume it's a StimulusVariant or similar
                    # We need to be sure of the return type.
                    # Let's assume it returns a list of dicts for this test.
                    raise AssertionError(f"Unexpected item type: {type(item)}")
                
                pair = (scn, sal)
                assert pair not in pairs, f"Duplicate pair {pair} found in seed {seed}"
                pairs.add(pair)

    def test_latin_square_balanced_assignment(self):
        """
        Verify that the Latin Square design ensures balanced assignment across participants.
        Each salience level should appear roughly equally for each scenario across the cohort.
        """
        scenarios = ["S1", "S2", "S3"]
        saliences = [SalienceLevel.LOW, SalienceLevel.MEDIUM, SalienceLevel.HIGH]
        
        num_participants = 30
        all_assignments = []
        
        for i in range(num_participants):
            order = generate_latin_square_order(scenarios, saliences, seed=i)
            all_assignments.append(order)
        
        # Count occurrences of (scenario, salience)
        counts = {}
        for scn in scenarios:
            for sal in saliences:
                counts[(scn, sal)] = 0
        
        for order in all_assignments:
            for item in order:
                if isinstance(item, tuple):
                    scn, sal = item
                elif isinstance(item, dict):
                    scn = item['scenario_id']
                    sal = item['salience_level']
                else:
                    continue
                counts[(scn, sal)] += 1
        
        # In a perfect Latin Square with N participants and N conditions,
        # each pair should appear exactly once per N participants.
        # With 3 scenarios and 3 saliences, a block of 3 participants should cover all 9 pairs once.
        # With 30 participants (10 blocks), each pair should appear 10 times.
        for pair, count in counts.items():
            # Allow small variance due to randomness if not strictly Latin Square
            # But generate_latin_square_order should be deterministic for the algorithm.
            # If it's a proper Latin Square generator, count should be exactly 10.
            # Let's assert it's close to 10 (allowing for implementation variations)
            assert count == 10, f"Count for {pair} is {count}, expected 10"

    def test_empty_scenario_list(self):
        """
        Test behavior when no scenarios are provided.
        """
        with pytest.raises(SurveyRandomizationError):
            generate_latin_square_order([], [SalienceLevel.LOW])

    def test_mismatched_dimensions(self):
        """
        Test behavior when number of scenarios != number of salience levels.
        Latin Square requires N x N.
        """
        with pytest.raises(SurveyRandomizationError):
            generate_latin_square_order(["S1", "S2"], [SalienceLevel.LOW])

    def test_duplicate_salience_in_input(self):
        """
        Test behavior when input salience list has duplicates.
        """
        with pytest.raises(SurveyRandomizationError):
            generate_latin_square_order(["S1", "S2"], [SalienceLevel.LOW, SalienceLevel.LOW])

if __name__ == "__main__":
    pytest.main([__file__, "-v"])