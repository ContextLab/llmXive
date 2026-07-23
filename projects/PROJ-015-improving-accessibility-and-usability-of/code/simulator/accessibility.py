"""
Accessibility accommodations module for the simulator.
Provides UI components for accessibility settings and disability type selection.
"""
import streamlit as st
from typing import Dict, Any, Optional


def render_accessibility_settings() -> Dict[str, Any]:
    """
    Renders UI components for accessibility settings.
    
    Returns:
        dict: Dictionary containing selected accessibility settings.
    """
    st.subheader("Accessibility Settings")
    
    settings = {
        "font_size": "normal",
        "high_contrast": False,
        "keyboard_navigation": True,
        "screen_reader_mode": False
    }
    
    # Font size selection
    st.write("**Font Size**")
    font_options = {
        "Normal": "normal",
        "Large": "large",
        "Extra Large": "extra_large"
    }
    selected_font = st.selectbox(
        "Select font size:",
        list(font_options.keys()),
        key="accessibility_font_size"
    )
    settings["font_size"] = font_options[selected_font]
    
    # High contrast mode
    st.write("**Display**")
    settings["high_contrast"] = st.checkbox(
        "Enable high contrast mode",
        value=False,
        key="accessibility_high_contrast"
    )
    
    # Keyboard navigation
    settings["keyboard_navigation"] = st.checkbox(
        "Enable enhanced keyboard navigation",
        value=True,
        key="accessibility_keyboard_nav"
    )
    
    # Screen reader mode
    settings["screen_reader_mode"] = st.checkbox(
        "Enable screen reader mode",
        value=False,
        key="accessibility_screen_reader"
    )
    
    return settings


def render_disability_selector() -> str:
    """
    Renders a dropdown selector for participants to choose their disability type.
    
    Returns:
        str: The selected disability type, or None if no selection is made.
    """
    st.subheader("Disability Type Selection")
    
    st.markdown(
        """
        To help us improve accessibility for people with disabilities, 
        please select the disability type that best describes you. 
        This information will be used to tailor the interface accommodations.
        """
    )
    
    disability_options = [
        "Select your disability type...",
        "Visual Impairment (Blindness/Low Vision)",
        "Motor/Physical Disability (Limited Mobility/Dexterity)",
        "Hearing Impairment (Deaf/Hard of Hearing)",
        "Cognitive/Neurological Disability (Learning Disabilities/ADHD/Autism)",
        "Speech Disability",
        "Multiple Disabilities",
        "Prefer not to say"
    ]
    
    selected_disability = st.selectbox(
        "Disability Type:",
        disability_options,
        key="disability_selector"
    )
    
    # Return the selected value, or empty string if placeholder is selected
    if selected_disability == "Select your disability type...":
        return ""
    
    return selected_disability


def render_disability_specific_accommodations(disability_type: str) -> Dict[str, Any]:
    """
    Renders additional accommodation options based on the selected disability type.
    
    Args:
        disability_type (str): The selected disability type.
        
    Returns:
        dict: Dictionary of additional accommodations.
    """
    accommodations = {}
    
    if "Visual" in disability_type:
        st.write("**Visual Impairment Accommodations**")
        accommodations["text_to_speech"] = st.checkbox(
            "Enable text-to-speech for all interface text",
            value=False,
            key="vsi_tts"
        )
        accommodations["magnification"] = st.slider(
            "Screen magnification level (1x - 4x)",
            min_value=1,
            max_value=4,
            value=1,
            key="vsi_magnification"
        )
        accommodations["color_blind_mode"] = st.checkbox(
            "Enable color-blind friendly color scheme",
            value=False,
            key="vsi_colorblind"
        )
        
    elif "Motor" in disability_type:
        st.write("**Motor/Physical Disability Accommodations**")
        accommodations["extended_timeouts"] = st.checkbox(
            "Extend session timeouts for slower interactions",
            value=True,
            key="motor_timeouts"
        )
        accommodations["dwell_clicking"] = st.checkbox(
            "Enable dwell-clicking (hover to select)",
            value=False,
            key="motor_dwell"
        )
        accommodations["voice_control"] = st.checkbox(
            "Enable voice control commands",
            value=False,
            key="motor_voice"
        )
        
    elif "Hearing" in disability_type:
        st.write("**Hearing Impairment Accommodations**")
        accommodations["visual_alerts"] = st.checkbox(
            "Replace audio alerts with visual indicators",
            value=True,
            key="hearing_visual_alerts"
        )
        accommodations["captions"] = st.checkbox(
            "Enable captions for any audio content",
            value=True,
            key="hearing_captions"
        )
        
    elif "Cognitive" in disability_type:
        st.write("**Cognitive/Neurological Disability Accommodations**")
        accommodations["simplified_interface"] = st.checkbox(
            "Use simplified interface with reduced distractions",
            value=True,
            key="cog_simplified"
        )
        accommodations["step_by_step"] = st.checkbox(
            "Present tasks in smaller, step-by-step chunks",
            value=True,
            key="cog_steps"
        )
        accommodations["reading_level"] = st.selectbox(
            "Reading level adjustment:",
            ["Standard", "Easy", "Very Easy"],
            key="cog_reading_level"
        )
        
    elif "Speech" in disability_type:
        st.write("**Speech Disability Accommodations**")
        accommodations["text_alternative"] = st.checkbox(
            "Use text-based communication instead of voice",
            value=True,
            key="speech_text"
        )
        accommodations["prediction"] = st.checkbox(
            "Enable text prediction for faster input",
            value=False,
            key="speech_prediction"
        )
        
    return accommodations