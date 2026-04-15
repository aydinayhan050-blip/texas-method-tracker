import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import json
import os
import time

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
            cycles = data.get("cycles", [])
            unit = data.get("unit", "KG")
            for cycle in cycles:
                if "week_completed_log" not in cycle: cycle["week_completed_log"] = [False] * cycle["weeks"]
                if "day_completed_log" not in cycle: cycle["day_completed_log"] = {}
                if "weight_log" not in cycle: cycle["weight_log"] = [80.0] * cycle["weeks"]
                if "success_log" not in cycle: cycle["success_log"] = {m: [False]*cycle["weeks"] for m in ["Squat", "Bench", "OHP", "Deadlift", "Power Clean"]}
                if "Power Clean" not in cycle["success_log"]: cycle["success_log"]["Power Clean"] = [False]*cycle["weeks"]
                if "variant" not in cycle: cycle["variant"] = "Modern (Deadlift Focus)"
                if "start_date" not in cycle: cycle["start_date"] = datetime.now().strftime("%Y-%m-%d")
            return cycles, unit
    return [], "KG"

# --- CORE MATH & UTILS ---
def format_weight(weight):
    val = round(float(weight), 2)
    return f"{int(val)}" if val % 1 == 0 else f"{val}"

def round_to_plates(weight, smallest_plate):
    step = smallest_plate * 2
    if step <= 0: return weight
    return round(weight / step) * step

def convert_weight(val, to_unit):
    if to_unit == "LBS": return val * 2.20462
    return val / 2.20462

# --- UI CONFIG ---
st.set_page_config(page_title="Texas Method Tracker", layout="wide")

