import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

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
    st.session_state.cycles = []
if 'current_unit' not in st.session_state:
    st.session_state.current_unit = "LBS"

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    new_unit = st.radio("Unit", ["LBS", "KG"], index=0)
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
        st.rerun()

    plate = st.number_input(f"Plates ({new_unit})", value=2.5 if new_unit == "LBS" else 1.25, step=0.25)
    st.divider()
    if st.button("🔥 Wipe Everything", type="primary", use_container_width=True):
        st.session_state.cycles = []
        st.rerun()

# --- CUSTOM CSS (Hardcore Red Overrides) ---
st.markdown(f"""
    <style>
    /* Uygulama Arka Planı */
    .stApp {{ background-color: {bg_color}; color: {text_color}; }}
    
    /* EGZERSİZ KUTULARI - MAVİYİ TAMAMEN SİLİP KIRMIZI YAPIYORUZ */
    div[data-testid="stNotification"] {{
        background-color: #cc0000 !important;
        color: white !important;
        border: none !important;
    }}
    
    /* Kutuların içindeki ikonları da beyaz yapalım ki görünsün */
    div[data-testid="stNotification"] svg {{
        fill: white !important;
    }}
    
    /* Uyarı Kutusu (Üstteki) */
    .warning-box {{ 
        background-color: #000000; 
        padding: 15px; 
        border-radius: 8px; 
        border: 2px solid #ff0000; 
        color: #ffffff; 
        text-align: center; 
        margin-bottom: 25px; 
    }}

    /* Tab Başlıkları */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
        color: #ff0000 !important;
        border-bottom-color: #ff0000 !important;
    }}

    .warmup-text {{ font-size: 0.85rem; color: #888; margin-bottom: 2px; }}
    .signature-footer {{ text-align: center; color: #555; font-size: 0.8rem; margin-top: 50px; padding-bottom: 20px; }}
    </style>
    """, unsafe_allow_html=True)

st.title("The Texas Method Tracker")

st.markdown("""<div class="warning-box">
    <b style="color: #ff0000;">ATTENTION:</b> Unchecked Friday boxes = No progress for next week.
</div>""", unsafe_allow_html=True)

# --- CREATE CYCLE ---
with st.expander("👊 New Cycle", expanded=len(st.session_state.cycles) == 0):
    with st.form("new_cycle_form"):
        c_name = st.text_input("Cycle Name", placeholder="e.g., Heavy Duty")
        c_weeks = st.slider("Weeks", 1, 16, 8)
        c_bw = st.number_input(f"Initial BW ({new_unit})", value=180.0 if new_unit == "LBS" else 80.0, step=0.5)
        
        st.write("---")
        def_inc = {"S": 5, "B": 5, "O": 5, "D": 10} if new_unit == "LBS" else {"S": 2.5, "B": 2.5, "O": 2.5, "D": 5}
        col1, col2, col3, col4 = st.columns(4)
        with col1: s_rm, s_inc = st.text_input("Squat 5RM", "225"), st.text_input("Sq Inc", str(def_inc["S"]))
        with col2: b_rm, b_inc = st.text_input("Bench 5RM", "185"), st.text_input("Bn Inc", str(def_inc["B"]))
        with col3: o_rm, o_inc = st.text_input("OHP 5RM", "115"), st.text_input("Oh Inc", str(def_inc["O"]))
        with col4: d_rm, d_inc = st.text_input("Dead 5RM", "315"), st.text_input("Dl Inc", str(def_inc["D"]))
            
        if st.form_submit_button("🏁 Start Cycle", use_container_width=True):
            if not c_name: st.error("Name your cycle.")
            else:
                st.session_state.cycles.append({
                    "name": c_name, "date": datetime.now().strftime("%Y-%m-%d"), "weeks": int(c_weeks),
                    "success_log": {m: [False]*int(c_weeks) for m in ["Squat", "Bench", "OHP", "Deadlift"]},
                    "weight_log": [float(c_bw)] * int(c_weeks),
                    "lifts": {
                        "Squat": {"rm": float(s_rm), "inc": float(s_inc)}, "Bench": {"rm": float(b_rm), "inc": float(b_inc)},
                        "OHP": {"rm": float(o_rm), "inc": float(o_inc)}, "Deadlift": {"rm": float(d_rm), "inc": float(d_inc)}
                    }
                })
                st.rerun()

