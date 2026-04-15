import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import json
import os
import time

# --- TRANSLATIONS ---
LANGUAGES = {
    "English": "EN", "Türkçe": "TR", "Español": "ES", 
    "Français": "FR", "Deutsch": "DE", "Русский": "RU"
}

T = {
    "EN": {
        "settings": "⚙️ Settings", "unit": "📏 Unit", "theme": "🎨 Theme", "lang": "🌐 Language",
        "small_plate": "🔩 Smallest Plate", "wipe_data": "🚨 Wipe All Data", "author": "by Aydin Ayhan",
        "title": "Texas Method Training Tracker", "create": "👊 Create New Cycle",
        "variant": "🏋️ Select Method Variant", "modern": "Modern (Deadlift Focus)", "standard": "Standard (Power Clean)",
        "var_help": "Standard uses Power Cleans on Monday to manage fatigue for Friday intensity.",
        "c_name": "📝 Cycle Name", "ph_name": "e.g. Strength Phase 1", "duration": "⏳ Duration (Weeks)",
        "bw": "⚖️ Initial BW", "inc": "Inc", "pc_disabled": "Power Clean Disabled",
        "start": "🚀 Start Cycle", "err_name": "⚠️ Please enter a name!",
        "started": "Started", "prog": "📊 Progress", "wgts": "🏋️ Weights", "del": "🗑️ Delete", "yes_del": "Yes, delete!",
        "week": "Week", "rest": "⏱️ Rest (min)", "pause": "⏸️ Pause / ▶️ Resume",
        "mon": "Monday (Volume)", "wed": "Wednesday (Light)", "fri": "Friday (Intensity)",
        "warmup": "🔥 Warmup", "bar": "Bar", "sets_3": "3 Sets", "bw_fail": "Bodyweight - Failure", "reps_10_15": "10-15 Reps",
        "pc_chk": "⚡ Power Clean Checklist", 
        "pc_help": "ℹ️ **What's the play?** If you crushed every set with solid form today, check this box. Doing so triggers a weight increase for next week. If you struggled or your form was shit, leave it blank—we'll stay at this weight to dial it in.",
        "crushed": "Crushed", "mark_fin": "Mark Finished", "fin": "Finished!",
        "fri_chk": "🏆 Friday Checklist",
        "fri_help": "ℹ️ **Judgment Day!** Mark the lifts you successfully smashed today. The checked ones will get heavier next week based on your chosen increments. If you missed reps, leave 'em blank and stay put. Don't bullshit yourself, boss!",
        "fin_week": "🏁 Finish & Log Week", "week_fin": "🏆 Week Finished!",
        "lift_prog": "Lifts Progress", "bw_prog": "Bodyweight Progress", "no_cyc": "No active cycles. Start your journey!",
        "Squat": "Squat", "Bench": "Bench", "OHP": "OHP", "Deadlift": "Deadlift", "Power Clean": "Power Clean", "Chin-ups": "Chin-ups", "Back Extensions": "Back Extensions"
    },
    "TR": {
        "settings": "⚙️ Ayarlar", "unit": "📏 Birim", "theme": "🎨 Tema", "lang": "🌐 Dil",
        "small_plate": "🔩 En Küçük Plaka", "wipe_data": "🚨 Tüm Verileri Sil", "author": "Hazırlayan: Aydın Ayhan",
        "title": "Texas Method Antrenman Takibi", "create": "👊 Yeni Döngü Oluştur",
        "variant": "🏋️ Metot Varyantı Seç", "modern": "Modern (Deadlift Odaklı)", "standard": "Standart (Power Clean)",
        "var_help": "Standart metot, Cuma günkü yoğunluğa enerji saklamak için Pazartesi günleri Power Clean kullanır.",
        "c_name": "📝 Döngü Adı", "ph_name": "Örn: Güç Fazı 1", "duration": "⏳ Süre (Hafta)",
        "bw": "⚖️ Başlangıç Vücut Ağırlığı", "inc": "Artış", "pc_disabled": "Power Clean Devre Dışı",
        "start": "🚀 Döngüyü Başlat", "err_name": "⚠️ Lütfen bir isim girin!",
        "started": "Başlangıç", "prog": "📊 İlerleme", "wgts": "🏋️ Ağırlıklar", "del": "🗑️ Sil", "yes_del": "Evet, sil!",
        "week": "Hafta", "rest": "⏱️ Dinlenme (dk)", "pause": "⏸️ Durdur / ▶️ Devam",
        "mon": "Pazartesi (Hacim)", "wed": "Çarşamba (Hafif)", "fri": "Cuma (Yoğunluk)",
        "warmup": "🔥 Isınma", "bar": "Bar", "sets_3": "3 Set", "bw_fail": "Vücut Ağırlığı - Tükeniş", "reps_10_15": "10-15 Tekrar",
        "pc_chk": "⚡ Power Clean Kontrol Listesi", 
        "pc_help": "ℹ️ **Ne yapıyoruz?** Bugün her seti sağlam bir formla bitirdiysen bu kutuyu işaretle. Böylece haftaya ağırlık artar. Eğer zorlandıysan veya formun bozulduysa boş bırak—tekniği oturtmak için bu ağırlıkta kalacağız.",
        "crushed": "Parçalandı:", "mark_fin": "Bitirildi İşaretle", "fin": "Bitti!",
        "fri_chk": "🏆 Cuma Kontrol Listesi",
        "fri_help": "ℹ️ **Hesap Günü!** Bugün başarıyla ezdiğin kaldırışları işaretle. İşaretlenenler seçtiğin artışlara göre haftaya ağırlaşacak. Tekrar kaçırdıysan boş bırak ve yerinde say. Kendini kandırma patron!",
        "fin_week": "🏁 Haftayı Bitir ve Kaydet", "week_fin": "🏆 Hafta Tamamlandı!",
        "lift_prog": "Kaldırış İlerlemesi", "bw_prog": "Vücut Ağırlığı İlerlemesi", "no_cyc": "Aktif döngü yok. Yolculuğuna başla!",
        "Squat": "Squat", "Bench": "Bench", "OHP": "OHP", "Deadlift": "Deadlift", "Power Clean": "Power Clean", "Chin-ups": "Barfiks", "Back Extensions": "Ters Mekik"
    },
    "ES": {
        "settings": "⚙️ Ajustes", "unit": "📏 Unidad", "theme": "🎨 Tema", "lang": "🌐 Idioma",
        "small_plate": "🔩 Disco Más Pequeño", "wipe_data": "🚨 Borrar Todos los Datos", "author": "por Aydin Ayhan",
        "title": "Registro de Entrenamiento Texas Method", "create": "👊 Crear Nuevo Ciclo",
        "variant": "🏋️ Seleccionar Variante", "modern": "Moderno (Enfoque Peso Muerto)", "standard": "Estándar (Power Clean)",
        "var_help": "El estándar usa Power Cleans el lunes para gestionar la fatiga para la intensidad del viernes.",
        "c_name": "📝 Nombre del Ciclo", "ph_name": "Ej. Fase de Fuerza 1", "duration": "⏳ Duración (Semanas)",
        "bw": "⚖️ Peso Corporal Inicial", "inc": "Aumento", "pc_disabled": "Power Clean Desactivado",
        "start": "🚀 Iniciar Ciclo", "err_name": "⚠️ ¡Por favor ingresa un nombre!",
        "started": "Iniciado", "prog": "📊 Progreso", "wgts": "🏋️ Pesos", "del": "🗑️ Eliminar", "yes_del": "¡Sí, eliminar!",
        "week": "Semana", "rest": "⏱️ Descanso (min)", "pause": "⏸️ Pausa / ▶️ Reanudar",
        "mon": "Lunes (Volumen)", "wed": "Miércoles (Ligero)", "fri": "Viernes (Intensidad)",
        "warmup": "🔥 Calentamiento", "bar": "Barra", "sets_3": "3 Series", "bw_fail": "Peso Corporal - Al Fallo", "reps_10_15": "10-15 Reps",
        "pc_chk": "⚡ Lista de Power Clean", 
        "pc_help": "ℹ️ **¿Cuál es el plan?** Si destrozaste cada serie con buena técnica hoy, marca esto. Hará que el peso suba la próxima semana. Si te costó, déjalo en blanco para consolidar la técnica.",
        "crushed": "Destrozado:", "mark_fin": "Marcar Finalizado", "fin": "¡Finalizado!",
        "fri_chk": "🏆 Lista del Viernes",
        "fri_help": "ℹ️ **¡Día del Juicio!** Marca los levantamientos que lograste hoy. Subirán de peso la próxima semana. Si fallaste repeticiones, no marques. ¡Sin excusas, jefe!",
        "fin_week": "🏁 Terminar y Guardar Semana", "week_fin": "🏆 ¡Semana Terminada!",
        "lift_prog": "Progreso de Levantamientos", "bw_prog": "Progreso de Peso Corporal", "no_cyc": "No hay ciclos activos. ¡Comienza tu viaje!",
        "Squat": "Sentadilla", "Bench": "Press Banca", "OHP": "OHP", "Deadlift": "Peso Muerto", "Power Clean": "Power Clean", "Chin-ups": "Dominadas", "Back Extensions": "Extensiones Lumbares"
    },
    "FR": {
        "settings": "⚙️ Paramètres", "unit": "📏 Unité", "theme": "🎨 Thème", "lang": "🌐 Langue",
        "small_plate": "🔩 Plus Petit Disque", "wipe_data": "🚨 Effacer Toutes les Données", "author": "par Aydin Ayhan",
        "title": "Suivi d'Entraînement Texas Method", "create": "👊 Créer un Nouveau Cycle",
        "variant": "🏋️ Sélectionner la Variante", "modern": "Moderne (Focus Soulevé de Terre)", "standard": "Standard (Power Clean)",
        "var_help": "Le standard utilise le Power Clean le lundi pour gérer la fatigue pour l'intensité du vendredi.",
        "c_name": "📝 Nom du Cycle", "ph_name": "Ex: Phase de Force 1", "duration": "⏳ Durée (Semaines)",
        "bw": "⚖️ Poids de Corps Initial", "inc": "Augment", "pc_disabled": "Power Clean Désactivé",
        "start": "🚀 Démarrer le Cycle", "err_name": "⚠️ Veuillez entrer un nom !",
        "started": "Démarré", "prog": "📊 Progrès", "wgts": "🏋️ Poids", "del": "🗑️ Supprimer", "yes_del": "Oui, supprimer !",
        "week": "Semaine", "rest": "⏱️ Repos (min)", "pause": "⏸️ Pause / ▶️ Reprendre",
        "mon": "Lundi (Volume)", "wed": "Mercredi (Léger)", "fri": "Vendredi (Intensité)",
        "warmup": "🔥 Échauffement", "bar": "Barre", "sets_3": "3 Séries", "bw_fail": "Poids de Corps - Échec", "reps_10_15": "10-15 Réps",
        "pc_chk": "⚡ Liste de Contrôle Power Clean", 
        "pc_help": "ℹ️ **C'est quoi le plan ?** Si tu as explosé chaque série avec une bonne technique, coche cette case. Le poids augmentera la semaine prochaine. Si c'était dur, laisse vide, on garde ce poids pour s'améliorer.",
        "crushed": "Explosé :", "mark_fin": "Marquer Terminé", "fin": "Terminé !",
        "fri_chk": "🏆 Liste du Vendredi",
        "fri_help": "ℹ️ **Le Jour du Jugement !** Coche les levés réussis. Ils seront plus lourds la semaine prochaine. Si tu as raté des réps, laisse vide. Ne te mens pas à toi-même, chef !",
        "fin_week": "🏁 Terminer et Sauvegarder", "week_fin": "🏆 Semaine Terminée !",
        "lift_prog": "Progrès des Levés", "bw_prog": "Progrès du Poids", "no_cyc": "Aucun cycle actif. Commencez !",
        "Squat": "Squat", "Bench": "Développé Couché", "OHP": "OHP", "Deadlift": "Soulevé de Terre", "Power Clean": "Power Clean", "Chin-ups": "Tractions", "Back Extensions": "Extensions Lombaires"
    },
    "DE": {
        "settings": "⚙️ Einstellungen", "unit": "📏 Einheit", "theme": "🎨 Design", "lang": "🌐 Sprache",
        "small_plate": "🔩 Kleinste Hantelscheibe", "wipe_data": "🚨 Alle Daten löschen", "author": "von Aydin Ayhan",
        "title": "Texas Method Trainings-Tracker", "create": "👊 Neuen Zyklus erstellen",
        "variant": "🏋️ Methodenvariante wählen", "modern": "Modern (Kreuzheben Fokus)", "standard": "Standard (Power Clean)",
        "var_help": "Standard nutzt Power Cleans am Montag, um Ermüdung für die Freitagsintensität zu managen.",
        "c_name": "📝 Zyklusname", "ph_name": "z.B. Kraftphase 1", "duration": "⏳ Dauer (Wochen)",
        "bw": "⚖️ Startgewicht (Körper)", "inc": "Erhöhung", "pc_disabled": "Power Clean Deaktiviert",
        "start": "🚀 Zyklus starten", "err_name": "⚠️ Bitte einen Namen eingeben!",
        "started": "Gestartet", "prog": "📊 Fortschritt", "wgts": "🏋️ Gewichte", "del": "🗑️ Löschen", "yes_del": "Ja, löschen!",
        "week": "Woche", "rest": "⏱️ Pause (Min)", "pause": "⏸️ Pause / ▶️ Weiter",
        "mon": "Montag (Volumen)", "wed": "Mittwoch (Leicht)", "fri": "Freitag (Intensität)",
        "warmup": "🔥 Aufwärmen", "bar": "Stange", "sets_3": "3 Sätze", "bw_fail": "Körpergewicht - Muskelversagen", "reps_10_15": "10-15 Wdh",
        "pc_chk": "⚡ Power Clean Checkliste", 
        "pc_help": "ℹ️ **Was ist der Plan?** Wenn du heute jeden Satz mit sauberer Technik gerockt hast, kreuze das an. Das erhöht das Gewicht für nächste Woche. Wenn nicht, lass es leer – wir bleiben bei diesem Gewicht.",
        "crushed": "Zerstört:", "mark_fin": "Als Fertig Markieren", "fin": "Fertig!",
        "fri_chk": "🏆 Freitags-Checkliste",
        "fri_help": "ℹ️ **Tag der Abrechnung!** Markiere die Lifts, die du gemeistert hast. Diese werden nächste Woche schwerer. Wenn du Wdh verpasst hast, lass sie leer. Mach dir nichts vor, Boss!",
        "fin_week": "🏁 Woche Beenden & Speichern", "week_fin": "🏆 Woche Beendet!",
        "lift_prog": "Fortschritt der Lifts", "bw_prog": "Körpergewicht Fortschritt", "no_cyc": "Keine aktiven Zyklen. Starten Sie!",
        "Squat": "Kniebeuge", "Bench": "Bankdrücken", "OHP": "OHP", "Deadlift": "Kreuzheben", "Power Clean": "Power Clean", "Chin-ups": "Klimmzüge", "Back Extensions": "Rückenstrecker"
    },
    "RU": {
        "settings": "⚙️ Настройки", "unit": "📏 Единица", "theme": "🎨 Тема", "lang": "🌐 Язык",
        "small_plate": "🔩 Наименьший диск", "wipe_data": "🚨 Удалить все данные", "author": "от Aydin Ayhan",
        "title": "Трекер тренировок Texas Method", "create": "👊 Создать новый цикл",
        "variant": "🏋️ Выбрать вариант метода", "modern": "Современный (акцент на становую)", "standard": "Стандарт (взятие на грудь)",
        "var_help": "Стандарт использует взятие на грудь в понедельник для управления усталостью перед пятницей.",
        "c_name": "📝 Название цикла", "ph_name": "напр. Фаза силы 1", "duration": "⏳ Длительность (недель)",
        "bw": "⚖️ Начальный вес тела", "inc": "Шаг", "pc_disabled": "Взятие на грудь отключено",
        "start": "🚀 Начать цикл", "err_name": "⚠️ Пожалуйста, введите имя!",
        "started": "Начат", "prog": "📊 Прогресс", "wgts": "🏋️ Веса", "del": "🗑️ Удалить", "yes_del": "Да, удалить!",
        "week": "Неделя", "rest": "⏱️ Отдых (мин)", "pause": "⏸️ Пауза / ▶️ Продолжить",
        "mon": "Понедельник (Объем)", "wed": "Среда (Легкая)", "fri": "Пятница (Интенсивность)",
        "warmup": "🔥 Разминка", "bar": "Гриф", "sets_3": "3 Подхода", "bw_fail": "Вес тела - до отказа", "reps_10_15": "10-15 Повторений",
        "pc_chk": "⚡ Чек-лист взятия на грудь", 
        "pc_help": "ℹ️ **Какой план?** Если сегодня ты порвал каждый подход с отличной техникой, поставь галочку. Это увеличит вес на следующей неделе. Если техника хромала, оставь пустым — оставим этот вес для отработки.",
        "crushed": "Разорван:", "mark_fin": "Отметить завершенным", "fin": "Завершено!",
        "fri_chk": "🏆 Пятничный чек-лист",
        "fri_help": "ℹ️ **Судный день!** Отметь подъемы, которые ты успешно порвал сегодня. Отмеченные станут тяжелее на следующей неделе. Если не потянул, оставь пустым. Не обманывай себя, босс!",
        "fin_week": "🏁 Завершить и сохранить неделю", "week_fin": "🏆 Неделя завершена!",
        "lift_prog": "Прогресс подъемов", "bw_prog": "Прогресс веса тела", "no_cyc": "Нет активных циклов. Начни свой путь!",
        "Squat": "Присед", "Bench": "Жим лежа", "OHP": "OHP", "Deadlift": "Становая тяга", "Power Clean": "Взятие на грудь", "Chin-ups": "Подтягивания", "Back Extensions": "Экстензии спины"
    }
}

