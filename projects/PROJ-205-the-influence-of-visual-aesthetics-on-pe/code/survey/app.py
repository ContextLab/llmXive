import streamlit as st
import os
import sys
import time
import hashlib
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import (
    generate_user_id,
    hash_ip,
    format_timestamp,
    get_education_code,
    save_submission,
    check_duplicate_ip,
    get_submissions_csv_path
)
from utils.config import get_irb_protocol_id, get_consent_file_path

# Constants
TIMEOUT_THRESHOLD = 1800  # 30 minutes
MIN_RATINGS_REQUIRED = 8
MAX_USER_AGENT_LENGTH = 255

def init_session_state():
    """Initialize session state variables if they don't exist."""
    if 'participant_id' not in st.session_state:
        st.session_state.participant_id = generate_user_id()
    if 'current_stimulus_index' not in st.session_state:
        st.session_state.current_stimulus_index = 0
    if 'ratings' not in st.session_state:
        st.session_state.ratings = []
    if 'consent_given' not in st.session_state:
        st.session_state.consent_given = False
    if 'demographics' not in st.session_state:
        st.session_state.demographics = {}
    if 'last_active' not in st.session_state:
        st.session_state.last_active = time.time()
    if 'session_status' not in st.session_state:
        st.session_state.session_status = 'active'
    if 'submission_status' not in st.session_state:
        st.session_state.submission_status = 'pending'
    if 'ip_hash' not in st.session_state:
        st.session_state.ip_hash = None

def update_last_active():
    """Update the last active timestamp."""
    st.session_state.last_active = time.time()

def check_session_timeout():
    """Check if the session has timed out."""
    if time.time() - st.session_state.last_active > TIMEOUT_THRESHOLD:
        st.session_state.session_status = 'timeout'
        st.session_state.submission_status = 'incomplete'
        st.error("Session timed out due to inactivity. Please restart the survey.")
        st.stop()

def extract_and_validate_ip():
    """Extract, hash, and validate the user's IP address."""
    if 'ip_hash' in st.session_state and st.session_state.ip_hash is not None:
        return st.session_state.ip_hash

    # Try to get IP from headers
    ip = st.context.headers.get('X-Forwarded-For')
    if not ip:
        # Fallback for local testing or if header is missing
        ip = st.context.headers.get('X-Real-IP')
    
    if not ip:
        if os.getenv('MODE') == 'production':
            st.error("Unable to identify your session. Please try again.")
            st.stop()
        else:
            # In development, use a dummy hash
            ip = "127.0.0.1"
    
    hashed = hash_ip(ip)
    st.session_state.ip_hash = hashed
    
    # Check for duplicates immediately (optional real-time check, though post-hoc is main)
    if check_duplicate_ip(hashed):
        st.warning("We have detected a duplicate submission from this IP. Your data will be flagged for review.")
        st.session_state.duplicate_flag = True
    else:
        st.session_state.duplicate_flag = False
        
    return hashed

