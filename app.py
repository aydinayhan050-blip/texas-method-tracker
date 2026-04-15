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

st.markdown(f"<style>.stApp {{ background-color: {bg_color}; color: {text_color}; }}</style>", unsafe_allow_html=True)
st.title("Texas Method Training Tracker")

# --- CREATE NEW CYCLE ---
u = st.session_state.current_unit
if u == "LBS":
    def_inc_s, def_inc_b, def_inc_o, def_inc_d = "5", "5", "5", "10"
else:
    def_inc_s, def_inc_b, def_inc_o, def_inc_d = "2.5", "2.5", "2.5", "5"

with st.expander("👊 Create New Cycle", expanded=len(st.session_state.cycles) == 0):
    with st.form("new_cycle_form"):
        c_name = st.text_input("📝 Cycle Name", placeholder="e.g. Strength Phase 1")
        c_weeks = st.slider("⏳ Duration (Weeks)", 1, 16, 8)
        c_bw = st.number_input(f"⚖️ Initial BW ({u})", value=80.0 if u == "KG" else 180.0)
        st.write("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1: 
            s_rm = st.text_input(f"🏋️ Squat 5RM ({u})", "100" if u == "KG" else "225")
            s_inc = st.text_input(f"➕ Squat Inc ({u})", def_inc_s)
        with col2: 
            b_rm = st.text_input(f"💪 Bench 5RM ({u})", "80" if u == "KG" else "185")
            b_inc = st.text_input(f"➕ Bench Inc ({u})", def_inc_b)
        with col3: 
            o_rm = st.text_input(f"🥥 OHP 5RM ({u})", "50" if u == "KG" else "115")
            o_inc = st.text_input(f"➕ OHP Inc ({u})", def_inc_o)
        with col4: 
            d_rm = st.text_input(f"🔥 Deadlift 5RM ({u})", "140" if u == "KG" else "315")
            d_inc = st.text_input(f"➕ Deadlift Inc ({u})", def_inc_d)
        
        if st.form_submit_button("🚀 Start Cycle"):
            if not c_name.strip():
                st.error("Name your cycle first!")
            else:
                st.session_state.cycles.append({
                    "name": c_name, 
                    "start_date": datetime.now().strftime("%Y-%m-%d"),
                    "weeks": int(c_weeks),
                    "success_log": {m: [False]*int(c_weeks) for m in ["Squat", "Bench", "OHP", "Deadlift"]},
                    "week_completed_log": [False] * int(c_weeks),
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
            h1, h2, h3, h4 = st.columns([0.55, 0.15, 0.15, 0.15])
            h1.markdown(f"### ⚡ {cycle['name']}")
            h1.caption(f"📅 Started on: {cycle.get('start_date', 'N/A')}")
            
            prog_key = f"p_{true_idx}"
            wgt_key = f"w_{true_idx}"
            if prog_key not in st.session_state: st.session_state[prog_key] = False
            if wgt_key not in st.session_state: st.session_state[wgt_key] = True

            if h2.button("📊 Progress", key=f"bp_{true_idx}", use_container_width=True):
                st.session_state[prog_key] = not st.session_state[prog_key]; st.session_state[wgt_key] = False; st.rerun()
            if h3.button("🏋️ Weights", key=f"bw_{true_idx}", use_container_width=True):
                st.session_state[wgt_key] = not st.session_state[wgt_key]; st.session_state[prog_key] = False; st.rerun()
            if h4.button("🗑️ Delete", key=f"bd_{true_idx}", use_container_width=True):
                st.session_state.cycles.pop(true_idx); save_data(); st.rerun()

            if st.session_state[wgt_key]:
                st.divider()
                tabs = st.tabs([f"Week {i+1} {'✅' if cycle['week_completed_log'][i] else '🏋️'}" for i in range(cycle['weeks'])])
                
                for w_i in range(cycle['weeks']):
                    with tabs[w_i]:
                        # --- TOP TIMER BAR ---
                        t_col1, t_col2 = st.columns([0.3, 0.7])
                        with t_col1:
                            rest_choice = st.slider("⏱️ Rest Duration (min)", 1, 10, 3, key=f"rest_sl_{true_idx}_{w_i}")
                        with t_col2:
                            timer_place = st.empty()
                            timer_place.info("Kutucuğu işaretle, geri sayım başlasın! 🚀")

                        counts = {m: sum(1 for prev_w in range(w_i) if cycle['success_log'][m][prev_w] and cycle['week_completed_log'][prev_w]) for m in ["Squat", "Bench", "OHP", "Deadlift"]}
                        new_bw = st.number_input("Current Bodyweight", value=cycle['weight_log'][w_i], key=f"bw_in_{true_idx}_{w_i}")
                        if new_bw != cycle['weight_log'][w_i]:
                            cycle['weight_log'][w_i] = new_bw; save_data()

                        st.divider()
                        is_a = (w_i + 1) % 2 != 0
                        m_p, w_p = ("Bench", "OHP") if is_a else ("OHP", "Bench")
                        
                        days = [("📅 Monday (Volume)", 0.90, ["Squat", m_p, "Deadlift"]),
                                ("📅 Wednesday (Light)", 0.70, ["Squat", w_p]),
                                ("📅 Friday (Intensity)", 1.00, ["Squat", m_p, "Deadlift"])]

                        lift_emojis = {"Squat": "🏋️", "Bench": "💪", "OHP": "🥥", "Deadlift": "⛓️"}

                        for d_idx, (title, pct, moves) in enumerate(days):
                            with st.expander(f"### {title}", expanded=False):
                                lift_cols = st.columns(len(moves))
                                for m_idx, mv in enumerate(moves):
                                    with lift_cols[m_idx]:
                                        current_5rm = cycle['lifts'][mv]['rm'] + (cycle['lifts'][mv]['inc'] * counts[mv])
                                        current_1rm = calculate_1rm(current_5rm, 5)
                                        calc_w = round_to_plates(current_5rm * pct, smallest_plate)
                                        
                                        set_count = 5 if "Monday" in title else (2 if "Wednesday" in title else 1)
                                        
                                        with st.container(border=True):
                                            st.markdown(f"**{lift_emojis.get(mv, '')} {mv}**")
                                            st.markdown(f"#### {set_count}x5 @ {format_weight(calc_w)} {u}")
                                            
                                            st.write("Sets Tracker:")
                                            set_grid = st.columns(set_count)
                                            for s_i in range(set_count):
                                                with set_grid[s_i]:
                                                    if st.checkbox(f"S{s_i+1}", key=f"chk_{true_idx}_{w_i}_{title}_{mv}_{s_i}"):
                                                        total_sec = rest_choice * 60
                                                        for sec in range(total_sec, -1, -1):
                                                            timer_place.error(f"⏱️ REST: {sec//60:02d}:{sec%60:02d} - {mv} S{s_i+1} bitti!")
                                                            time.sleep(1)
                                                        timer_place.success("🔥 SET BAŞLASIN! HAYDİ KNK!")
                                                        st.balloons()

                                            with st.expander("🔥 Warm-up"):
                                                bar_w = 45 if u == "LBS" else 20
                                                warmups = [(f"Bar x 2x5", bar_w), (f"40% x 5", calc_w * 0.40), (f"60% x 3", calc_w * 0.60), (f"80% x 2", calc_w * 0.80), (f"90% x 1", calc_w * 0.90)]
                                                for label, val in warmups:
                                                    final_v = max(bar_w, round_to_plates(val, smallest_plate))
                                                    st.write(f"• {label}: **{format_weight(final_v)}**")

                                if "Wednesday" in title:
                                    st.info("🦾 **Pullups**: 3 x Max | 🏹 **Back Extensions**: 5 x 10")

                                if "Friday" in title:
                                    st.divider()
                                    st.subheader("🏆 Friday Crush Check")
                                    st.caption("⚠️ **ÖNEMLİ:** Eğer bu hareketi başarıyla tamamlayamazsan (Fail), kutuyu boş bırak. Bu durumda haftaya ağırlık artışı olmayacaktır!")
                                    
                                    check_cols = st.columns(len(moves))
                                    for m_idx, mv in enumerate(moves):
                                        with check_cols[m_idx]:
                                            is_success = cycle['success_log'][mv][w_i]
                                            chk = st.checkbox(f"Crushed {mv}", value=is_success, key=f"chk_f_{true_idx}_{w_i}_{mv}")
                                            
                                            if chk:
                                                st.success(f"🔥 {mv} Gelişiyor!")
                                            else:
                                                st.warning(f"❌ {mv} Fail (Ağırlık sabit)")
                                                
                                            if chk != cycle['success_log'][mv][w_i]:
                                                cycle['success_log'][mv][w_i] = chk
                                                save_data()
                                    
                                    st.divider()
                                    if not cycle['week_completed_log'][w_i]:
                                        if st.button("✅ Finish Week", key=f"wd_{true_idx}_{w_i}", use_container_width=True, type="primary"):
                                            cycle['week_completed_log'][w_i] = True
                                            save_data(); st.rerun()
                                    else:
                                        st.success("Week Logged!")
                                        if st.button("🔓 Undo", key=f"ud_{true_idx}_{w_i}"):
                                            cycle['week_completed_log'][w_i] = False
                                            save_data(); st.rerun()

            if st.session_state[prog_key]:
                st.divider()
                weeks_range = list(range(1, cycle['weeks'] + 1))
                c1, c2 = st.columns(2)
                with c1:
                    fig_w = go.Figure()
                    for lift, color in zip(["Squat", "Value", "Bench", "OHP", "Deadlift"], ["#FF4B4B", "#1C83E1", "#FFFFFF", "#FFC300"]):
                        if lift not in cycle['lifts'] and lift != "Value": continue
                        y_vals = []
                        for w in range(cycle['weeks']):
                            c = sum(1 for prev_w in range(w) if cycle['success_log'].get(lift, [False]*20)[prev_w] and cycle['week_completed_log'][prev_w])
                            y_vals.append(cycle['lifts'].get(lift, {'rm':0})['rm'] + (cycle['lifts'].get(lift, {'inc':0})['inc'] * c))
                        fig_w.add_trace(go.Scatter(x=weeks_range, y=y_vals, name=lift, line=dict(color=color, width=4), mode='lines+markers'))
                    fig_w.update_layout(title="Lifts Progress", height=450, template="plotly_dark" if theme_choice == "Deep Dark" else "plotly_white")
                    st.plotly_chart(fig_w, use_container_width=True)
                with c2:
                    fig_p = go.Figure()
                    fig_p.add_trace(go.Scatter(x=weeks_range, y=cycle['weight_log'], name="BW", line=dict(color="#00C49A", width=4), mode='lines+markers'))
                    fig_p.update_layout(title="Bodyweight Tracker", height=450, template="plotly_dark" if theme_choice == "Deep Dark" else "plotly_white")
                    st.plotly_chart(fig_p, use_container_width=True)
else:
    st.info("No active cycles. Name one and let's go!")
