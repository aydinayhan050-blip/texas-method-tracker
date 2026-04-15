import streamlit as st
import json
from datetime import datetime
import plotly.graph_objects as go
from streamlit_local_storage import LocalStorage

# --- UI CONFIG ---
st.set_page_config(page_title="Texas Method: Auto-Sync", layout="wide")

# Initialize Local Storage
local_storage = LocalStorage()

# --- AUTO-SAVE LOGIC ---
def sync_to_device():
    """Tüm session_state verisini otomatik olarak telefona kaydeder."""
    if 'cycles' in st.session_state:
        local_storage.setItem("texas_method_v1", json.dumps(st.session_state.cycles))

def load_from_device():
    """Açılışta telefondaki veriyi çeker."""
    saved_data = local_storage.getItem("texas_method_v1")
    return json.loads(saved_data) if saved_data else []

# --- CSS (Hardcore Red & Black) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    div[data-testid="stNotification"] { background-color: #cc0000 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- INITIAL LOAD ---
if 'cycles' not in st.session_state:
    stored_data = load_from_device()
    st.session_state.cycles = stored_data

# --- APP INTERFACE ---
st.title("Texas Method: Auto-Save 🦾")

# --- NEW CYCLE FORM ---
with st.expander("👊 Launch New Cycle", expanded=len(st.session_state.cycles) == 0):
    with st.form("cycle_form", clear_on_submit=True):
        c_name = st.text_input("Cycle Name", value="New Season")
        col1, col2 = st.columns(2)
        with col1:
            s_rm = st.number_input("Squat 5RM", value=100.0)
            b_rm = st.number_input("Bench 5RM", value=80.0)
        with col2:
            o_rm = st.number_input("OHP 5RM", value=50.0)
            d_rm = st.number_input("Deadlift 5RM", value=140.0)
        
        if st.form_submit_button("Start Training"):
            new_cycle = {
                "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                "name": c_name,
                "lifts": {"Squat": s_rm, "Bench": b_rm, "OHP": o_rm, "Deadlift": d_rm},
                "status": "Active"
            }
            st.session_state.cycles.append(new_cycle)
            sync_to_device() # OTOMATİK KAYIT
            st.rerun()

# --- DISPLAY & AUTO-UPDATE ---
if st.session_state.cycles:
    for idx, cycle in enumerate(reversed(st.session_state.cycles)):
        # Sondan başa doğru indexi bulmak için
        true_idx = len(st.session_state.cycles) - 1 - idx
        
        with st.container(border=True):
            col_head, col_del = st.columns([0.85, 0.15])
            with col_head:
                st.subheader(f"⚡ {cycle['name']}")
            with col_del:
                if st.button("🗑️", key=f"del_{cycle['id']}"):
                    st.session_state.cycles.pop(true_idx)
                    sync_to_device() # OTOMATİK KAYIT (SİLERKEN)
                    st.rerun()
            
            # Değerleri değiştirdiğinde otomatik kaydetmesi için:
            new_sq = st.number_input(f"Squat 5RM ({cycle['id']})", value=float(cycle['lifts']['Squat']), key=f"sq_{cycle['id']}")
            if new_sq != cycle['lifts']['Squat']:
                st.session_state.cycles[true_idx]['lifts']['Squat'] = new_sq
                sync_to_device() # OTOMATİK KAYIT (DEĞİŞTİĞİ ANDA)

            st.write(f"Current Target: {cycle['lifts']['Squat']} kg")
else:
    st.info("No active cycles. Your progress will be auto-saved to this device.")

# Alt kısma küçük bir status bar
st.caption("✨ Data is automatically synced to your device storage.")