# --- DISPLAY ---
if st.session_state.cycles:
    for idx, cycle in enumerate(reversed(st.session_state.cycles)):
        true_idx = len(st.session_state.cycles) - 1 - idx
        with st.container(border=True):
            head_col1, head_col2 = st.columns([0.7, 0.3])
            head_col1.subheader(f"⚡ {cycle['name']}")
            
            del_key = f"confirm_del_{true_idx}"
            if del_key not in st.session_state: st.session_state[del_key] = False
            
            if not st.session_state[del_key]:
                if head_col2.button("🗑️ Delete", key=f"btn_{true_idx}", use_container_width=True):
                    st.session_state[del_key] = True
                    st.rerun()
            else:
                head_col2.error("Sure?")
                c1, c2 = head_col2.columns(2)
                if c1.button("Yes", key=f"yes_{true_idx}", use_container_width=True):
                    st.session_state.cycles.pop(true_idx)
                    del st.session_state[del_key]
                    st.rerun()
                if c2.button("No", key=f"no_{true_idx}", use_container_width=True):
                    st.session_state[del_key] = False
                    st.rerun()

            tab1, tab2 = st.tabs(["📅 Training Log", "📈 Progress Analysis"])
            with tab1:
                w_tabs = st.tabs([f"W{i+1}" for i in range(cycle['weeks'])])
                for w_i in range(cycle['weeks']):
                    counts = {mv: sum(1 for s in cycle['success_log'][mv][:w_i] if s == True) for mv in ["Squat", "Bench", "OHP", "Deadlift"]}
                    with w_tabs[w_i]:
                        st.write("**Current BW**")
                        new_bw = st.number_input(f"Weight", value=cycle['weight_log'][w_i], key=f"bw_{true_idx}_{w_i}", step=0.1, label_visibility="collapsed")
                        if new_bw != cycle['weight_log'][w_i]:
                            cycle['weight_log'][w_i] = new_bw
                            st.rerun()
                        
                        st.divider()
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
                                st.markdown(f"#### {day_title}")
                                for mv in moves:
                                    base_5rm = cycle['lifts'][mv]['rm'] + (cycle['lifts'][mv]['inc'] * counts[mv])
                                    work_weight = round_to_plates(base_5rm * pct, plate)
                                    # BURASI KIRMIZI KUTU OLACAK KISIM:
                                    st.info(f"**{mv}**: {rep_scheme} @ **{format_weight(work_weight)} {new_unit}**")
                                    with st.expander("🔥 Warmup"):
                                        for line in get_warmup_sets(work_weight, new_unit, plate):
                                            st.markdown(f'<p class="warmup-text">{line}</p>', unsafe_allow_html=True)
                                
                                if "Wednesday" in day_title:
                                    st.divider()
                                    st.info("Pullups: 3 Sets to Failure")
                                    st.info("Hyperextensions: 5 Sets x 10")

                                if "Friday" in day_title:
                                    st.divider()
                                    st.write("**Friday Check? 🏆**")
                                    for mv in moves:
                                        val = cycle['success_log'][mv][w_i]
                                        if st.checkbox(f"Crushed {mv}?", value=val, key=f"s_{true_idx}_{w_i}_{mv}") != val:
                                            cycle['success_log'][mv][w_i] = not val
                                            st.rerun()

            with tab2:
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                weeks_axis = [f"W{i+1}" for i in range(cycle['weeks'])]
                for lift, data in cycle['lifts'].items():
                    y, s_c = [], 0
                    for i in range(cycle['weeks']):
                        current_w = round_to_plates(data['rm'] + (data['inc'] * s_c), plate)
                        y.append(current_w)
                        if cycle['success_log'][lift][i]: s_c += 1
                    fig.add_trace(go.Scatter(x=weeks_axis, y=y, name=f"{lift}", mode='lines+markers'), secondary_y=False)
                
                fig.add_trace(go.Scatter(x=weeks_axis, y=cycle['weight_log'], name="Bodyweight", line=dict(color='gray', dash='dot'), mode='lines+markers'), secondary_y=True)
                fig.update_layout(template="plotly_dark" if theme_choice == "Deep Dark" else "plotly_white", height=600)
                st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="signature-footer">By Aydin Ayhan</div>', unsafe_allow_html=True)
else:
    st.info("No active cycles.")
