"""
Integration test for the correlation pipeline with synthetic data.

This test validates the end-to-end flow of User Story 2:
1. Generates a controlled synthetic dataset where divergence scores
   are perfectly negatively correlated with simulated failure rates.
2. Executes the AXPO simulator logic (mocked for deterministic control).
3. Runs the analysis service to compute Pearson correlation.
4. Verifies that the output demonstrates a strong negative relationship.

NOTE: While the task description mentions "synthetic data", this refers to
the INPUT DATA GENERATION for the purpose of the integration test.
The pipeline logic (correlation calculation) must remain real and use
actual statistical libraries (scipy.stats).
"""

import pytest
import numpy as np
import pandas as pd
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

# Import pipeline components
from src.lib.axpo_simulator import SimulationResult, AXPOSimulator
from src.services.analysis_service import AnalysisService, CorrelationResult

# Constants for synthetic generation
N_SAMPLES = 100
SEED = 42
NOISE_SCALE = 0.05  # Small noise to make it realistic but still strongly correlated


@dataclass
class SyntheticRecord:
    """A record for the synthetic dataset."""
    problem_id: str
    divergence_score: float
    failure_rate: float
    problem_type: str


def generate_synthetic_correlation_data(n: int, seed: int = 42) -> List[SyntheticRecord]:
    """
    Generates synthetic data where divergence_score and failure_rate
    are perfectly negatively correlated (r ≈ -1.0).

    Formula: failure_rate = (1 - divergence_score) + small_noise
    """
    rng = np.random.default_rng(seed)
    records = []

    for i in range(n):
        # Divergence score uniformly distributed [0, 1]
        divergence = rng.uniform(0.0, 1.0)

        # Failure rate is inversely proportional to divergence
        # High divergence -> Low failure rate
        # Low divergence -> High failure rate
        base_failure = 1.0 - divergence
        noise = rng.normal(0, NOISE_SCALE)
        failure = max(0.0, min(1.0, base_failure + noise))

        records.append(
            SyntheticRecord(
                problem_id=f"synth_{i:04d}",
                divergence_score=divergence,
                failure_rate=failure,
                problem_type="synthetic_mixed"
            )
        )

    return records


