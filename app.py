import streamlit as st
import json
from datetime import datetime
import pandas as pd
from streamlit_local_storage import LocalStorage

# --- UI CONFIG ---
st.set_page_config(page_title="Texas Method Tracker", layout="wide")
local_storage = LocalStorage()

# --- AUTO-SAVE & LOAD ---
def sync_to_device():
    if 'cycles' in st.session_state:
        data = {"cycles": st.session_state.cycles, "unit": st.session_state.current_unit}
        local_storage.setItem("texas_method_v16", json.dumps(data))

def load_from_device():
    saved = local_storage.getItem("texas_method_v16")
    return json.loads(saved) if saved else None

if 'initialized' not in st.session_state:
    stored = load_from_device()
    if stored:
        st.session_state.cycles = stored.get('cycles', [])
        st.session_state.current_unit = stored.get('unit', "LBS")
    else:
        st.session_state.cycles = []
        st.session_state.current_unit = "LBS"
    st.session_state.initialized = True

# --- HELPERS ---
def format_weight(weight):
    val = round(float(weight), 2)
    return f"{int(val)}" if val % 1 == 0 else f"{val}"

def round_to_plates(weight, smallest_unit):
    step = smallest_unit * 2
    return round(weight / step) * step

# --- CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    button[kind="primary"] { background-color: #ff0000 !important; border: none !important; }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] { color: #ff0000 !important; border-bottom-color: #ff0000 !important; }
    .crush-box { border: 2px solid #ff0000; padding: 15px; border-radius: 10px; background-color: #1a0000; margin-top: 10px; }
    .signature { font-size: 14px; color: #555; text-align: center; margin-top: 50px; border-top: 1px solid #333; padding-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("Texas Method: Eternal Tracker 🦾")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    new_unit = st.radio("Unit", ["LBS", "KG"], index=0 if st.session_state.current_unit == "LBS" else 1)
    if new_unit != st.session_state.current_unit:
        st.session_state.current_unit = new_unit
        sync_to_device()
        st.rerun()
    plate = st.number_input(f"Smallest Plate ({new_unit})", value=2.5 if new_unit == "LBS" else 1.25, step=0.25)
    if st.button("🔥 Full Wipe", type="primary", use_container_width=True):
        st.session_state.cycles = []
        sync_to_device()
        st.rerun()

# --- CREATE CYCLE ---
with st.expander("👊 Launch New Cycle", expanded=len(st.session_state.cycles) == 0):
    with st.form("new_cycle"):
        c_name = st.text_input("Cycle Name", placeholder="Iron Road")
        c_weeks = st.slider("Weeks", 1, 12, 8)
        col1, col2, col3, col4 = st.columns(4)
        with col1: s_rm = st.number_input("Squat 5RM", value=100.0)
        with col2: b_rm = st.number_input("Bench 5RM", value=80.0)
        with col3: o_rm = st.number_input("OHP 5RM", value=50.0)
        with col4: d_rm = st.number_input("Dead 5RM", value=140.0)
        if st.form_submit_button("🏁 Launch", use_container_width=True):
            st.session_state.cycles.append({
                "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                "name": c_name, "weeks": int(c_weeks),
                "success_log": {m: [False]*int(c_weeks) for m in ["Squat", "Bench", "OHP", "Deadlift"]},
                "lifts": {
                    "Squat": {"rm": float(s_rm), "inc": 2.5 if new_unit == "LBS" else 2.5},
                    "Bench": {"rm": float(b_rm), "inc": 2.5 if new_unit == "LBS" else 1.25},
                    "OHP": {"rm": float(o_rm), "inc": 2.5 if new_unit == "LBS" else 1.25},
                    "Deadlift": {"rm": float(d_rm), "inc": 5.0 if new_unit == "LBS" else 5.0}
                }
            })
            sync_to_device(); st.rerun()

# --- DISPLAY ---
if st.session_state.cycles:
    for idx, cycle in enumerate(reversed(st.session_state.cycles)):
        t_idx = len(st.session_state.cycles) - 1 - idx
        with st.container(border=True):
            st.subheader(f"⚡ {cycle['name']}")
            w_tabs = st.tabs([f"W{i+1}" for i in range(cycle['weeks'])])
            for w_i in range(cycle['weeks']):
                with w_tabs[w_i]:
                    is_a = (w_i + 1) % 2 != 0
                    m_pres, w_pres = ("Bench", "OHP") if is_a else ("OHP", "Bench")
                    cols = st.columns(3)
                    days = [
                        ("Monday (Volume)", 0.90, "5x5", ["Squat", m_pres, "Deadlift"]),
                        ("Wednesday (Light)", 0.70, "2x5", ["Squat", w_pres]),
                        ("Friday (Intensity)", 1.00, "1x5", ["Squat", m_pres, "Deadlift"])
                    ]
                    for d_i, (title, pct, reps, moves) in enumerate(days):
                        with cols[d_i]:
                            st.markdown(f"#### {title}")
                            if d_i == 2: st.markdown('<div class="crush-box"><b>Did You Crush It?</b>', unsafe_allow_html=True)
                            for mv in moves:
                                # Haftalık artış hesabı: Geçmiş haftalardaki başarı sayısına bak
                                successes = sum(1 for s in cycle['success_log'][mv][:w_i] if s)
                                current_w = round_to_plates(cycle['lifts'][mv]['rm'] + (successes * cycle['lifts'][mv]['inc']), plate)
                                work_w = round_to_plates(current_w * pct, plate)
                                st.info(f"**{mv}**: {reps} @ **{format_weight(work_w)}**")
                                
                                if d_i == 2: # Friday Checklist
                                    val = cycle['success_log'][mv][w_i]
                                    if st.checkbox(f"Crushed {mv}", value=val, key=f"c_{cycle['id']}_{w_i}_{mv}"):
                                        if not val:
                                            st.session_state.cycles[t_idx]['success_log'][mv][w_i] = True
                                            sync_to_device(); st.rerun()
                            if d_i == 2: st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="signature">Assistant Exercises by Aydın Ayhan</div>', unsafe_allow_html=True)
