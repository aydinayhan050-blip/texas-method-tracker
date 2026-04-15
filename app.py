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
                return data.get("cycles", []), data.get("unit", "KG")
            return data, "KG"
    return [], "KG"

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
    st.header("⚙️ Settings")
    unit_index = 0 if st.session_state.current_unit == "LBS" else 1
    new_unit = st.radio("📏 Unit", ["LBS", "KG"], index=unit_index)
    theme_choice = st.selectbox("🎨 Theme", ["Deep Dark", "Light"])
    
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

    plate = st.number_input(f"🔩 Plate Inc ({new_unit})", value=2.5 if new_unit == "LBS" else 1.25, step=0.25)
    st.divider()
    if st.button("🚨 Wipe All Data", type="primary", use_container_width=True):
        st.session_state.cycles = []
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()

st.markdown(f"<style>.stApp {{ background-color: {bg_color}; color: {text_color}; }}</style>", unsafe_allow_html=True)
st.title("Texas Method Training Tracker")

# --- ATTENTION BANNER ---
st.warning("""
**⚠️ ATTENTION: TRACK YOUR PROGRESS OR STAY WEAK!** If you don't check the boxes in the **Friday Checklist**, the program won't log your success.  
**No check = No weight increase for next week.** Finish your sets, check the box, and keep making gains!
""")

# --- DYNAMIC DEFAULTS ---
if new_unit == "LBS":
    def_inc_s, def_inc_b, def_inc_o, def_inc_d = "5", "5", "5", "10"
else:
    def_inc_s, def_inc_b, def_inc_o, def_inc_d = "2.5", "2.5", "2.5", "5"

