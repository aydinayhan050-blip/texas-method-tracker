import streamlit as st
import plotly.graph_objects as go
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

# --- UI CONFIG ---
st.set_page_config(page_title="Texas Method Tracker", layout="wide")

if 'cycles' not in st.session_state:
    cycles, saved_unit = load_data()
    st.session_state.cycles = cycles
    st.session_state.current_unit = saved_unit

def format_weight(weight):
    val = round(float(weight), 2)
    return f"{int(val)}" if val % 1 == 0 else f"{val}"

def round_to_plates(weight, smallest_unit):
    step = smallest_unit * 2
    return round(weight / step) * step

def convert_weight(val, to_unit):
    if to_unit == "LBS": return val * 2.20462
    return val / 2.20462

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

    plate = st.number_input(f"🔩 Plate Inc ({new_unit})", value=2.5 if new_unit == "LBS" else 1.25, step=0.25)
    st.divider()
    if st.button("🚨 Wipe All Data", type="primary", use_container_width=True):
        st.session_state.cycles = []
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()
    
    st.markdown('<div style="text-align: right; color: gray; font-size: 0.7rem; margin-top: 5px;">By Aydin Ayhan</div>', unsafe_allow_html=True)

st.markdown(f"<style>.stApp {{ background-color: {bg_color}; color: {text_color}; }}</style>", unsafe_allow_html=True)
st.title("Texas Method Training Tracker")

# --- CREATE NEW CYCLE ---
if new_unit == "LBS":
    def_inc_s, def_inc_b, def_inc_o, def_inc_d = "5", "5", "5", "10"
else:
    def_inc_s, def_inc_b, def_inc_o, def_inc_d = "2.5", "2.5", "2.5", "5"