def show_consent_form():
    """Display the IRB-approved consent form."""
    protocol_id = get_irb_protocol_id()
    consent_file = get_consent_file_path()
    
    st.title("Informed Consent")
    st.header(f"Protocol ID: {protocol_id}")
    
    try:
        with open(consent_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Replace placeholder if present (handled by T011d logic mostly, but safe to check)
            if "<<INSERT_IRB_APPROVED_TEXT_HERE>>" in content:
                st.error("IRB-approved text is missing. Please contact the administrator.")
                st.stop()
            st.markdown(content)
    except FileNotFoundError:
        st.error("Consent form could not be loaded.")
        st.stop()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("I Agree"):
            st.session_state.consent_given = True
            st.rerun()
    with col2:
        if st.button("I Do Not Agree"):
            st.session_state.consent_given = False
            st.switch_page("withdrawal.py")

def render_stimulus():
    """Render the current stimulus."""
    stimuli_dir = os.path.join(os.path.dirname(__file__), '..', 'stimuli')
    stimuli_files = sorted([f for f in os.listdir(stimuli_dir) if f.endswith('.html')])
    
    if not stimuli_files:
        st.error("No stimuli found.")
        st.stop()
    
    if st.session_state.current_stimulus_index >= len(stimuli_files):
        # All stimuli shown, move to demographics
        st.session_state.current_stimulus_index = len(stimuli_files)
        st.rerun()
        return

    current_file = stimuli_files[st.session_state.current_stimulus_index]
    with open(os.path.join(stimuli_dir, current_file), 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    st.components.v1.html(html_content, height=600, scrolling=True)
    
    if st.button("Next Stimulus"):
        st.session_state.current_stimulus_index += 1
        st.rerun()

def show_demographics():
    """Show the demographic input form."""
    st.title("Demographics")
    
    with st.form("demographics_form"):
        age = st.number_input("Age (years)", min_value=18, max_value=120, step=1)
        education = st.selectbox(
            "Education Level",
            ["High School", "Bachelor's", "Master's", "PhD"]
        )
        
        submitted = st.form_submit_button("Submit")
        if submitted:
            st.session_state.demographics = {
                "age": age,
                "education": education
            }
            st.rerun()

def collect_ratings():
    """Collect ratings for the current stimulus."""
    # This would be called after viewing a stimulus if we wanted per-stimulus ratings
    # But the task implies collecting ratings for the whole set or per stimulus.
    # Based on T018, we need multi-point Likert inputs.
    # Let's assume we collect ratings after the stimuli loop, or per stimulus.
    # The prompt says "collect multiple ratings".
    # For simplicity in this flow, we'll collect ratings after all stimuli or per stimulus.
    # Let's implement per-stimulus rating collection to ensure data integrity.
    
    # Actually, looking at T022d, it asks to write Age and Education to CSV.
    # The ratings are collected via T018.
    # We need to integrate the rating collection into the flow.
    
    # Let's assume the flow is:
    # 1. Consent
    # 2. Stimuli (loop) -> collect rating for each
    # 3. Demographics
    # 4. Submit all
    
    # But T022d specifically mentions writing Age/Education to the CSV.
    # So we need to ensure that when we submit, we include demographics.
    
    # Let's restructure:
    # - Show stimuli one by one.
    # - After each, ask for ratings.
    # - After all stimuli, ask for demographics.
    # - Submit.
    
    # However, the task T022d is about writing the data.
    # The `save_submission` function in helpers.py handles the writing.
    # We just need to call it with the right arguments.
    
    pass

def submit_survey():
    """Submit the survey data."""
    if not st.session_state.demographics:
        st.error("Please provide demographics first.")
        return

    demographics = st.session_state.demographics
    age = demographics['age']
    education = demographics['education']
    
    # We need to iterate through ratings and save each
    # Assuming st.session_state.ratings contains a list of dicts with stimulus_id, credibility, professionalism
    
    if not st.session_state.ratings:
        st.error("No ratings collected.")
        return

    for rating in st.session_state.ratings:
        save_submission(
            participant_id=st.session_state.participant_id,
            stimulus_id=rating['stimulus_id'],
            credibility=rating['credibility'],
            professionalism=rating['professionalism'],
            hashed_ip=st.session_state.ip_hash,
            age=age,
            education=education,
            timestamp=format_timestamp()
        )
    
    st.success("Thank you for your participation!")
    st.balloons()

def main():
    """Main entry point for the survey app."""
    init_session_state()
    update_last_active()
    check_session_timeout()
    
    # Extract IP early
    extract_and_validate_ip()

    if not st.session_state.consent_given:
        show_consent_form()
        return

    # Check if we need to show demographics first or stimuli
    # Let's show stimuli first, then demographics
    if st.session_state.current_stimulus_index < 4: # Assuming 4 stimuli
        st.title(f"Stimulus {st.session_state.current_stimulus_index + 1} of 4")
        render_stimulus()
        
        # Collect ratings for this stimulus
        col1, col2 = st.columns(2)
        with col1:
            credibility = st.slider("Credibility (1-7)", 1, 7, 4)
        with col2:
            professionalism = st.slider("Professionalism (1-7)", 1, 7, 4)
        
        if st.button("Save Rating and Next"):
            st.session_state.ratings.append({
                'stimulus_id': f"stim_{st.session_state.current_stimulus_index}",
                'credibility': credibility,
                'professionalism': professionalism
            })
            st.session_state.current_stimulus_index += 1
            st.rerun()
    else:
        # All stimuli done, show demographics
        st.title("Demographics")
        show_demographics()
        
        if st.session_state.demographics:
            # Show submit button
            if st.button("Submit Survey"):
                submit_survey()

if __name__ == "__main__":
    main()
