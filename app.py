import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import json
import os

# --- STORAGE FUNCTIONS ---
DB_FILE = "texas_method_data.json"

def save_data():
    data = {
        "cycles": st.session_state.cycles,
        "unit": st.session_state.current_unit
    }
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

def get_warmup_sets(target_weight, unit, plate_inc):
    if target_weight <= 20: return []
    bar = 20 if unit == "KG" else 45
    if target_weight <= bar + 5: return [f"Empty Bar: 2x5 @ {bar} {unit}"]
    steps = [(0, "Empty Bar", 2, 5), (0.4, "40%", 1, 5), (0.6, "60%", 1, 3), (0.8, "80%", 1, 2), (0.9, "90%", 1, 1)]
    lines = []
    for pct, label, sets, reps in steps:
        w = bar if pct == 0 else max(bar, round_to_plates(target_weight * pct, plate_inc))
        if w < target_weight:
            lines.append(f"{label}: {sets}x{reps} @ **{format_weight(w)}** {unit}")
    return lines

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
    if st.button("Wipe All Data", type="primary", use_container_width=True):
        st.session_state.cycles = []
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()

# --- CUSTOM CSS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_color}; color: {text_color}; }}
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{ color: #ff0000 !important; border-bottom-color: #ff0000 !important; }}
    .warmup-text {{ font-size: 0.85rem; color: #888; }}
    .signature-footer {{ text-align: center; color: #555; font-size: 0.8rem; margin-top: 50px; }}
    </style>
    """, unsafe_allow_html=True)

st.title("Texas Method Training Tracker")

# --- NEW CYCLE FORM ---
with st.expander("Create New Cycle", expanded=len(st.session_state.cycles) == 0):
    with st.form("new_cycle_form"):
        c_name = st.text_input("Cycle Name", placeholder="e.g., Spring Strength")
        c_weeks = st.slider("Duration (Weeks)", 1, 16, 8)
        c_bw = st.number_input(f"Initial Bodyweight ({new_unit})", value=180.0 if new_unit == "LBS" else 80.0, step=0.5)
        
        st.write("---")
        def_inc = {"S": 5, "B": 5, "O": 5, "D": 10} if new_unit == "LBS" else {"S": 2.5, "B": 2.5, "O": 2.5, "D": 5}
        col1, col2, col3, col4 = st.columns(4)
        with col1: s_rm, s_inc = st.text_input("Squat 5RM", "225"), st.text_input("Squat Increment", str(def_inc["S"]))
        with col2: b_rm, b_inc = st.text_input("Bench 5RM", "185"), st.text_input("Bench Increment", str(def_inc["B"]))
        with col3: o_rm, o_inc = st.text_input("OHP 5RM", "115"), st.text_input("OHP Increment", str(def_inc["O"]))
        with col4: d_rm, d_inc = st.text_input("Deadlift 5RM", "315"), st.text_input("Deadlift Increment", str(def_inc["D"]))
            
        if st.form_submit_button("Start Cycle", use_container_width=True):
            if not c_name: st.error("Please name your cycle.")
            else:
                st.session_state.cycles.append({
                    "name": c_name, "date": datetime.now().strftime("%Y-%m-%d"), "weeks": int(c_weeks),
                    "success_log": {m: [False]*int(c_weeks) for m in ["Squat", "Bench", "OHP", "Deadlift"]},
                    "failed_week_log": [False] * int(c_weeks),
                    "weight_log": [float(c_bw)] * int(c_weeks),
                    "lifts": {
                        "Squat": {"rm": float(s_rm), "inc": float(s_inc)}, "Bench": {"rm": float(b_rm), "inc": float(b_inc)},
                        "OHP": {"rm": float(o_rm), "inc": float(o_inc)}, "Deadlift": {"rm": float(d_rm), "inc": float(d_inc)}
                    }
                })
                save_data()
                st.rerun()

# --- DISPLAY CYCLES ---
if st.session_state.cycles:
    for idx, cycle in enumerate(reversed(st.session_state.cycles)):
        true_idx = len(st.session_state.cycles) - 1 - idx
        if "failed_week_log" not in cycle: cycle["failed_week_log"] = [False] * cycle["weeks"]

        with st.container(border=True):
            st.subheader(f"Cycle: {cycle['name']}")
            
            tab_main_log, tab_analysis = st.tabs(["Training Log", "Progress Chart"])
            
            with tab_main_log:
                # Determine week titles and auto-focus
                week_titles = []
                last_completed = -1
                for w_i in range(cycle['weeks']):
                    is_completed = any(cycle['success_log'][mv][w_i] for mv in ["Squat", "Bench", "OHP", "Deadlift"]) or cycle['failed_week_log'][w_i]
                    title = f"Week {w_i+1}"
                    if is_completed:
                        title += " ✅"
                        last_completed = w_i
                    week_titles.append(title)
                
                # Active week is the one after the last completed
                focus_index = min(last_completed + 1, cycle['weeks'] - 1)
                
                # Using a session state key for the tabs is tricky in Streamlit, 
                # but we can force the scroll or highlight via info box.
                w_tabs = st.tabs(week_titles)
                
                for w_i in range(cycle['weeks']):
                    counts = {mv: sum(1 for s in cycle['success_log'][mv][:w_i] if s == True) for mv in ["Squat", "Bench", "OHP", "Deadlift"]}
                    
                    with w_tabs[w_i]:
                        if w_i == focus_index: st.info("Current Active Week")
                        if cycle['failed_week_log'][w_i]: st.warning("Note: This week was skipped/failed. No weight was added.")
                            
                        st.write("Bodyweight")
                        new_bw = st.number_input(f"Weight Value", value=cycle['weight_log'][w_i], key=f"bw_{true_idx}_{w_i}", step=0.1, label_visibility="collapsed")
                        if new_bw != cycle['weight_log'][w_i]:
                            cycle['weight_log'][w_i] = new_bw; save_data(); st.rerun()
                        
                        st.divider()
                        is_a = (w_i + 1) % 2 != 0
                        m_pres, w_pres = ("Bench", "OHP") if is_a else ("OHP", "Bench")
                        cols = st.columns(3)
                        days = [
                            ("Monday (Volume)", 0.90, "5x5", ["Squat", m_pres, "Deadlift"]),
                            ("Wednesday (Light)", 0.70, "2x5", ["Squat", w_pres]),
                            ("Friday (Intensity)", 1.00, "1x5", ["Squat", m_pres, "Deadlift"])
                        ]

                        for d_idx, (day_title, pct, rep_scheme, moves) in enumerate(days):
                            with cols[d_idx]:
                                st.markdown(f"**{day_title}**")
                                for mv in moves:
                                    base_5rm = cycle['lifts'][mv]['rm'] + (cycle['lifts'][mv]['inc'] * counts[mv])
                                    work_weight = round_to_plates(base_5rm * pct, plate)
                                    st.info(f"{mv}: {rep_scheme} @ {format_weight(work_weight)} {new_unit} ({int(pct*100)}%)")
                                
                                if "Friday" in day_title:
                                    st.divider()
                                    st.write("Check Success:")
                                    for mv in moves:
                                        val = cycle['success_log'][mv][w_i]
                                        if st.checkbox(f"Completed {mv}", value=val, key=f"s_{true_idx}_{w_i}_{mv}"):
                                            if not val:
                                                cycle['success_log'][mv][w_i] = True
                                                cycle['failed_week_log'][w_i] = False
                                                save_data(); st.rerun()
                                        elif val:
                                            cycle['success_log'][mv][w_i] = False
                                            save_data(); st.rerun()
                                    
                                    if st.button("Mark Week as Failed", key=f"f_{true_idx}_{w_i}", use_container_width=True):
                                        cycle['failed_week_log'][w_i] = True
                                        for mv in ["Squat", "Bench", "OHP", "Deadlift"]: cycle['success_log'][mv][w_i] = False
                                        save_data(); st.rerun()

            with tab_analysis:
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                weeks_axis = [f"W{i+1}" for i in range(cycle['weeks'])]
                for lift, data in cycle['lifts'].items():
                    y, s_c = [], 0
                    for i in range(cycle['weeks']):
                        current_w = round_to_plates(data['rm'] + (data['inc'] * s_c), plate)
                        y.append(current_w)
                        if cycle['success_log'][lift][i]: s_c += 1
                    fig.add_trace(go.Scatter(x=weeks_axis, y=y, name=lift), secondary_y=False)
                
                fig.update_layout(template="plotly_dark" if theme_choice == "Deep Dark" else "plotly_white", height=500)
                st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="signature-footer">By Aydin Ayhan</div>', unsafe_allow_html=True)
else:
    st.info("No active cycles found. Create one above to start tracking.")
