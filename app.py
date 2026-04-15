import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import json
import os
import random

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
                if "week_completed_log" not in cycle:
                    cycle["week_completed_log"] = [False] * cycle["weeks"]
            return cycles, unit
    return [], "KG"

# --- CORE MATH ---
def calculate_1rm(weight, reps):
    if reps == 1: return weight
    return weight / (1.0278 - (0.0278 * reps))

def custom_round_percent(p):
    return int(5 * round(float(p)/5))

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
        save_data(); st.rerun()

    default_plate = 2.5 if new_unit == "LBS" else 1.25
    smallest_plate = st.number_input(f"🔩 Smallest Plate ({new_unit})", value=default_plate, step=0.25)
    
    st.divider()
    if st.button("🚨 Wipe All Data", type="primary", use_container_width=True):
        st.session_state.cycles = []
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()
    
    st.markdown('<div style="text-align: right; color: gray; font-size: 0.7rem; margin-top: 5px;">By Aydın Ayhan</div>', unsafe_allow_html=True)

st.markdown(f"<style>.stApp {{ background-color: {bg_color}; color: {text_color}; }}</style>", unsafe_allow_html=True)
st.title("Texas Method Training Tracker")

# --- CREATE NEW CYCLE ---
u = st.session_state.current_unit
placeholders = [
    "🚀 Road to 200KG Squat", "🦾 Winter Bulk Phase 1", "🔥 Summer Shred 2026", 
    "🧱 Foundation Building", "🦍 Primal Strength", "⚡ Lightning Bolt Cycle",
    "💀 No Pain No Gain", "📈 Progressive Overload", "🏅 Champion Mindset",
    "🛡️ Iron Fortress", "🧨 Explosive Power", "🩸 Blood, Sweat & Iron",
    "🦖 Jurassic Strength", "⚔️ Warrior Mode", "🌋 Vulcan Intensity"
]
random_placeholder = random.choice(placeholders)

