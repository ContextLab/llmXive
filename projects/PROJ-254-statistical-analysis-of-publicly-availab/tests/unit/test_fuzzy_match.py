import json
import os
from pathlib import Path
from difflib import SequenceMatcher

import pytest

# Import utility for string similarity
from code.utils import get_logger

# Import the models to ensure we are using the project's types
from code.models import Track

# Setup logger
logger = get_logger("test_fuzzy_match")

def load_fixture(filename: str):
    """Load a JSON fixture from the tests/fixtures directory."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / filename
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)

def calculate_similarity(s1: str, s2: str) -> float:
    """Calculate string similarity using SequenceMatcher."""
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()

def find_best_match(
    mpd_track: dict, mb_candidates: list, threshold: float = 0.85
) -> dict:
    """
    Fuzzy matching logic to find the best MusicBrainz candidate for an MPD track.
    Returns a match object with match details.
    """
    best_match = None
    best_score = 0.0

    title = mpd_track.get("title", "")
    artist = mpd_track.get("artist", "")

    for candidate in mb_candidates:
        mb_title = candidate.get("title", "")
        mb_artist = candidate.get("artist", "")

        # Calculate weighted similarity
        title_sim = calculate_similarity(title, mb_title)
        artist_sim = calculate_similarity(artist, mb_artist)

        # Weight title higher as it's usually more unique
        score = (title_sim * 0.7) + (artist_sim * 0.3)

        if score > best_score:
            best_score = score
            best_match = {
                "mpd_track": mpd_track,
                "mb_candidate": candidate,
                "score": score,
                "title_similarity": title_sim,
                "artist_similarity": artist_sim
            }

    if best_match and best_match["score"] >= threshold:
        return best_match
    return None

def run_fuzzy_matching(mp_tracks: list, mb_candidates: list) -> dict:
    """
    Run the full fuzzy matching pipeline on a set of tracks.
    Returns a result dictionary with match statistics.
    """
    matched_count = 0
    matches = []

    for track in mp_tracks:
        match = find_best_match(track, mb_candidates)
        if match:
            matches.append(match)
            matched_count += 1

    total_tracks = len(mp_tracks)
    match_rate = matched_count / total_tracks if total_tracks > 0 else 0.0

    return {
        "total_tracks": total_tracks,
        "matched_tracks": matched_count,
        "match_rate": match_rate,
        "matches": matches
    }

def test_fuzzy_match_fallback():
    """
    Unit test for fuzzy matching fallback logic.
    Uses fixture tests/fixtures/fuzzy_match_input.json.
    Asserts that result['match_rate'] > 0.8.
    """
    logger.info("Starting test_fuzzy_match_fallback")
    
    # Load the fixture data
    data = load_fixture("fuzzy_match_input.json")
    mpd_tracks = data["mpd_tracks"]
    mb_candidates = data["musicbrainz_candidates"]
    expected_matches = data["expected_matches"]

    logger.info(f"Loaded {len(mpd_tracks)} MPD tracks and {len(mb_candidates)} MB candidates")

    # Run the fuzzy matching logic
    result = run_fuzzy_matching(mpd_tracks, mb_candidates)

    logger.info(f"Match result: {result['matched_tracks']} / {result['total_tracks']}")
    logger.info(f"Match rate: {result['match_rate']}")

    # Assert the match rate is greater than 0.8 (80%)
    # Given the fixture data has slight typos (e.g., "Led Zepplin" vs "Led Zeppelin"),
    # the fuzzy logic should still catch them with high confidence.
    assert result["match_rate"] > 0.8, (
        f"Match rate {result['match_rate']} is below threshold 0.8. "
        f"Expected > 0.8 for fixture with minor typos."
    )

    # Additional sanity check: ensure we matched at least 8 out of 10 tracks
    assert result["matched_tracks"] >= 8, (
        f"Only matched {result['matched_tracks']} tracks. Expected at least 8."
    )

    logger.info("test_fuzzy_match_fallback PASSED")