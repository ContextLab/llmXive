import pytest
import pandas as pd
import numpy as np
from code.identify_contaminated_windows import identify_contaminated_segments, generate_is_contaminated_mask

def test_identify_contaminated_segments_no_contamination():
    """Test that no segments are identified when there is no hacking."""
    data = {
        'G(t)': [1.0, 1.1, 0.9, 1.0, 1.2],
        'hacked_label': [False, False, False, False, False]
    }
    df = pd.DataFrame(data)
    segments = identify_contaminated_segments(df, window_size=2)
    assert segments == []

def test_identify_contaminated_segments_short_segment():
    """Test that short segments are ignored."""
    # Create a segment of length 3 (less than window_size 5)
    # G(t) needs to be > 3*MAD to be an event.
    # Let's make G(t) large in the middle.
    data = {
        'G(t)': [1.0, 1.0, 10.0, 10.0, 10.0, 1.0, 1.0],
        'hacked_label': [False, False, True, True, True, False, False]
    }
    df = pd.DataFrame(data)
    # MAD will be small, 10.0 will be > 3*MAD.
    # Segment length is 3. Window size is 5.
    segments = identify_contaminated_segments(df, window_size=5)
    assert segments == []

def test_identify_contaminated_segments_long_segment():
    """Test that long segments are identified."""
    # Create a segment of length 10 (greater than window_size 5)
    # G(t) needs to be > 3*MAD.
    # Base values: 1.0. Segment values: 100.0.
    base_vals = [1.0] * 5
    segment_vals = [100.0] * 10
    end_vals = [1.0] * 5
    g_vals = base_vals + segment_vals + end_vals
    hacked_vals = [False]*5 + [True]*10 + [False]*5

    data = {
        'G(t)': g_vals,
        'hacked_label': hacked_vals
    }
    df = pd.DataFrame(data)
    
    segments = identify_contaminated_segments(df, window_size=5)
    assert len(segments) == 1
    # Segment should be from index 5 to 14
    assert segments[0] == (5, 14)

def test_identify_contaminated_segments_mixed():
    """Test with multiple segments, some valid, some not."""
    # Short segment (len 3)
    # Long segment (len 10)
    # Short segment (len 2)
    
    # Base
    vals = [1.0] * 5
    # Short event (len 3)
    vals += [10.0] * 3
    # Gap
    vals += [1.0] * 3
    # Long event (len 10)
    vals += [100.0] * 10
    # Gap
    vals += [1.0] * 3
    # Short event (len 2)
    vals += [10.0] * 2
    
    hacked = [False]*5 + [True]*3 + [False]*3 + [True]*10 + [False]*3 + [True]*2
    
    data = {'G(t)': vals, 'hacked_label': hacked}
    df = pd.DataFrame(data)
    
    segments = identify_contaminated_segments(df, window_size=5)
    assert len(segments) == 1
    # Only the long one should be found
    # Start index: 5 + 3 + 3 = 11
    # End index: 11 + 10 - 1 = 20
    assert segments[0] == (11, 20)

def test_generate_is_contaminated_mask():
    """Test mask generation."""
    df = pd.DataFrame({'G(t)': [1, 2, 3], 'hacked_label': [False, False, False]})
    segments = [(1, 1)] # Just index 1
    mask = generate_is_contaminated_mask(df, segments)
    
    assert mask.iloc[0] == False
    assert mask.iloc[1] == True
    assert mask.iloc[2] == False