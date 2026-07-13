"""
Unit tests for phenomenological metrics.
Includes tests for consistency, stability, and marker analysis.
"""
import unittest
import sys
import os
from pathlib import Path
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.markers import count_markers_in_text, compute_marker_scores
from analysis.consistency import split_into_sentences, compute_pairwise_contradictions
from config import MARKER_DICTIONARIES


class TestMarkerMetrics(unittest.TestCase):
    """Tests for marker counting and scoring."""

    def test_count_sensory_keywords(self):
        """Verify that sensory markers are correctly identified."""
        text = "I see the light, hear the sound, and feel the warmth."
        count = count_markers_in_text(text, "sensory")
        # Expected: see, hear, feel (3)
        self.assertEqual(count, 3)

    def test_count_temporal_keywords(self):
        """Verify that temporal markers are correctly identified."""
        text = "Now I remember, then I forgot, before this moment."
        count = count_markers_in_text(text, "temporal")
        # Expected: now, then, before, moment (4)
        self.assertEqual(count, 4)

    def test_count_intentional_keywords(self):
        """Verify that intentional markers are correctly identified."""
        text = "I think, I believe, I desire, I intend to perceive."
        count = count_markers_in_text(text, "intentional")
        # Expected: think, believe, desire, intend, perceive (5)
        self.assertEqual(count, 5)


class TestConsistencyMetrics(unittest.TestCase):
    """Tests for consistency analysis."""

    def test_split_into_sentences(self):
        """Verify sentence splitting logic."""
        text = "First sentence. Second sentence! Third sentence?"
        sentences = split_into_sentences(text)
        self.assertEqual(len(sentences), 3)
        self.assertEqual(sentences[0].strip(), "First sentence")

    def test_pairwise_contradiction_detection(self):
        """Verify contradiction detection on known pairs."""
        # Note: This uses a small NLI model for CPU. 
        # We test the function signature and basic flow.
        sentences = [
            "The sky is blue.",
            "The sky is not blue."
        ]
        # We expect a higher contradiction score for these pairs compared to consistent ones.
        # The actual score depends on the model, but the function should return a float.
        scores = compute_pairwise_contradictions(sentences)
        self.assertIsInstance(scores, list)
        self.assertEqual(len(scores), 1) # 1 pair


class TestPhenomenologicalIncoherence(unittest.TestCase):
    """
    Test case for Freeman Dyson's review concern:
    Verify that the system does not penalize inherently incoherent but 
    phenomenologically accurate reports (e.g., stream-of-consciousness) 
    if they maintain internal marker consistency.
    """

    def test_stream_of_consciousness_marker_consistency(self):
        """
        A stream-of-consciousness report may lack syntactic coherence (jumping thoughts,
        fragmented sentences) but should still exhibit high internal marker consistency
        (sensory, temporal, intentional markers are present and frequent).
        
        This test verifies that the marker metric rewards the presence of phenomenological
        structure even when the text is syntactically fragmented.
        """
        # Simulated stream-of-consciousness text: fragmented but rich in markers
        stream_text = """
        Light. Bright light. Now. The light is now. 
        I feel the heat. Heat on skin. Feel it. 
        Think about the light. Why the light? 
        Before the dark. Then the light. 
        Smell smoke. Taste ash. 
        Desire to leave. Intend to move. 
        Moment passed. Duration of heat. 
        See the shadow. Hear the sound. 
        Believe it is real. Perceive the change.
        """
        
        # Calculate marker counts
        sensory_count = count_markers_in_text(stream_text, "sensory")
        temporal_count = count_markers_in_text(stream_text, "temporal")
        intentional_count = count_markers_in_text(stream_text, "intentional")
        
        # Calculate total marker density
        total_markers = sensory_count + temporal_count + intentional_count
        total_words = len(stream_text.split())
        marker_density = total_markers / total_words if total_words > 0 else 0
        
        # Assertions:
        # 1. The text must contain a significant number of markers (high density)
        # 2. The text is syntactically fragmented (low sentence count relative to words)
        
        # Expect at least 15 markers in this sample
        self.assertGreater(total_markers, 15, "Stream-of-consciousness text should have high marker count")
        
        # Expect marker density > 5%
        self.assertGreater(marker_density, 0.05, "Marker density should be significant")
        
        # Verify specific categories are present
        self.assertGreater(sensory_count, 0, "Sensory markers should be present")
        self.assertGreater(temporal_count, 0, "Temporal markers should be present")
        self.assertGreater(intentional_count, 0, "Intentional markers should be present")

    def test_incoherent_text_low_markers(self):
        """
        A truly incoherent text (random noise) should have low marker counts.
        This ensures the metric is not just counting words, but specific phenomenological terms.
        """
        noise_text = """
        blargh flibber zorp quux. 
        12345 random symbols @#$%.
        asdfjkl; qwertyuiop.
        """
        
        sensory_count = count_markers_in_text(noise_text, "sensory")
        temporal_count = count_markers_in_text(noise_text, "temporal")
        intentional_count = count_markers_in_text(noise_text, "intentional")
        
        self.assertEqual(sensory_count, 0, "Noise text should have no sensory markers")
        self.assertEqual(temporal_count, 0, "Noise text should have no temporal markers")
        self.assertEqual(intentional_count, 0, "Noise text should have no intentional markers")

    def test_phenomenological_incoherence_vs_syntactic_coherence(self):
        """
        Compare a syntactically perfect but phenomenologically empty report
        against a syntactically fragmented but phenomenologically rich report.
        
        The goal is to ensure the metric prioritizes phenomenological markers
        over syntactic perfection.
        """
        # Syntactically perfect, low markers
        syntactic_perfect = "The weather is nice today. The sun is shining. I am happy."
        
        # Syntactically fragmented, high markers
        phenomenological_rich = """
        Sun. Bright. Now. Feel heat. 
        Think of beach. Desire water. 
        Before rain. Then sun. 
        Smell salt. Taste sand. 
        Perceive light. Believe in warmth.
        """
        
        perfect_markers = (
            count_markers_in_text(syntactic_perfect, "sensory") +
            count_markers_in_text(syntactic_perfect, "temporal") +
            count_markers_in_text(syntactic_perfect, "intentional")
        )
        
        rich_markers = (
            count_markers_in_text(phenomenological_rich, "sensory") +
            count_markers_in_text(phenomenological_rich, "temporal") +
            count_markers_in_text(phenomenological_rich, "intentional")
        )
        
        # The rich text should have significantly more markers
        self.assertGreater(rich_markers, perfect_markers, 
                           "Phenomenologically rich text should have more markers than syntactically perfect but empty text")


if __name__ == "__main__":
    unittest.main()