# --- STORAGE FUNCTIONS ---
DB_FILE = "texas_method_data.json"

def save_data():
    data = {"cycles": st.session_state.cycles, "unit": st.session_state.current_unit, "lang": st.session_state.lang}
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            cycles = data.get("cycles", [])
            unit = data.get("unit", "KG")
            lang = data.get("lang", "EN")
            for cycle in cycles:
                if "week_completed_log" not in cycle: cycle["week_completed_log"] = [False] * cycle["weeks"]
                if "day_completed_log" not in cycle: cycle["day_completed_log"] = {}
                if "weight_log" not in cycle: cycle["weight_log"] = [80.0] * cycle["weeks"]
                if "success_log" not in cycle: cycle["success_log"] = {m: [False]*cycle["weeks"] for m in ["Squat", "Bench", "OHP", "Deadlift", "Power Clean"]}
                if "Power Clean" not in cycle["success_log"]: cycle["success_log"]["Power Clean"] = [False]*cycle["weeks"]
                if "variant" not in cycle: cycle["variant"] = "Modern (Deadlift Focus)"
                if "start_date" not in cycle: cycle["start_date"] = datetime.now().strftime("%Y-%m-%d")
            return cycles, unit, lang
    return [], "KG", "EN"

def update_success_log(t_idx, w_i, mv, key):
    st.session_state.cycles[t_idx]['success_log'][mv][w_i] = st.session_state[key]
    save_data()