class MockAXPOSimulator:
    """
    Mock simulator that returns pre-computed failure rates from the synthetic data.
    This bypasses the heavy simulation logic for the integration test while
    exercising the data merging logic.
    """
    def __init__(self, synthetic_records: List[SyntheticRecord]):
        self.synthetic_records = synthetic_records

    def run_batch(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Simulates running the AXPO simulator on the provided records.
        In a real scenario, this would execute the agent simulation.
        Here, we map the input problem_id to our pre-generated synthetic failure rates.
        """
        results = []
        for record in records:
            pid = record.get("problem_id")
            # Find matching synthetic record
            match = next((r for r in self.synthetic_records if r.problem_id == pid), None)
            if match:
                results.append({
                    "problem_id": pid,
                    "failure_rate": match.failure_rate,
                    "success_rate": 1.0 - match.failure_rate,
                    "simulated": True
                })
            else:
                # Fallback for records not in synthetic set (shouldn't happen in this test)
                results.append({
                    "problem_id": pid,
                    "failure_rate": 0.5,
                    "success_rate": 0.5,
                    "simulated": False
                })
        return results


class MockDivergenceModel:
    """
    Mock divergence model that returns pre-computed scores from synthetic data.
    """
    def __init__(self, synthetic_records: List[SyntheticRecord]):
        self.synthetic_records = synthetic_records

    def compute_batch(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for record in records:
            pid = record.get("problem_id")
            match = next((r for r in self.synthetic_records if r.problem_id == pid), None)
            if match:
                results.append({
                    "problem_id": pid,
                    "semantic_divergence_score": match.divergence_score,
                    "embedding_vector": None # Skip actual vector for speed
                })
            else:
                results.append({
                    "problem_id": pid,
                    "semantic_divergence_score": 0.0,
                    "embedding_vector": None
                })
        return results


@pytest.fixture
def synthetic_data() -> List[SyntheticRecord]:
    """Fixture to generate the synthetic dataset."""
    return generate_synthetic_correlation_data(N_SAMPLES, SEED)


@pytest.fixture
def input_records(synthetic_data) -> List[Dict[str, Any]]:
    """Converts synthetic records to the dictionary format expected by the pipeline."""
    return [asdict(record) for record in synthetic_data]


def test_correlation_pipeline_negative_correlation(input_records, synthetic_data):
    """
    Integration test: Verify that the pipeline correctly identifies a strong
    negative correlation between divergence scores and failure rates.
    """
    # 1. Setup mocks
    mock_simulator = MockAXPOSimulator(synthetic_data)
    mock_divergence = MockDivergenceModel(synthetic_data)

    # 2. Simulate the pipeline steps

    # Step A: Get Divergence Scores (Simulated US1 output)
    divergence_results = mock_divergence.compute_batch(input_records)

    # Step B: Get Failure Rates (Simulated US2 AXPO output)
    simulation_results = mock_simulator.run_batch(input_records)

    # 3. Merge Data
    # Create a dataframe to merge results by problem_id
    df_div = pd.DataFrame(divergence_results)
    df_sim = pd.DataFrame(simulation_results)

    merged_df = pd.merge(df_div, df_sim, on="problem_id", how="inner")

    assert len(merged_df) == N_SAMPLES, "Merge should result in N_SAMPLES records"
    assert "semantic_divergence_score" in merged_df.columns
    assert "failure_rate" in merged_df.columns

    # 4. Run Analysis Service (Real calculation)
    analysis_service = AnalysisService()

    # Perform the correlation test
    # We pass the specific columns to the service
    correlation_result = analysis_service.compute_pearson_correlation(
        x=merged_df["semantic_divergence_score"],
        y=merged_df["failure_rate"]
    )

    # 5. Assertions
    # The hypothesis is: Divergence is negatively correlated with failure.
    # High Divergence -> Low Failure.
    # Therefore, we expect r to be close to -1.0.

    r_value = correlation_result.r_value
    p_value = correlation_result.p_value

    print(f"Correlation Result: r={r_value:.4f}, p={p_value:.4e}")

    # Assert strong negative correlation (r < -0.8)
    # Given our synthetic generation: failure = 1 - divergence + noise
    # The correlation should be very close to -1.0.
    assert r_value < -0.8, f"Expected strong negative correlation (r < -0.8), got {r_value:.4f}"

    # Assert statistical significance (p < 0.05)
    assert p_value < 0.05, f"Expected significant p-value (< 0.05), got {p_value:.4e}"

    # Verify the direction is correct (negative)
    assert r_value < 0, "Correlation coefficient must be negative"

    # Optional: Verify the AnalysisService flag logic if it exists
    # If the service returns a 'significant_negative' flag, check it.
    if hasattr(correlation_result, 'significant_negative'):
        assert correlation_result.significant_negative is True, "Flag should indicate significant negative correlation"


def test_pipeline_handles_mismatched_ids(input_records, synthetic_data):
    """
    Integration test: Verify pipeline behavior when IDs don't match perfectly.
    (Edge case for the merge logic)
    """
    # Modify input to have an extra record not in synthetic data
    extra_record = {"problem_id": "extra_001", "some_field": "value"}
    test_records = input_records + [extra_record]

    mock_simulator = MockAXPOSimulator(synthetic_data)
    mock_divergence = MockDivergenceModel(synthetic_data)

    # Run pipeline
    div_res = mock_divergence.compute_batch(test_records)
    sim_res = mock_simulator.run_batch(test_records)

    df_div = pd.DataFrame(div_res)
    df_sim = pd.DataFrame(sim_res)

    # Inner join should drop the extra record
    merged = pd.merge(df_div, df_sim, on="problem_id", how="inner")

    # The extra record should not be in the merged result
    assert "extra_001" not in merged["problem_id"].values
    assert len(merged) == N_SAMPLES