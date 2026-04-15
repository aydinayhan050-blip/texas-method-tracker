import streamlit as st
import json
from datetime import datetime
from streamlit_local_storage import LocalStorage

# --- UI & LOCAL STORAGE SETUP ---
st.set_page_config(page_title="Texas Method Planner", layout="wide")
local_storage = LocalStorage()

# --- ORIGINAL LOGIC FUNCTIONS ---
def round_to_plates(weight, smallest_plate):
    step = smallest_plate * 2
    return round(weight / step) * step

# --- SYNC LOGIC ---
def sync_to_device():
    if 'data' in st.session_state:
        local_storage.setItem("texas_planner_db", json.dumps(st.session_state.data))

def load_from_device():
    saved = local_storage.getItem("texas_planner_db")
    return json.loads(saved) if saved else None

# --- INITIALIZE SESSION ---
if 'data' not in st.session_state:
    stored = load_from_device()
    if stored:
        st.session_state.data = stored
    else:
        st.session_state.data = None # Start fresh

# --- CSS (Hardcore Theme) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .crush-box { border: 2px solid #ff0000; padding: 15px; border-radius: 10px; background-color: #1a0000; }
    .signature { font-size: 14px; color: #555; text-align: center; margin-top: 50px; border-top: 1px solid #333; padding-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("Ultimate Texas Method Planner 🦾")

# --- SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("⚙️ Configuration")
    smallest_plate = st.number_input("Smallest Plate (kg)", value=1.25, step=0.25)
    if st.button("🔥 Reset All Progress", type="primary"):
        st.session_state.data = None
        sync_to_device()
        st.rerun()

# --- INPUT FORM (Only shows if no data) ---
if st.session_state.data is None:
    with st.form("init_form"):
        st.subheader("Enter Starting 5RM Values")
        weeks = st.slider("Weeks to Generate", 1, 12, 8)
        col1, col2 = st.columns(2)
        with col1:
            sq = st.number_input("Squat 5RM (kg)", value=100.0)
            bp = st.number_input("Bench Press 5RM (kg)", value=80.0)
        with col2:
            ohp = st.number_input("Overhead Press 5RM (kg)", value=50.0)
            dl = st.number_input("Deadlift 5RM (kg)", value=140.0)
        
        if st.form_submit_button("Generate Cycle"):
            st.session_state.data = {
                "weeks_total": weeks,
                "lifts": {
                    "Squat": {"current_5rm": sq, "inc": 2.5},
                    "Bench Press": {"current_5rm": bp, "inc": 2.5},
                    "Overhead Press": {"current_5rm": ohp, "inc": 1.0},
                    "Deadlift": {"current_5rm": dl, "inc": 5.0}
                },
                "history": {} # To track which Friday PRs were crushed
            }
            sync_to_device()
            st.rerun()

# --- MAIN PLANNER ---
if st.session_state.data:
    data = st.session_state.data
    
    for w in range(1, data["weeks_total"] + 1):
        with st.expander(f"WEEK {w} " + ("(Pattern A)" if w % 2 != 0 else "(Pattern B)"), expanded=(w==1)):
            
            # Pattern Logic
            if w % 2 != 0:
                mon_p, wed_p, fri_p = "Bench Press", "Overhead Press", "Bench Press"
            else:
                mon_p, wed_p, fri_p = "Overhead Press", "Bench Press", "Overhead Press"
            
            # Calculate weights based on previous successes
            # (If Friday was crushed, increment applies to all subsequent weeks)
            def get_current_w(lift_name, week_num):
                base = data["lifts"][lift_name]["current_5rm"]
                inc = data["lifts"][lift_name]["inc"]
                # Count how many times this lift was crushed in weeks strictly BEFORE current week
                past_successes = sum(1 for wk in range(1, week_num) if data["history"].get(f"w{wk}_{lift_name}", False))
                return base + (past_successes * inc)

            col_m, col_w, col_f = st.columns(3)
            
            # --- MONDAY ---
            with col_m:
                st.markdown("### MONDAY (Volume)")
                sq_v = round_to_plates(get_current_w("Squat", w) * 0.90, smallest_plate)
                pr_v = round_to_plates(get_current_w(mon_p, w) * 0.90, smallest_plate)
                dl_v = round_to_plates(get_current_w("Deadlift", w) * 0.90, smallest_plate)
                st.info(f"**Squat**: 5x5 @ {sq_v} kg\n\n**{mon_p}**: 5x5 @ {pr_v} kg\n\n**Deadlift**: 1x5 @ {dl_v} kg")

            # --- WEDNESDAY ---
            with col_w:
                st.markdown("### WEDNESDAY (Light)")
                sq_l = round_to_plates(get_current_w("Squat", w) * 0.70, smallest_plate)
                pr_l = round_to_plates(get_current_w(wed_p, w) * 0.70, smallest_plate)
                st.success(f"**Squat**: 2x5 @ {sq_l} kg\n\n**{wed_p}**: 3x5 @ {pr_l} kg\n\n**Chin-ups**: 3x Failure\n\n**Hypers**: 5x10")

            # --- FRIDAY ---
            with col_f:
                st.markdown("### FRIDAY (Intensity)")
                st.markdown('<div class="crush-box"><b>Did You Crush It?</b>', unsafe_allow_html=True)
                
                friday_lifts = ["Squat", fri_p, "Deadlift"]
                for lift in friday_lifts:
                    int_w = round_to_plates(get_current_w(lift, w), smallest_plate)
                    key = f"w{w}_{lift}"
                    checked = data["history"].get(key, False)
                    
                    if st.checkbox(f"{lift}: 1x5 @ {int_w} kg", value=checked, key=f"cb_{key}"):
                        if not checked:
                            st.session_state.data["history"][key] = True
                            sync_to_device()
                            st.rerun()
                    elif checked: # Handle unchecking
                        st.session_state.data["history"][key] = False
                        sync_to_device()
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="signature">Assistant Exercises by Aydın Ayhan</div>', unsafe_allow_html=True)