# --- BUTTON CALLBACKS (Fixes double-click issues) ---
def mark_day_finished(t_idx, d_key):
    st.session_state.cycles[t_idx]['day_completed_log'][d_key] = True
    save_data()

def mark_week_finished(t_idx, w_i, d_key):
    st.session_state.cycles[t_idx]['day_completed_log'][d_key] = True
    st.session_state.cycles[t_idx]['week_completed_log'][w_i] = True
    save_data()

def delete_cycle(t_idx):
    st.session_state.cycles.pop(t_idx)
    save_data()

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
        font-size: 80px !important;
        font-weight: 900;
        text-align: center;
        color: #FF4B4B !important;
        margin: 0px;
        line-height: 1;
        font-family: 'Courier New', Courier, monospace;
    }
    .ready-text {
        font-size: 50px !important;
        color: #28a745 !important;
        font-weight: 900;
        text-align: center;
    }
    
    @media (max-width: 600px) {
        .big-timer { font-size: 50px !important; }
        .ready-text { font-size: 35px !important; }
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
    cycles, saved_unit, saved_lang = load_data()
    st.session_state.cycles = cycles
    st.session_state.current_unit = saved_unit
    st.session_state.lang = saved_lang

if 'timer_paused' not in st.session_state:
    st.session_state.timer_paused = False

lang = st.session_state.lang
tr = T[lang]

# --- SIDEBAR ---
with st.sidebar:
    st.header(tr["settings"])
    
    # Language Selector
    selected_lang_name = st.selectbox(tr["lang"], list(LANGUAGES.keys()), index=list(LANGUAGES.values()).index(lang))
    new_lang = LANGUAGES[selected_lang_name]
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        save_data(); st.rerun()

    unit_index = 0 if st.session_state.current_unit == "LBS" else 1
    new_unit = st.radio(tr["unit"], ["LBS", "KG"], index=unit_index)
    theme_choice = st.selectbox(tr["theme"], ["Deep Dark", "Light"])
    
    bg_color = "#0e1117" if theme_choice == "Deep Dark" else "#ffffff"
    text_color = "#ffffff" if theme_choice == "Deep Dark" else "#000000"

    if new_unit != st.session_state.current_unit:
        for cycle in st.session_state.cycles:
            for lift in cycle['lifts']:
                cycle['lifts'][lift]['rm'] = convert_weight(cycle['lifts'][lift]['rm'], new_unit)
                cycle['lifts'][lift]['inc'] = convert_weight(cycle['lifts'][lift]['inc'], new_unit)
            cycle['weight_log'] = [convert_weight(w, new_unit) for w in cycle['weight_log']]
        st.session_state.current_unit = new_unit
        save_data(); st.rerun()

    smallest_plate = st.number_input(f"{tr['small_plate']} ({new_unit})", value=2.5 if new_unit == "LBS" else 1.25, step=0.25)
    
    st.divider()
    if st.button(tr["wipe_data"], type="primary", use_container_width=True):
        st.session_state.cycles = []
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()
    
    st.markdown(f"<div style='text-align: center; opacity: 0.5; font-size: 0.8em; margin-top: 10px;'>{tr['author']}</div>", unsafe_allow_html=True)

st.markdown(f"""
    <style>
    :root {{
        color-scheme: {"dark" if theme_choice == "Deep Dark" else "light"};
    }}
    .stApp, [data-testid="stHeader"], [data-testid="stSidebar"] {{ 
        background-color: {bg_color} !important; 
    }}
    [data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stExpander"] details,
    div[data-testid="stPopoverBody"] {{
        background-color: {bg_color} !important;
    }}
    [data-testid="stMarkdownContainer"] p, 
    [data-testid="stMarkdownContainer"] h1, 
    [data-testid="stMarkdownContainer"] h2, 
    [data-testid="stMarkdownContainer"] h3, 
    [data-testid="stMarkdownContainer"] h4, 
    [data-testid="stMarkdownContainer"] h5, 
    [data-testid="stMarkdownContainer"] h6,
    label span {{
        color: {text_color} !important;
    }}
    </style>
""", unsafe_allow_html=True)

st.title(tr["title"])

# --- CREATE CYCLE ---
u = st.session_state.current_unit
def_inc = ["5", "5", "5", "10", "5"] if u == "LBS" else ["2.5", "2.5", "2.5", "5", "2.5"]

with st.expander(tr["create"], expanded=len(st.session_state.cycles) == 0):
    if 'temp_variant' not in st.session_state:
        st.session_state.temp_variant = "Modern (Deadlift Focus)"
    
    variant_choice = st.radio(tr["variant"], 
                              [tr["modern"], tr["standard"]], 
                              index=0 if st.session_state.temp_variant == "Modern (Deadlift Focus)" else 1,
                              help=tr["var_help"])
    st.session_state.temp_variant = "Modern (Deadlift Focus)" if variant_choice == tr["modern"] else "Standard (Power Clean)"
    
    with st.form("new_cycle_form", clear_on_submit=True):
        c_name = st.text_input(tr["c_name"], placeholder=tr["ph_name"])
        c_weeks = st.slider(tr["duration"], 1, 16, 8)
        c_bw = st.number_input(f"{tr['bw']} ({u})", value=80.0 if u == "KG" else 180.0)
        st.write("---")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1: s_rm, s_inc = st.text_input(f"🏋️ {tr['Squat']} 5RM ({u})", "100"), st.text_input(f"➕ {tr['Squat']} {tr['inc']} ({u})", def_inc[0])
        with col2: b_rm, b_inc = st.text_input(f"💪 {tr['Bench']} 5RM ({u})", "80"), st.text_input(f"➕ {tr['Bench']} {tr['inc']} ({u})", def_inc[1])
        with col3: o_rm, o_inc = st.text_input(f"🥥 {tr['OHP']} 5RM ({u})", "50"), st.text_input(f"➕ {tr['OHP']} {tr['inc']} ({u})", def_inc[2])
        with col4: d_rm, d_inc = st.text_input(f"🔥 {tr['Deadlift']} 5RM ({u})", "140"), st.text_input(f"➕ {tr['Deadlift']} {tr['inc']} ({u})", def_inc[3])
        
        pc_rm, pc_inc = "60", def_inc[4]
        with col5: 
            if st.session_state.temp_variant == "Standard (Power Clean)":
                pc_rm = st.text_input(f"⚡ {tr['Power Clean']} 3RM ({u})", "60")
                pc_inc = st.text_input(f"➕ {tr['Power Clean']} {tr['inc']} ({u})", def_inc[4])
            else:
                st.write(tr["pc_disabled"])

        submit = st.form_submit_button(tr["start"])
        if submit:
            if not c_name.strip(): st.error(tr["err_name"])
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
                st.markdown(f"<p class='start-date-text'>{tr['started']}: {cycle.get('start_date', 'N/A')}</p>", unsafe_allow_html=True)
            
            p_key, w_key = f"p_{t_idx}", f"w_{t_idx}"
            if p_key not in st.session_state: st.session_state[p_key] = False
            if w_key not in st.session_state: st.session_state[w_key] = True

            if h2.button(tr["prog"], key=f"bp_{t_idx}", use_container_width=True):
                st.session_state[p_key] = not st.session_state[p_key]; st.session_state[w_key] = False; st.rerun()
            if h3.button(tr["wgts"], key=f"bw_{t_idx}", use_container_width=True):
                st.session_state[w_key] = not st.session_state[w_key]; st.session_state[p_key] = False; st.rerun()
            
            with h4.popover(tr["del"], use_container_width=True):
                st.button(tr["yes_del"], key=f"conf_del_{t_idx}", type="primary", use_container_width=True, on_click=delete_cycle, args=(t_idx,))

            if st.session_state[w_key]:
                tabs = st.tabs([f"{tr['week']} {i+1} {'✅' if cycle['week_completed_log'][i] else ''}" for i in range(cycle['weeks'])])
                for w_i in range(cycle['weeks']):
                    with tabs[w_i]:
                        t_col1, t_col2 = st.columns([0.3, 0.7])
                        with t_col1: 
                            rest_choice = st.slider(tr["rest"], 1, 10, 3, key=f"rs_{t_idx}_{w_i}")
                            pause_btn = st.button(tr["pause"], key=f"pause_{t_idx}_{w_i}", use_container_width=True)
                            if pause_btn:
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
                        days = [(tr["mon"], 0.90, ["Squat", m_p, monday_pull]),
                                (tr["wed"], 0.80, ["Squat", w_p, "Chin-ups", "Back Extensions"]),
                                (tr["fri"], 1.00, ["Squat", m_p, "Deadlift"])]
                        
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
                                            calc_w = round_to_plates(c_rm * (1.00 if mv == "Power Clean" else pct), smallest_plate)
                                            set_count = 5 if mv == "Power Clean" else (5 if "Monday" in d_name or tr["mon"] == d_name else (2 if "Wednesday" in d_name or tr["wed"] == d_name else 1))
                                            rep_count = 3 if mv == "Power Clean" else 5
                                            rm_label = "3RM" if mv == "Power Clean" else "5RM"
                                        
                                        with st.container(border=True):
                                            st.markdown(f"**{lift_emojis.get(mv, '')} {tr.get(mv, mv)}**")
                                            if not is_accessory:
                                                st.markdown(f"#### {set_count}x{rep_count} @ {format_weight(calc_w)} {u}")
                                                st.caption(f"({int(pct*100)}% of {rm_label})" if mv != "Power Clean" else f"(100% of {rm_label})")
                                                
                                                with st.popover(tr["warmup"], use_container_width=True):
                                                    st.write(f"**{tr['warmup']} - {tr.get(mv, mv)}:**")
                                                    bar_w = 45 if u == "LBS" else 20
                                                    st.write(f"1. {bar_w} {u} x 2x5 ({tr['bar']})")
                                                    w40 = round_to_plates(calc_w * 0.4, smallest_plate)
                                                    st.write(f"2. {format_weight(max(bar_w, w40))} {u} x 5 (40%)")
                                                    w60 = round_to_plates(calc_w * 0.6, smallest_plate)
                                                    st.write(f"3. {format_weight(max(bar_w, w60))} {u} x 3 (60%)")
                                                    w80 = round_to_plates(calc_w * 0.8, smallest_plate)
                                                    st.write(f"4. {format_weight(max(bar_w, w80))} {u} x 2 (80%)")
                                                    w90 = round_to_plates(calc_w * 0.9, smallest_plate)
                                                    st.write(f"5. {format_weight(max(bar_w, w90))} {u} x 1 (90%)")

                                                for s_i in range(set_count):
                                                    cb_key = f"ck_{t_idx}_{w_i}_{d_name}_{mv}_{s_i}"
                                                    prev_state_key = f"prev_{cb_key}"
                                                    rem_key = f"rem_{cb_key}"
                                                    
                                                    if prev_state_key not in st.session_state: st.session_state[prev_state_key] = False
                                                    if rem_key not in st.session_state: st.session_state[rem_key] = 0
                                                    
                                                    checked = st.checkbox(f"Set {s_i+1}", key=cb_key)
                                                    
                                                    if checked and not st.session_state[prev_state_key]:
                                                        st.session_state[prev_state_key] = True
                                                        st.session_state.timer_paused = False
                                                        for k in list(st.session_state.keys()):
                                                            if k.startswith("rem_ck_") and k != rem_key:
                                                                st.session_state[k] = -1
                                                        st.session_state[rem_key] = rest_choice * 60
                                                    
                                                    if checked and st.session_state[rem_key] > 0:
                                                        if not st.session_state.timer_paused:
                                                            is_interrupt = False
                                                            for k, v in st.session_state.items():
                                                                if isinstance(v, bool) and v is True and (k.startswith("btn_v2_") or k.startswith("final_btn_") or k.startswith("conf_del_") or k.startswith("bp_") or k.startswith("bw_")):
                                                                    is_interrupt = True
                                                                    break
                                                                if k.startswith("ck_") and v is True and not st.session_state.get(f"prev_{k}", False):
                                                                    is_interrupt = True
                                                                    break
                                                            
                                                            if not is_interrupt:
                                                                while st.session_state[rem_key] >= 0:
                                                                    m, sc = divmod(st.session_state[rem_key], 60)
                                                                    timer_place.markdown(f'<p class="big-timer">{m:02d}:{sc:02d}</p>', unsafe_allow_html=True)
                                                                    if st.session_state[rem_key] == 0:
                                                                        break
                                                                    time.sleep(1)
                                                                    st.session_state[rem_key] -= 1
                                                                
                                                                if st.session_state[rem_key] == 0:
                                                                    st.components.v1.html("<script>window.parent.notifyEnd();</script>", height=0)
                                                                    timer_place.markdown('<p class="ready-text">READY! 🔥</p>', unsafe_allow_html=True)
                                                                    st.session_state[rem_key] = -1
                                                            else:
                                                                m, sc = divmod(st.session_state[rem_key], 60)
                                                                timer_place.markdown(f'<p class="big-timer">{m:02d}:{sc:02d}</p>', unsafe_allow_html=True)
                                                        else:
                                                            m, sc = divmod(st.session_state[rem_key], 60)
                                                            timer_place.markdown(f'<p class="big-timer">{m:02d}:{sc:02d}</p>', unsafe_allow_html=True)
                                            else:
                                                st.markdown(f"#### {tr['sets_3']}")
                                                st.markdown(tr["bw_fail"] if mv == "Chin-ups" else tr["reps_10_15"])

                                st.divider()
                                if tr["fri"] not in d_name and "Friday" not in d_name:
                                    if (tr["mon"] in d_name or "Monday" in d_name) and cycle.get("variant") == "Standard (Power Clean)":
                                        st.subheader(tr["pc_chk"])
                                        st.caption(tr["pc_help"])
                                        pc_key = f"pc_success_{t_idx}_{w_i}"
                                        cycle['success_log']["Power Clean"][w_i] = st.checkbox(f"⚡ {tr['crushed']} {tr['Power Clean']}", value=cycle['success_log']["Power Clean"][w_i], key=pc_key, on_change=update_success_log, kwargs={'t_idx': t_idx, 'w_i': w_i, 'mv': "Power Clean", 'key': pc_key})
                                        st.write("---")
                                    
                                    if not is_done:
                                        st.button(f"{tr['mark_fin']} - {d_name}", key=f"btn_v2_{d_key}", use_container_width=True, on_click=mark_day_finished, args=(t_idx, d_key))
                                    else: 
                                        st.success(f"✅ {d_name} {tr['fin']}")
                                    
                                else:
                                    st.subheader(tr["fri_chk"])
                                    st.caption(tr["fri_help"])
                                    cc = st.columns(len(moves))
                                    for mi, mv in enumerate(moves):
                                        with cc[mi]:
                                            cb_key = f"success_chk_{t_idx}_{w_i}_{mv}"
                                            cycle['success_log'][mv][w_i] = st.checkbox(f"{tr['crushed']} {tr.get(mv, mv)}", value=cycle['success_log'][mv][w_i], key=cb_key, on_change=update_success_log, kwargs={'t_idx': t_idx, 'w_i': w_i, 'mv': mv, 'key': cb_key})

                                    if not is_done:
                                        st.button(tr["fin_week"], key=f"final_btn_{t_idx}_{w_i}", use_container_width=True, type="primary", on_click=mark_week_finished, args=(t_idx, w_i, d_key))
                                    else: 
                                        st.success(tr["week_fin"])

            if st.session_state[p_key]:
                st.divider()
                weeks_range = list(range(1, cycle['weeks'] + 1))
                c1, c2 = st.columns(2)
                with c1:
                    fig_w = go.Figure()
                    lifts_to_show = ["Squat", "Bench", "OHP", "Deadlift"]
                    if cycle.get("variant") == "Standard (Power Clean)": lifts_to_show.append("Power Clean")
                    colors = {"Squat": "#FF4B4B", "Bench": "#1C83E1", "OHP": "#FFFFFF", "Deadlift": "#FFC300", "Power Clean": "#00FF00"}
                    for lift in lifts_to_show:
                        y_vals = []
                        for w in range(cycle['weeks']):
                            c = sum(1 for prev in range(w) if cycle['success_log'][lift][prev])
                            y_vals.append(cycle['lifts'][lift]['rm'] + (cycle['lifts'][lift]['inc'] * c))
                        fig_w.add_trace(go.Scatter(x=weeks_range, y=y_vals, name=tr.get(lift, lift), line=dict(color=colors.get(lift, "#888"), width=4), mode='lines+markers'))
                    fig_w.update_layout(title=tr["lift_prog"], template="plotly_dark" if theme_choice == "Deep Dark" else "plotly_white")
                    st.plotly_chart(fig_w, use_container_width=True)
                with c2:
                    fig_p = go.Figure()
                    fig_p.add_trace(go.Scatter(x=weeks_range, y=cycle['weight_log'], name="BW", line=dict(color="#00C49A", width=4), mode='lines+markers'))
                    fig_p.update_layout(title=tr["bw_prog"], template="plotly_dark" if theme_choice == "Deep Dark" else "plotly_white")
                    st.plotly_chart(fig_p, use_container_width=True)
else:
    st.info(tr["no_cyc"])