with st.expander("👊 Create New Cycle", expanded=len(st.session_state.cycles) == 0):
    with st.form("new_cycle_form"):
        c_name = st.text_input("📝 Cycle Name", placeholder="e.g. Winter Bulk")
        c_weeks = st.slider("⏳ Duration (Weeks)", 1, 16, 8)
        c_bw = st.number_input(f"⚖️ Initial BW ({new_unit})", value=80.0 if new_unit == "KG" else 180.0)
        st.write("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1: 
            s_rm = st.text_input(f"🏋️ Squat 5RM", "100" if new_unit == "KG" else "225")
            s_inc = st.text_input(f"➕ Squat Inc", def_inc_s)
        with col2: 
            b_rm = st.text_input(f"💪 Bench 5RM", "80" if new_unit == "KG" else "185")
            b_inc = st.text_input(f"➕ Bench Inc", def_inc_b)
        with col3: 
            o_rm = st.text_input(f"🥥 OHP 5RM", "50" if new_unit == "KG" else "115")
            o_inc = st.text_input(f"➕ OHP Inc", def_inc_o)
        with col4: 
            d_rm = st.text_input(f"🔥 Deadlift 5RM", "140" if new_unit == "KG" else "315")
            d_inc = st.text_input(f"➕ Deadlift Inc", def_inc_d)
        
        if st.form_submit_button("🚀 Start Cycle"):
            st.session_state.cycles.append({
                "name": c_name, 
                "start_date": datetime.now().strftime("%Y-%m-%d"),
                "weeks": int(c_weeks),
                "success_log": {m: [False]*int(c_weeks) for m in ["Squat", "Bench", "OHP", "Deadlift"]},
                "week_completed_log": [False] * int(c_weeks),
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
            h1, h2, h3, h4 = st.columns([0.55, 0.15, 0.15, 0.15])
            h1.subheader(f"⚡ {cycle['name']}")
            
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

            # --- LOGGING SECTION ---
            if st.session_state[wgt_key]:
                st.divider()
                tabs = st.tabs([f"Week {i+1} {'✅' if cycle['week_completed_log'][i] else '🏋️'}" for i in range(cycle['weeks'])])
                
                for w_i in range(cycle['weeks']):
                    with tabs[w_i]:
                        # Ağırlık hesaplama: Sadece "Week Completed" olmuş VE "Success" işaretlenmiş haftalar artış sağlar
                        counts = {}
                        for m in ["Squat", "Bench", "OHP", "Deadlift"]:
                            # Geçmiş haftalarda hem 'success' olan hem de 'week_completed' butonuna basılmış olanları say
                            counts[m] = sum(1 for prev_w in range(w_i) if cycle['success_log'][m][prev_w] and cycle['week_completed_log'][prev_w])

                        new_bw = st.number_input("Current Bodyweight", value=cycle['weight_log'][w_i], key=f"bw_in_{true_idx}_{w_i}")
                        if new_bw != cycle['weight_log'][w_i]:
                            cycle['weight_log'][w_i] = new_bw; save_data()

                        st.divider()
                        is_a = (w_i + 1) % 2 != 0
                        m_p, w_p = ("Bench", "OHP") if is_a else ("OHP", "Bench")
                        cols = st.columns(3)
                        days = [("📅 Monday", 0.90, "5x5", ["Squat", m_p, "Deadlift"]),
                                ("📅 Wednesday", 0.70, "2x5", ["Squat", w_p]),
                                ("📅 Friday", 1.00, "1x5", ["Squat", m_p, "Deadlift"])]

                        for d_idx, (title, pct, reps, moves) in enumerate(days):
                            with cols[d_idx]:
                                st.markdown(f"#### {title}")
                                for mv in moves:
                                    base_w = cycle['lifts'][mv]['rm'] + (cycle['lifts'][mv]['inc'] * counts[mv])
                                    calc_w = round_to_plates(base_w * pct, plate)
                                    st.info(f"**{mv}**: {reps} @ **{format_weight(calc_w)}**")
                                
                                if "Friday" in title:
                                    st.write("🏆 **Friday Crush Check:**")
                                    for mv in moves:
                                        # Success log update
                                        chk = st.checkbox(f"Crushed {mv}", value=cycle['success_log'][mv][w_i], key=f"chk_{true_idx}_{w_i}_{mv}")
                                        if chk != cycle['success_log'][mv][w_i]:
                                            cycle['success_log'][mv][w_i] = chk
                                            save_data()
                                    
                                    st.divider()
                                    # WEEK DONE BUTTON
                                    if not cycle['week_completed_log'][w_i]:
                                        if st.button("✅ Week Done", key=f"wd_{true_idx}_{w_i}", use_container_width=True, type="primary"):
                                            cycle['week_completed_log'][w_i] = True
                                            cycle['failed_week_log'][w_i] = False
                                            save_data(); st.rerun()
                                    else:
                                        st.success("Week Logged!")
                                        if st.button("🔓 Undo Week Done", key=f"ud_{true_idx}_{w_i}"):
                                            cycle['week_completed_log'][w_i] = False
                                            save_data(); st.rerun()

                                    if st.button("💀 All Failed", key=f"af_{true_idx}_{w_i}", use_container_width=True):
                                        cycle['failed_week_log'][w_i] = True
                                        cycle['week_completed_log'][w_i] = True # Mark as done so it doesn't stay open
                                        for m in ["Squat", "Bench", "OHP", "Deadlift"]: cycle['success_log'][m][w_i] = False
                                        save_data(); st.rerun()

            # --- PROGRESS SECTION ---
            if st.session_state[prog_key]:
                st.divider()
                weeks_range = list(range(1, cycle['weeks'] + 1))
                c1, c2 = st.columns(2)
                with c1:
                    fig_w = go.Figure()
                    for lift, color in zip(["Squat", "Bench", "OHP", "Deadlift"], ["#FF4B4B", "#1C83E1", "#FFFFFF", "#FFC300"]):
                        y_vals = []
                        for w in range(cycle['weeks']):
                            c = sum(1 for prev_w in range(w) if cycle['success_log'][lift][prev_w] and cycle['week_completed_log'][prev_w])
                            y_vals.append(cycle['lifts'][lift]['rm'] + (cycle['lifts'][lift]['inc'] * c))
                        fig_w.add_trace(go.Scatter(x=weeks_range, y=y_vals, name=lift, line=dict(color=color, width=3)))
                    fig_w.update_layout(title="Lifts Progress", height=350, template="plotly_dark")
                    st.plotly_chart(fig_w, use_container_width=True)
                with c2:
                    fig_p = go.Figure()
                    fig_p.add_trace(go.Scatter(x=weeks_range, y=cycle['weight_log'], name="BW", line=dict(color="#00C49A", width=4)))
                    fig_p.update_layout(title="BW Progress", height=350, template="plotly_dark")
                    st.plotly_chart(fig_p, use_container_width=True)
else:
    st.info("No active cycles. Go lift something heavy!")
