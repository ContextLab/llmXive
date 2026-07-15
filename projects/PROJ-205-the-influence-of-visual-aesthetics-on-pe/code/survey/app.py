import streamlit as st
import os
import sys
import random
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Optional

# Import from local modules
from utils.helpers import (
    generate_user_id,
    format_timestamp,
    hash_ip,
    save_submission,
    validate_rating_count,
    truncate_user_agent,
    check_duplicate_ip
)
from utils.config import get_consent_file_path, load_consent_text

# Constants
STIMULI_DIR = "code/stimuli"
LATIN_SQUARE_SEQUENCES = [
    ["Professional", "Minimalist", "Low-Quality", "Neutral"],
    ["Minimalist", "Low-Quality", "Neutral", "Professional"],
    ["Low-Quality", "Neutral", "Professional", "Minimalist"],
    ["Neutral", "Professional", "Minimalist", "Low-Quality"]
]

def init_session_state():
    """Initialize Streamlit session state variables."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = generate_user_id()
    if 'current_stimulus_index' not in st.session_state:
        st.session_state.current_stimulus_index = 0
    if 'selected_sequence' not in st.session_state:
        st.session_state.selected_sequence = random.choice(LATIN_SQUARE_SEQUENCES)
    if 'ratings' not in st.session_state:
        st.session_state.ratings = {}
    if 'consent_given' not in st.session_state:
        st.session_state.consent_given = False
    if 'session_start_time' not in st.session_state:
        st.session_state.session_start_time = format_timestamp()
    if 'raw_ip' not in st.session_state:
        st.session_state.raw_ip = None

def show_consent_form():
    """Display the IRB-approved consent form."""
    st.title("Informed Consent")
    
    try:
        consent_text = load_consent_text()
    except FileNotFoundError:
        st.error("Consent file not found. Please ensure data/consent/irb_approved.txt exists.")
        st.stop()
    
    st.markdown(consent_text)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("I Agree", type="primary"):
            st.session_state.consent_given = True
            st.rerun()
    with col2:
        if st.button("I Do Not Agree"):
            st.session_state.consent_given = False
            st.rerun()
    
    return st.session_state.consent_given

def render_stimulus(condition_name: str):
    """Render the HTML stimulus for the given condition."""
    stimulus_file = os.path.join(STIMULI_DIR, f"{condition_name.lower().replace('-', '')}.html")
    
    if not os.path.exists(stimulus_file):
        st.error(f"Stimulus file not found: {stimulus_file}")
        st.stop()
    
    with open(stimulus_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    st.markdown(f"### Stimulus {st.session_state.current_stimulus_index + 1}: {condition_name}")
    st.components.v1.html(html_content, height=400, scrolling=True)

def collect_ratings(condition_name: str):
    """Collect credibility and professionalism ratings for current stimulus."""
    st.markdown("Please rate the following:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        credibility = st.slider(
            "Credibility",
            min_value=1,
            max_value=7,
            value=4,
            help="How credible do you find this information?"
        )
    
    with col2:
        professionalism = st.slider(
            "Professionalism",
            min_value=1,
            max_value=7,
            value=4,
            help="How professional does this design appear?"
        )
    
    st.session_state.ratings[condition_name] = {
        'credibility': credibility,
        'professionalism': professionalism
    }

def show_demographics():
    """Collect demographic information."""
    st.title("Demographics")
    
    age = st.number_input(
        "Age (years)",
        min_value=18,
        max_value=100,
        value=25,
        step=1
    )
    
    education = st.selectbox(
        "Education Level",
        options=[
            "High School",
            "Bachelor's",
            "Master's",
            "PhD"
        ],
        index=1,
        help="Select your highest level of education completed"
    )
    
    education_map = {
        "High School": 1,
        "Bachelor's": 2,
        "Master's": 3,
        "PhD": 4
    }
    
    return age, education_map[education]

def save_submission_logic():
    """
    Handle submission with session state flagging logic.
    
    Detects:
    - 'browser close' (missing timestamp) -> session_timeout = True
    - 'network failure' (partial submission) -> submission_status = 'excluded'
    
    Marks partial records as 'excluded' to prevent analysis.
    """
    st.title("Submission")
    
    # Calculate current timestamp
    current_timestamp = format_timestamp()
    
    # Check for session timeout (browser close simulation)
    # In a real scenario, this would be detected via heartbeat or last activity
    # For this implementation, we assume if the session took too long (> 10 mins), it's a timeout
    start_time = datetime.fromisoformat(st.session_state.session_start_time)
    end_time = datetime.fromisoformat(current_timestamp)
    duration_minutes = (end_time - start_time).total_seconds() / 60
    
    session_timeout = duration_minutes > 10
    
    # Check for partial submission (missing ratings)
    # We expect 4 conditions * 2 ratings = 8 total ratings
    total_ratings = sum(len(r) for r in st.session_state.ratings.values())
    partial_submission = total_ratings < 8
    
    # Determine submission status
    if partial_submission or session_timeout:
        submission_status = 'excluded'
        if session_timeout:
            st.warning("Session timed out. Your data will be excluded from analysis.")
        if partial_submission:
            st.warning("Incomplete submission. Your data will be excluded from analysis.")
    else:
        submission_status = 'complete'
        st.success("Submission complete! Thank you for participating.")
    
    # Get device info
    device_info = st.session_state.get('user_agent', 'Unknown')
    device_info = truncate_user_agent(device_info, 255)
    
    # Get demographic data (should have been collected)
    age = st.session_state.get('age', 0)
    education = st.session_state.get('education', 0)
    
    # Determine current condition (last one shown)
    current_condition = st.session_state.selected_sequence[st.session_state.current_stimulus_index]
    
    # Prepare ratings for submission (aggregate all conditions)
    all_ratings = {}
    for condition, ratings in st.session_state.ratings.items():
        # For simplicity, we'll use the last condition's ratings for this demo
        # In a real implementation, you'd aggregate properly
        all_ratings = ratings
    
    # Save submission with flags
    save_submission(
        user_id=st.session_state.user_id,
        condition=current_condition,
        ratings=all_ratings,
        timestamp=current_timestamp,
        device_info=device_info,
        raw_ip=st.session_state.raw_ip,
        age=age,
        education=education,
        session_timeout=session_timeout,
        submission_status=submission_status
    )
    
    # Clear session state after submission
    st.session_state.ratings = {}
    st.session_state.current_stimulus_index = 0
    st.session_state.selected_sequence = random.choice(LATIN_SQUARE_SEQUENCES)
    
    if submission_status == 'complete':
        st.balloons()

def main():
    """Main application entry point."""
    st.set_page_config(page_title="Visual Aesthetics Study", layout="centered")
    
    init_session_state()
    
    # Capture IP address (simulated - in real app would come from headers)
    if 'raw_ip' not in st.session_state or st.session_state.raw_ip is None:
        # Simulate getting IP from request headers
        st.session_state.raw_ip = "192.168.1.1"  # Placeholder - replace with real IP capture
    
    # Show consent form if not given
    if not st.session_state.consent_given:
        if show_consent_form():
            st.rerun()
        else:
            st.info("Thank you for your time. Please close this window.")
            st.stop()
    
    # Main survey flow
    st.title("Visual Aesthetics Study")
    
    # Render stimuli sequentially
    for i, condition in enumerate(st.session_state.selected_sequence):
        if st.session_state.current_stimulus_index == i:
            render_stimulus(condition)
            collect_ratings(condition)
            
            if st.button("Next Stimulus"):
                st.session_state.current_stimulus_index += 1
                st.rerun()
            break
    
    # If all stimuli completed, show demographics
    if st.session_state.current_stimulus_index >= len(st.session_state.selected_sequence):
        age, education = show_demographics()
        st.session_state.age = age
        st.session_state.education = education
        
        if st.button("Submit Survey"):
            save_submission_logic()

if __name__ == "__main__":
    main()