# --- CREATE NEW CYCLE ---
with st.expander("👊 Create New Cycle", expanded=len(st.session_state.cycles) == 0):
    with st.form("new_cycle_form"):
        c_name = st.text_input("📝 Cycle Name", placeholder="e.g. Winter Bulk")
        c_weeks = st.slider("⏳ Duration (Weeks)", 1, 16, 8)
        c_bw = st.number_input(f"⚖️ Initial BW ({new_unit})", value=180.0 if new_unit == "LBS" else 80.0)
        st.write("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1: 
            s_rm = st.text_input(f"🏋️ Squat 5RM ({new_unit})", "225" if new_unit == "LBS" else "100")
            s_inc = st.text_input(f"➕ Squat Inc ({new_unit})", def_inc_s)
        with col2: 
            b_rm = st.text_input(f"💪 Bench 5RM ({new_unit})", "185" if new_unit == "LBS" else "80")
            b_inc = st.text_input(f"➕ Bench Inc ({new_unit})", def_inc_b)
        with col3: 
            o_rm = st.text_input(f"🥥 OHP 5RM ({new_unit})", "115" if new_unit == "LBS" else "50")
            o_inc = st.text_input(f"➕ OHP Inc ({new_unit})", def_inc_o)
        with col4: 
            d_rm = st.text_input(f"🔥 Deadlift 5RM ({new_unit})", "315" if new_unit == "LBS" else "140")
            d_inc = st.text_input(f"➕ Deadlift Inc ({new_unit})", def_inc_d)
        
        if st.form_submit_button("🚀 Start Cycle"):
            if not c_name.strip():
                st.error("Yo! Name your cycle before you start!")
            else:
                st.session_state.cycles.append({
                    "name": c_name, 
                    "start_date": datetime.now().strftime("%Y-%m-%d"),
                    "weeks": int(c_weeks),
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
            head1, head2 = st.columns([0.85, 0.15])
            head1.subheader(f"⚡ {cycle['name']}")
            # Date moved under the name
            start_val = cycle.get("start_date", datetime.now().strftime("%Y-%m-%d"))
            head1.markdown(f"*Started on: {start_val}*")
            
            confirm_key = f"del_confirm_{true_idx}"
            if confirm_key not in st.session_state: st.session_state[confirm_key] = False
            
            if not st.session_state[confirm_key]:
                if head2.button("🗑️ Delete", key=f"del_btn_{true_idx}"):
                    st.session_state[confirm_key] = True; st.rerun()
            else:
                head2.warning("You sure?")
                c1, c2 = head2.columns(2)
                if c1.button("✅", key=f"y_{true_idx}"):
                    st.session_state.cycles.pop(true_idx)
                    st.session_state[confirm_key] = False; save_data(); st.rerun()
                if c2.button("❌", key=f"n_{true_idx}"):
                    st.session_state[confirm_key] = False; st.rerun()

            week_titles = [f"W{w_i+1} {'✅' if (any(cycle['success_log'][m][w_i] for m in ['Squat','Bench','OHP','Deadlift']) or cycle['failed_week_log'][w_i]) else '🏋️'}" for w_i in range(cycle['weeks'])]
            w_tabs = st.tabs(week_titles)
            
            for w_i in range(cycle['weeks']):
                with w_tabs[w_i]:
                    counts = {m: sum(1 for s in cycle['success_log'][m][:w_i] if s) for m in ["Squat", "Bench", "OHP", "Deadlift"]}
                    if cycle['failed_week_log'][w_i]: st.warning("⚠️ This week was marked as a FAIL.")

                    st.write("⚖️ **Bodyweight**")
                    new_bw = st.number_input("BW", value=cycle['weight_log'][w_i], key=f"bw_{true_idx}_{w_i}", label_visibility="collapsed")
                    if new_bw != cycle['weight_log'][w_i]:
                        cycle['weight_log'][w_i] = new_bw; save_data(); st.rerun()

                    st.divider()
                    is_a = (w_i + 1) % 2 != 0
                    m_p, w_p = ("Bench", "OHP") if is_a else ("OHP", "Bench")
                    cols = st.columns(3)
                    lift_ems = {"Squat": "🏋️ Squat", "Bench": "💪 Bench", "OHP": "🥥 OHP", "Deadlift": "🔥 Deadlift"}
                    days = [("📅 Monday (Volume)", 0.90, "5x5", ["Squat", m_p, "Deadlift"]),
                            ("📅 Wednesday (Light)", 0.70, "2x5", ["Squat", w_p]),
                            ("📅 Friday (Intensity)", 1.00, "1x5", ["Squat", m_p, "Deadlift"])]

                    for d_idx, (d_title, pct, reps, moves) in enumerate(days):
                        with cols[d_idx]:
                            st.markdown(f"#### {d_title}")
                            for mv in moves:
                                wgt = round_to_plates((cycle['lifts'][mv]['rm'] + (cycle['lifts'][mv]['inc'] * counts[mv])) * pct, plate)
                                st.info(f"**{lift_ems.get(mv, mv)}**: {reps} @ **{format_weight(wgt)} {new_unit}**")
                            
                            if "Wednesday" in d_title:
                                st.success("🦾 **Pullups**: 3 Sets x Max Reps")
                                st.success("🏹 **Back Extensions**: 5 Sets x 10 Reps")

                            if "Friday" in d_title:
                                st.divider()
                                st.write("🏆 **Friday Checklist:**")
                                for mv in moves:
                                    val = cycle['success_log'][mv][w_i]
                                    if st.checkbox(f"Crushed {mv}", value=val, key=f"c_{true_idx}_{w_i}_{mv}"):
                                        if not val:
                                            cycle['success_log'][mv][w_i] = True
                                            cycle['failed_week_log'][w_i] = False
                                            save_data(); st.rerun()
                                    elif val:
                                        cycle['success_log'][mv][w_i] = False; save_data(); st.rerun()
                                
                                if st.button("💀 Mark Week as Failed", key=f"f_{true_idx}_{w_i}", use_container_width=True):
                                    cycle['failed_week_log'][w_i] = True
                                    for m in ["Squat", "Bench", "OHP", "Deadlift"]: cycle['success_log'][m][w_i] = False
                                    save_data(); st.rerun()

    st.markdown('<div style="text-align: center; color: #555; font-size: 0.8rem; margin-top: 50px;">By Aydin Ayhan</div>', unsafe_allow_html=True)
else:
    st.info("👋 No active cycles. Fill out the form above to get after it!")