st.markdown("""
    <script>
    function notifyEnd() {
        if (navigator.vibrate) { navigator.vibrate(500); }
        var context = new (window.AudioContext || window.webkitAudioContext)();
        var osc = context.createOscillator();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(440, context.currentTime);
        osc.connect(context.destination);
        osc.start();
        osc.stop(context.currentTime + 0.5);
    }
    </script>
    <style>
    div[data-testid="stStatusWidget"] { display: none !important; }
    * { opacity: 1 !important; filter: none !important; }
    .big-timer {
        font-size: 110px !important;
        font-weight: 900;
        text-align: center;
        color: #FF4B4B;
        margin: 0px;
        line-height: 1;
        font-family: 'Courier New', Courier, monospace;
    }
    .ready-text {
        font-size: 75px !important;
        color: #28a745;
        font-weight: 900;
        text-align: center;
    }
    .start-date-text {
        font-size: 0.85em;
        opacity: 0.6;
        margin-top: -15px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

if 'cycles' not in st.session_state:
    cycles, saved_unit = load_data()
    st.session_state.cycles = cycles
    st.session_state.current_unit = saved_unit

if 'timer_paused' not in st.session_state:
    st.session_state.timer_paused = False

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    unit_index = 0 if st.session_state.current_unit == "LBS" else 1
    new_unit = st.radio("📏 Unit", ["LBS", "KG"], index=unit_index)
    theme_choice = st.selectbox("🎨 Theme", ["Deep Dark", "Light"])
    bg_color = "#0e1117" if theme_choice == "Deep Dark" else "#ffffff"

    if new_unit != st.session_state.current_unit:
        for cycle in st.session_state.cycles:
            for lift in cycle['lifts']:
                cycle['lifts'][lift]['rm'] = convert_weight(cycle['lifts'][lift]['rm'], new_unit)
                cycle['lifts'][lift]['inc'] = convert_weight(cycle['lifts'][lift]['inc'], new_unit)
            cycle['weight_log'] = [convert_weight(w, new_unit) for w in cycle['weight_log']]
        st.session_state.current_unit = new_unit
        save_data(); st.rerun()

    smallest_plate = st.number_input(f"🔩 Smallest Plate ({new_unit})", value=2.5 if new_unit == "LBS" else 1.25, step=0.25)
    
    st.divider()
    if st.button("🚨 Wipe All Data", type="primary", use_container_width=True):
        st.session_state.cycles = []
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()
    
    st.markdown("<div style='text-align: center; opacity: 0.5; font-size: 0.8em; margin-top: 10px;'>by Aydin Ayhan</div>", unsafe_allow_html=True)

st.markdown(f"<style>.stApp {{ background-color: {bg_color}; }}</style>", unsafe_allow_html=True)
st.title("Texas Method Training Tracker")

# --- CREATE CYCLE ---
u = st.session_state.current_unit
def_inc = ["5", "5", "5", "10", "5"] if u == "LBS" else ["2.5", "2.5", "2.5", "5", "2.5"]

with st.expander("👊 Create New Cycle", expanded=len(st.session_state.cycles) == 0):
    if 'temp_variant' not in st.session_state:
        st.session_state.temp_variant = "Modern (Deadlift Focus)"
    
    variant_choice = st.radio("🏋️ Select Method Variant", 
                             ["Modern (Deadlift Focus)", "Standard (Power Clean)"], 
                             index=0 if st.session_state.temp_variant == "Modern (Deadlift Focus)" else 1)
    st.session_state.temp_variant = variant_choice
    
    with st.form("new_cycle_form", clear_on_submit=True):
        c_name = st.text_input("📝 Cycle Name", placeholder="e.g. Strength Phase 1")
        c_weeks = st.slider("⏳ Duration (Weeks)", 1, 16, 8)
        c_bw = st.number_input(f"⚖️ Initial BW ({u})", value=80.0 if u == "KG" else 180.0)
        st.write("---")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1: s_rm, s_inc = st.text_input(f"🏋️ Squat 5RM", "100"), st.text_input(f"➕ Squat Inc", def_inc[0])
        with col2: b_rm, b_inc = st.text_input(f"💪 Bench 5RM", "80"), st.text_input(f"➕ Bench Inc", def_inc[1])
        with col3: o_rm, o_inc = st.text_input(f"🥥 OHP 5RM", "50"), st.text_input(f"➕ OHP Inc", def_inc[2])
        with col4: d_rm, d_inc = st.text_input(f"🔥 Deadlift 5RM", "140"), st.text_input(f"➕ Deadlift Inc", def_inc[3])
        
        pc_rm, pc_inc = "60", def_inc[4]
        with col5: 
            if st.session_state.temp_variant == "Standard (Power Clean)":
                pc_rm = st.text_input(f"⚡ Power Clean 3RM", "60")
                pc_inc = st.text_input(f"➕ Power Clean Inc", def_inc[4])
            else:
                st.write("Power Clean Disabled")

        submit = st.form_submit_button("🚀 Start Cycle")
        if submit:
            if not c_name.strip(): st.error("⚠️ Please enter a name!")
            else:
                st.session_state.cycles.append({
                    "name": c_name, "variant": st.session_state.temp_variant, "start_date": datetime.now().strftime("%Y-%m-%d"), "weeks": int(c_weeks),
                    "success_log": {m: [False]*int(c_weeks) for m in ["Squat", "Bench", "OHP", "Deadlift", "Power Clean"]},
                    "week_completed_log": [False] * int(c_weeks), "day_completed_log": {}, "weight_log": [float(c_bw)] * int(c_weeks),
                    "lifts": {"Squat": {"rm": float(s_rm), "inc": float(s_inc)}, "Bench": {"rm": float(b_rm), "inc": float(b_inc)},
                              "OHP": {"rm": float(o_rm), "inc": float(o_inc)}, "Deadlift": {"rm": float(d_rm), "inc": float(d_inc)},
                              "Power Clean": {"rm": float(pc_rm), "inc": float(pc_inc)}}
                })
                save_data(); st.rerun()

# --- DISPLAY ---
if st.session_state.cycles:
    for idx, cycle in enumerate(reversed(st.session_state.cycles)):
        t_idx = len(st.session_state.cycles) - 1 - idx
        with st.container(border=True):
            h1, h2, h3, h4 = st.columns([0.55, 0.15, 0.15, 0.15])
            with h1:
                st.markdown(f"### ⚡ {cycle['name']}")
                st.markdown(f"<p class='start-date-text'>Started: {cycle.get('start_date', 'N/A')}</p>", unsafe_allow_html=True)
            
            p_key, w_key = f"p_{t_idx}", f"w_{t_idx}"
            if p_key not in st.session_state: st.session_state[p_key] = False
            if w_key not in st.session_state: st.session_state[w_key] = True

            if h2.button("📊 Progress", key=f"bp_{t_idx}", use_container_width=True):
                st.session_state[p_key] = not st.session_state[p_key]; st.session_state[w_key] = False; st.rerun()
            if h3.button("🏋️ Weights", key=f"bw_{t_idx}", use_container_width=True):
                st.session_state[w_key] = not st.session_state[w_key]; st.session_state[p_key] = False; st.rerun()
            
            with h4.popover("🗑️ Delete", use_container_width=True):
                if st.button("Yes, delete!", key=f"conf_del_{t_idx}", type="primary", use_container_width=True):
                    st.session_state.cycles.pop(t_idx); save_data(); st.rerun()

            if st.session_state[w_key]:
                tabs = st.tabs([f"Week {i+1} {'✅' if cycle['week_completed_log'][i] else ''}" for i in range(cycle['weeks'])])
                for w_i in range(cycle['weeks']):
                    with tabs[w_i]:
                        t_col1, t_col2 = st.columns([0.3, 0.7])
                        with t_col1: 
                            rest_choice = st.slider("⏱️ Rest (min)", 1, 10, 3, key=f"rs_{t_idx}_{w_i}")
                            if st.button("⏸️ Pause / ▶️ Resume", key=f"pause_{t_idx}_{w_i}", use_container_width=True):
                                st.session_state.timer_paused = not st.session_state.timer_paused
                        with t_col2:
                            timer_place = st.empty()
                            timer_place.markdown('<p class="big-timer">00:00</p>', unsafe_allow_html=True)
                        
                        cycle['weight_log'][w_i] = st.number_input(f"BW ({u})", value=cycle['weight_log'][w_i], key=f"bw_in_{t_idx}_{w_i}")
                        st.divider()

                        counts = {m: sum(1 for prev in range(w_i) if cycle['success_log'][m][prev]) for m in ["Squat", "Bench", "OHP", "Deadlift", "Power Clean"]}
                        is_a = (w_i + 1) % 2 != 0
                        m_p, w_p = ("Bench", "OHP") if is_a else ("OHP", "Bench")
                        
                        monday_pull = "Power Clean" if cycle.get("variant") == "Standard (Power Clean)" else "Deadlift"
                        
                        days = [("Monday (Volume)", 0.90, ["Squat", m_p, monday_pull]),
                                ("Wednesday (Light)", 0.80, ["Squat", w_p, "Chin-ups", "Back Extensions"]),
                                ("Friday (Intensity)", 1.00, ["Squat", m_p, "Deadlift"])]
                        
                        lift_emojis = {"Squat": "🏋️", "Bench": "💪", "OHP": "🥥", "Deadlift": "⛓️", "Power Clean": "⚡", "Chin-ups": "🐒", "Back Extensions": "🦒"}

                        for d_name, pct, moves in days:
                            d_key = f"cycle{t_idx}_w{w_i}_{d_name}"
                            is_done = cycle['day_completed_log'].get(d_key, False)
                            
                            with st.expander(f"### 📅 {d_name} {'✅' if is_done else ''}"):
                                lift_cols = st.columns(len(moves))
                                for m_idx, mv in enumerate(moves):
                                    with lift_cols[m_idx]:
                                        is_accessory = mv in ["Chin-ups", "Back Extensions"]
                                        if not is_accessory:
                                            c_rm = cycle['lifts'][mv]['rm'] + (cycle['lifts'][mv]['inc'] * counts[mv])
                                            calc_w = round_to_plates(c_rm * pct, smallest_plate)
                                            set_count = 3 if mv == "Power Clean" else (5 if "Monday" in d_name else (2 if "Wednesday" in d_name else 1))
                                            rep_count = 3 if mv == "Power Clean" else 5
                                            rm_label = "3RM" if mv == "Power Clean" else "5RM"
                                        
                                        with st.container(border=True):
                                            st.markdown(f"**{lift_emojis.get(mv, '')} {mv}**")
                                            if not is_accessory:
                                                st.markdown(f"#### {set_count}x{rep_count} @ {format_weight(calc_w)} {u}")
                                                st.caption(f"({int(pct*100)}% of {rm_label})")

                                                for s_i in range(set_count):
                                                    cb_key = f"ck_{t_idx}_{w_i}_{d_name}_{mv}_{s_i}"
                                                    prev_state_key = f"prev_{cb_key}"
                                                    if prev_state_key not in st.session_state: st.session_state[prev_state_key] = False
                                                    if st.checkbox(f"Set {s_i+1}", key=cb_key) and not st.session_state[prev_state_key]:
                                                        st.session_state[prev_state_key] = True
                                                        st.session_state.timer_paused = False
                                                        s = rest_choice * 60
                                                        while s >= 0:
                                                            if not st.session_state.timer_paused:
                                                                m, sc = divmod(s, 60)
                                                                timer_place.markdown(f'<p class="big-timer">{m:02d}:{sc:02d}</p>', unsafe_allow_html=True)
                                                                time.sleep(1)
                                                                s -= 1
                                                            else:
                                                                time.sleep(0.5)

                                                        st.components.v1.html("<script>window.parent.notifyEnd();</script>", height=0)
                                                        timer_place.markdown('<p class="ready-text">READY! 🔥</p>', unsafe_allow_html=True)

                                if "Monday" in d_name and cycle.get("variant") == "Standard (Power Clean)":
                                    pc_key = f"pc_success_{t_idx}_{w_i}"
                                    new_val = st.checkbox(
                                        "⚡ Crushed Power Clean",
                                        value=cycle['success_log']["Power Clean"][w_i],
                                        key=pc_key
                                    )
                                    if new_val != cycle['success_log']["Power Clean"][w_i]:
                                        cycle['success_log']["Power Clean"][w_i] = new_val
                                        save_data()
