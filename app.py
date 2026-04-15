import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import json
import os

# --- STORAGE FUNCTIONS ---
DB_FILE = "texas_method_data.json"

def save_data():
    data = {"cycles": st.session_state.cycles, "unit": st.session_state.current_unit}
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data.get("cycles", []), data.get("unit", "LBS")
            return data, "LBS"
    return [], "LBS"

# --- CORE FUNCTIONS ---
def format_weight(weight):
    val = round(float(weight), 2)
    return f"{int(val)}" if val % 1 == 0 else f"{val}"

def round_to_plates(weight, smallest_unit):
    step = smallest_unit * 2
    return round(weight / step) * step

def convert_weight(val, to_unit):
    if to_unit == "LBS": return val * 2.20462
    return val / 2.20462

# --- UI CONFIG ---
st.set_page_config(page_title="Texas Method Tracker", layout="wide")

if 'cycles' not in st.session_state:
    cycles, saved_unit = load_data()
    st.session_state.cycles = cycles
    st.session_state.current_unit = saved_unit

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    unit_index = 0 if st.session_state.current_unit == "LBS" else 1
    new_unit = st.radio("Unit", ["LBS", "KG"], index=unit_index)
    theme_choice = st.selectbox("Theme", ["Deep Dark", "Light"])
    
    bg_color = "#0e1117" if theme_choice == "Deep Dark" else "#ffffff"
    text_color = "#ffffff" if theme_choice == "Deep Dark" else "#0e1117"

    if new_unit != st.session_state.current_unit:
        for cycle in st.session_state.cycles:
            for lift in cycle['lifts']:
                cycle['lifts'][lift]['rm'] = convert_weight(cycle['lifts'][lift]['rm'], new_unit)
                cycle['lifts'][lift]['inc'] = convert_weight(cycle['lifts'][lift]['inc'], new_unit)
            cycle['weight_log'] = [convert_weight(w, new_unit) for w in cycle['weight_log']]
        st.session_state.current_unit = new_unit
        save_data()
        st.rerun()

    plate = st.number_input(f"Plate Increment ({new_unit})", value=2.5 if new_unit == "LBS" else 1.25, step=0.25)
    st.divider()
    if st.button("Wipe All Data", type="primary"):
        st.session_state.cycles = []
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()

st.markdown(f"<style>.stApp {{ background-color: {bg_color}; color: {text_color}; }}</style>", unsafe_allow_html=True)
st.title("Texas Method Training Tracker")

# --- NEW CYCLE ---
with st.expander("Create New Cycle", expanded=len(st.session_state.cycles) == 0):
    with st.form("new_cycle"):
        c_name = st.text_input("Cycle Name")
        c_weeks = st.slider("Weeks", 1, 16, 8)
        c_bw = st.number_input(f"Initial BW ({new_unit})", value=80.0)
        col1, col2, col3, col4 = st.columns(4)
        with col1: s_rm, s_inc = st.text_input("Squat 5RM", "100"), st.text_input("Squat Inc", "2.5")
        with col2: b_rm, b_inc = st.text_input("Bench 5RM", "80"), st.text_input("Bench Inc", "2.5")
        with col3: o_rm, o_inc = st.text_input("OHP 5RM", "50"), st.text_input("OHP Inc", "2.5")
        with col4: d_rm, d_inc = st.text_input("Deadlift 5RM", "140"), st.text_input("Deadlift Inc", "5")
        if st.form_submit_button("Start"):
            st.session_state.cycles.append({
                "name": c_name, "weeks": int(c_weeks),
                "success_log": {m: [False]*int(c_weeks) for m in ["Squat", "Bench", "OHP", "Deadlift"]},
                "failed_week_log": [False] * int(c_weeks),
                "weight_log": [float(c_bw)] * int(c_weeks),
                "lifts": {
                    "Squat": {"rm": float(s_rm), "inc": float(s_inc)}, "Bench": {"rm": float(b_rm), "inc": float(b_inc)},
                    "OHP": {"rm": float(o_rm), "inc": float(o_inc)}, "Deadlift": {"rm": float(d_rm), "inc": float(d_inc)}
                }
            })
            save_data(); st.rerun()

# --- DISPLAY ---
if st.session_state.cycles:
    for idx, cycle in enumerate(reversed(st.session_state.cycles)):
        true_idx = len(st.session_state.cycles) - 1 - idx
        with st.container(border=True):
            st.subheader(f"Cycle: {cycle['name']}")
            
            # HAFTA SEÇİMİ (DROPDOWN KULLANIMI) - BU SAYESİNDE W1'E DÖNMEZ
            week_options = []
            auto_focus_idx = 0
            for w_i in range(cycle['weeks']):
                is_comp = any(cycle['success_log'][mv][w_i] for mv in ["Squat", "Bench", "OHP", "Deadlift"]) or cycle['failed_week_log'][w_i]
                label = f"Week {w_i+1} {'✅' if is_comp else ''}"
                week_options.append(label)
                if is_comp: auto_focus_idx = w_i + 1
            
            # Sınırı koru
            auto_focus_idx = min(auto_focus_idx, cycle['weeks'] - 1)
            
            # Selectbox kullanarak aktif haftayı state'de tutuyoruz
            selected_week_label = st.selectbox("Select Week", week_options, index=auto_focus_idx, key=f"select_{true_idx}")
            w_i = week_options.index(selected_week_label)
            
            # ANTRENMAN İÇERİĞİ
            counts = {mv: sum(1 for s in cycle['success_log'][mv][:w_i] if s == True) for mv in ["Squat", "Bench", "OHP", "Deadlift"]}
            
            if cycle['failed_week_log'][w_i]: st.warning("This week is marked as FAILED. No weight increase for next week.")
            
            is_a = (w_i + 1) % 2 != 0
            m_pres, w_pres = ("Bench", "OHP") if is_a else ("OHP", "Bench")
            cols = st.columns(3)
            days = [
                ("Monday", 0.90, "5x5", ["Squat", m_pres, "Deadlift"]),
                ("Wednesday", 0.70, "2x5", ["Squat", w_pres]),
                ("Friday", 1.00, "1x5", ["Squat", m_pres, "Deadlift"])
            ]

            for d_idx, (day_title, pct, rep_scheme, moves) in enumerate(days):
                with cols[d_idx]:
                    st.markdown(f"### {day_title}")
                    for mv in moves:
                        base_5rm = cycle['lifts'][mv]['rm'] + (cycle['lifts'][mv]['inc'] * counts[mv])
                        work_weight = round_to_plates(base_5rm * pct, plate)
                        st.info(f"**{mv}**: {rep_scheme} @ {format_weight(work_weight)} {new_unit}")
                    
                    if "Friday" in day_title:
                        st.divider()
                        for mv in moves:
                            val = cycle['success_log'][mv][w_i]
                            if st.checkbox(f"Crushed {mv}", value=val, key=f"chk_{true_idx}_{w_i}_{mv}"):
                                if not val:
                                    cycle['success_log'][mv][w_i] = True
                                    cycle['failed_week_log'][w_i] = False
                                    save_data(); st.rerun()
                            elif val:
                                cycle['success_log'][mv][w_i] = False
                                save_data(); st.rerun()
                        
                        if st.button("Mark Week as Failed", key=f"failbtn_{true_idx}_{w_i}"):
                            cycle['failed_week_log'][w_i] = True
                            for mv in ["Squat", "Bench", "OHP", "Deadlift"]: cycle['success_log'][mv][w_i] = False
                            save_data(); st.rerun()