with st.expander("👊 Create New Cycle", expanded=len(st.session_state.cycles) == 0):
    with st.form("new_cycle_form"):
        c_name = st.text_input("📝 Cycle Name", placeholder=f"Örn: {random_placeholder}")
        c_weeks = st.slider("⏳ Duration (Weeks)", 1, 16, 8)
        c_bw = st.number_input(f"⚖️ Initial BW ({u})", value=80.0 if u == "KG" else 180.0)
        st.write("---")
        col1, col2, col3, col4 = st.columns(4)
        if u == "LBS": def_inc = "5"; def_inc_d = "10"
        else: def_inc = "2.5"; def_inc_d = "5"
        
        with col1: 
            s_rm = st.text_input(f"🏋️ Squat 5RM ({u})", "100" if u == "KG" else "225")
            s_inc = st.text_input(f"➕ Squat Inc ({u})", def_inc)
        with col2: 
            b_rm = st.text_input(f"💪 Bench 5RM ({u})", "80" if u == "KG" else "185")
            b_inc = st.text_input(f"➕ Bench Inc ({u})", def_inc)
        with col3: 
            o_rm = st.text_input(f"🥥 OHP 5RM ({u})", "50" if u == "KG" else "115")
            o_inc = st.text_input(f"➕ OHP Inc ({u})", def_inc)
        with col4: 
            d_rm = st.text_input(f"⛓️ Deadlift 5RM ({u})", "140" if u == "KG" else "315")
            d_inc = st.text_input(f"➕ Deadlift Inc ({u})", def_inc_d)
        
        if st.form_submit_button("🚀 Start Cycle"):
            if not c_name.strip(): st.error("Name your cycle first!")
            else:
                st.session_state.cycles.append({
                    "name": c_name, "start_date": datetime.now().strftime("%Y-%m-%d"),
                    "weeks": int(c_weeks), "week_completed_log": [False] * int(c_weeks),
                    "success_log": {m: [False]*int(c_weeks) for m in ["Squat", "Bench", "OHP", "Deadlift"]},
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
            h1, h2, h3, h4 = st.columns([0.50, 0.15, 0.15, 0.20])
            h1.markdown(f"### ⚡ {cycle['name']}")
            h1.caption(f"📅 Started: {cycle.get('start_date', 'N/A')}")
            
            # State management for tabs/delete
            prog_key = f"p_{true_idx}"; wgt_key = f"w_{true_idx}"; del_key = f"confirm_del_{true_idx}"
            if prog_key not in st.session_state: st.session_state[prog_key] = False
            if wgt_key not in st.session_state: st.session_state[wgt_key] = True
            if del_key not in st.session_state: st.session_state[del_key] = False

            if h2.button("📊 Progress", key=f"bp_{true_idx}", use_container_width=True):
                st.session_state[prog_key] = not st.session_state[prog_key]; st.session_state[wgt_key] = False; st.rerun()
            if h3.button("🏋️ Weights", key=f"bw_{true_idx}", use_container_width=True):
                st.session_state[wgt_key] = not st.session_state[wgt_key]; st.session_state[prog_key] = False; st.rerun()
            
            # IMPROVED DELETE WITH CONFIRMATION
            if not st.session_state[del_key]:
                if h4.button("🗑️ Delete Cycle", key=f"bd_{true_idx}", use_container_width=True):
                    st.session_state[del_key] = True; st.rerun()
            else:
                c1, c2 = h4.columns(2)
                if c1.button("✅ Yes", key=f"by_{true_idx}", use_container_width=True, type="primary"):
                    st.session_state.cycles.pop(true_idx); save_data(); st.session_state[del_key] = False; st.rerun()
                if c2.button("❌ No", key=f"bn_{true_idx}", use_container_width=True):
                    st.session_state[del_key] = False; st.rerun()

            if st.session_state[wgt_key]:
                st.divider()
                tabs = st.tabs([f"Week {i+1} {'✅' if cycle['week_completed_log'][i] else '🏋️'}" for i in range(cycle['weeks'])])
                for w_i in range(cycle['weeks']):
                    with tabs[w_i]:
                        counts = {m: sum(1 for prev_w in range(w_i) if cycle['success_log'][m][prev_w] and cycle['week_completed_log'][prev_w]) for m in ["Squat", "Bench", "OHP", "Deadlift"]}
                        new_bw = st.number_input("Current BW", value=cycle['weight_log'][w_i], key=f"bw_in_{true_idx}_{w_i}")
                        if new_bw != cycle['weight_log'][w_i]: cycle['weight_log'][w_i] = new_bw; save_data()
                        
                        st.divider()
                        is_a = (w_i + 1) % 2 != 0
                        m_p, w_p = ("Bench", "OHP") if is_a else ("OHP", "Bench")
                        cols = st.columns(3)
                        days = [("📅 Monday (Volume)", 0.90, ["Squat", m_p, "Deadlift"]),
                                ("📅 Wednesday (Light)", 0.70, ["Squat", w_p]),
                                ("📅 Friday (Intensity)", 1.00, ["Squat", m_p, "Deadlift"])]
                        
                        lift_emojis = {"Squat": "🏋️", "Bench": "💪", "OHP": "🥥", "Deadlift": "⛓️"}

                        for d_idx, (title, pct, moves) in enumerate(days):
                            with cols[d_idx]:
                                st.markdown(f"#### {title}")
                                for mv in moves:
                                    cur_5rm = cycle['lifts'][mv]['rm'] + (cycle['lifts'][mv]['inc'] * counts[mv])
                                    cur_1rm = calculate_1rm(cur_5rm, 5)
                                    calc_w = round_to_plates(cur_5rm * pct, smallest_plate)
                                    p_1rm = custom_round_percent((calc_w / cur_1rm) * 100)
                                    p_5rm = custom_round_percent((calc_w / cur_5rm) * 100)
                                    reps = "5x5" if "Monday" in title else ("2x5" if "Wednesday" in title else "1x5")
                                    
                                    with st.container(border=True):
                                        st.markdown(f"**{lift_emojis.get(mv, '')} {mv}**: {reps} @ **{format_weight(calc_w)} {u}**")
                                        st.caption(f"*(%{p_1rm} 1RM / %{p_5rm} 5RM)*")
                                        with st.expander("🔥 Warm-up Sets"):
                                            bar = 45 if u == "LBS" else 20
                                            warmups = [("Bar x 2x5", bar), ("40% x 5", calc_w*0.4), ("60% x 3", calc_w*0.6), ("80% x 2", calc_w*0.8), ("90% x 1", calc_w*0.9)]
                                            for l, v in warmups:
                                                fv = max(bar, round_to_plates(v, smallest_plate))
                                                st.write(f"• {l}: **{format_weight(fv)} {u}**")

                                if "Wednesday" in title:
                                    st.success("🦾 **Pullups**: 3 x Max"); st.success("🏹 **Back Ext**: 5 x 10")
                                if "Friday" in title:
                                    st.write("🏆 **Friday Crush Check:**")
                                    for mv in moves:
                                        chk = st.checkbox(f"Crushed {mv}", value=cycle['success_log'][mv][w_i], key=f"chk_{true_idx}_{w_i}_{mv}")
                                        if chk != cycle['success_log'][mv][w_i]: cycle['success_log'][mv][w_i] = chk; save_data()
                                    st.divider()
                                    if not cycle['week_completed_log'][w_i]:
                                        if st.button("✅ Week Done", key=f"wd_{true_idx}_{w_i}", use_container_width=True, type="primary"):
                                            cycle['week_completed_log'][w_i] = True; save_data(); st.rerun()
                                    else:
                                        st.success("Week Logged!")
                                        if st.button("🔓 Undo", key=f"ud_{true_idx}_{w_i}"): cycle['week_completed_log'][w_i] = False; save_data(); st.rerun()

            if st.session_state[prog_key]:
                st.divider()
                weeks = list(range(1, cycle['weeks'] + 1))
                c1, c2 = st.columns(2)
                with c1:
                    fig = go.Figure()
                    for l, clr in zip(["Squat", "Bench", "OHP", "Deadlift"], ["#FF4B4B", "#1C83E1", "#FFFFFF", "#FFC300"]):
                        y = [cycle['lifts'][l]['rm'] + (cycle['lifts'][l]['inc'] * sum(1 for pw in range(w) if cycle['success_log'][l][pw] and cycle['week_completed_log'][pw])) for w in range(cycle['weeks'])]
                        fig.add_trace(go.Scatter(x=weeks, y=y, name=l, line=dict(color=clr, width=4), mode='lines+markers'))
                    fig.update_layout(title="Lifts Progress", height=450, template="plotly_dark" if theme_choice == "Deep Dark" else "plotly_white")
                    st.plotly_chart(fig, use_container_width=True)
                with c2:
                    fig_bw = go.Figure()
                    fig_bw.add_trace(go.Scatter(x=weeks, y=cycle['weight_log'], name="BW", line=dict(color="#00C49A", width=4), mode='lines+markers'))
                    fig_bw.update_layout(title="Bodyweight Tracker", height=450, template="plotly_dark" if theme_choice == "Deep Dark" else "plotly_white")
                    st.plotly_chart(fig_bw, use_container_width=True)
else:
    st.info("No active cycles. Name one and let's go!")
