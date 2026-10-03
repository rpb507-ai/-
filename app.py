import json
from PIL import Image
import google.generativeai as genai
import streamlit as st

st.set_page_config(
    page_title="Valve Calibration Check", page_icon="⚙️", layout="wide"
)

# 1. Отримання ключа зі Streamlit Secrets або з бічного меню (якщо Secrets порожні)
api_key = ""
if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
    api_key = st.secrets["GEMINI_API_KEY"]

# Якщо ключ не налаштований у Secrets, показуємо поле введення в бічному меню
if not api_key:
    api_key = st.sidebar.text_input("Gemini API Key", type="password")

# Очищення ключа від можливих пробілів чи лапок
clean_api_key = api_key.strip().strip("'\"").strip() if api_key else ""

# Переклади
LANG = {
    "UK": {
        "title": "⚙️ Перевірка калібрування клапанів",
        "card1": "📸 Фото 1 (Картка фактичних вимірів)",
        "card2": "📸 Фото 2 (Картка толеранцій)",
        "screen": "🖥️️ Фото 3 (Екран монітора)",
        "btn": "Розпочати порівняння",
        "t1": "1. Перевірка толеранцій (Екран vs Картка 2)",
        "t2": "2. Перевірка фактичного виміру (Екран vs Картка 1)",
        "screen_val": "Значення на екрані",
        "card_val": "Значення на картці",
        "err_key": "Помилка: Не вказано API Key. Додайте його в Secrets або у бічному меню.",
        "err_files": "Будь ласка, завантажте всі 3 фотографії.",
    },
    "PL": {
        "title": "⚙️ Weryfikacja kalibracji zaworów",
        "card1": "📸 Zdjęcie 1 (Karta pomiarów rzeczywistych)",
        "card2": "📸 Zdjęcie 2 (Karta tolerancji)",
        "screen": "🖥️ Zdjęcie 3 (Ekran monitora)",
        "btn": "Rozpocznij porównanie",
        "t1": "1. Porównanie tolerancji (Ekran vs Karta 2)",
        "t2": "2. Porównanie pomiaru rzeczywistego (Ekran vs Karta 1)",
        "screen_val": "Ekran",
        "card_val": "Karta",
        "err_key": "Błąd: Brak klucza API w Secrets lub w panelu bocznym.",
        "err_files": "Proszę przesłać wszystkie 3 zdjęcia.",
    },
    "EN": {
        "title": "⚙️ Valve Calibration Verification",
        "card1": "📸 Photo 1 (Actual Measurements Card)",
        "card2": "📸 Photo 2 (Tolerances Card)",
        "screen": "🖥️ Photo 3 (Monitor Screen)",
        "btn": "Run Analysis",
        "t1": "1. Tolerance Check (Screen vs Card 2)",
        "t2": "2. Actual Measurement Check (Screen vs Card 1)",
        "screen_val": "Screen Value",
        "card_val": "Card Value",
        "err_key": "Error: API Key is missing. Add it to Secrets or the sidebar.",
        "err_files": "Please upload all 3 photos.",
    },
}

selected_lang = st.sidebar.selectbox("Language / Мова / Język", ["UK", "PL", "EN"])
txt = LANG[selected_lang]

st.title(txt["title"])

col1, col2, col3 = st.columns(3)
with col1:
    img1_file = st.file_uploader(txt["card1"], type=["jpg", "jpeg", "png"])
    if img1_file:
        st.image(img1_file, use_container_width=True)

with col2:
    img2_file = st.file_uploader(txt["card2"], type=["jpg", "jpeg", "png"])
    if img2_file:
        st.image(img2_file, use_container_width=True)

with col3:
    img3_file = st.file_uploader(txt["screen"], type=["jpg", "jpeg", "png"])
    if img3_file:
        st.image(img3_file, use_container_width=True)


def analyze_images(img1, img2, img3, key):
    genai.configure(api_key=key)
    model = genai.GenerativeModel("gemini-3.5-flash")

    prompt = """
    You are an industrial quality control expert. Compare measurement data from three images:
    - Image 1: Calibration card with actual measurements (Wymiar rzeczywisty) and "OK" range limits (OK wymiar ponizej to OK wymiar powyzej).
    - Image 2: Reference card with nominal dimensions and tolerances (Tolerancja ±X).
    - Image 3: Monitor screen showing current calibration readings (Opis, Pomiar, Dolna tolerancja, Gorna tolerancja).

    Tasks:
    1. Match parameters logically by name between Image 3 and Cards.
    2. Task 1: Compare Image 3 "Dolna tolerancja" and "Gorna tolerancja" against Image 2 "Tolerancja".
    3. Task 2: Check if Image 3 "Pomiar" falls within the "OK" range from Image 1 (between OK min and OK max).

    Return ONLY a JSON object formatted as follows:
    {
        "task1": [
            {"parameter": "Parameter name", "screen_val": "Dolna: -0.15, Gorna: 0.15", "card_val": "±0.15", "match": true}
        ],
        "task2": [
            {"parameter": "Parameter name", "screen_val": "30.017", "card_val": "30.013 - 30.033", "match": true}
        ]
    }
    """

    i1 = Image.open(img1)
    i2 = Image.open(img2)
    i3 = Image.open(img3)

    response = model.generate_content(
        [i1, i2, i3, prompt],
        generation_config={"response_mime_type": "application/json"},
    )
    return json.loads(response.text)


if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None

if st.button(txt["btn"], type="primary", use_container_width=True):
    if not clean_api_key or len(clean_api_key) < 10:
        st.error(txt["err_key"])
    elif not (img1_file and img2_file and img3_file):
        st.error(txt["err_files"])
    else:
        with st.spinner("Аналіз зображень через Gemini AI..."):
            try:
                st.session_state["analysis_result"] = analyze_images(
                    img1_file, img2_file, img3_file, clean_api_key
                )
            except Exception as e:
                st.error(f"Помилка обробки: {str(e)}")

if st.session_state["analysis_result"]:
    res = st.session_state["analysis_result"]

    st.subheader(txt["t1"])
    for item in res.get("task1", []):
        color = "#155724" if item["match"] else "#721c24"
        bg = "#d4edda" if item["match"] else "#f8d7da"
        status_text = "OK" if item["match"] else "NOK"

        st.markdown(
            f"""
        <div style="background-color:{bg}; padding:10px; border-radius:5px; margin-bottom:5px; color:{color}; font-weight:bold;">
            <b>{item['parameter']}</b><br>
            {txt['screen_val']}: {item['screen_val']} | {txt['card_val']}: {item['card_val']} &nbsp; <b>[{status_text}]</b>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.subheader(txt["t2"])
    for item in res.get("task2", []):
        color = "#155724" if item["match"] else "#721c24"
        bg = "#d4edda" if item["match"] else "#f8d7da"
        status_text = "OK" if item["match"] else "NOK"

        st.markdown(
            f"""
        <div style="background-color:{bg}; padding:10px; border-radius:5px; margin-bottom:5px; color:{color}; font-weight:bold;">
            <b>{item['parameter']}</b><br>
            {txt['screen_val']}: {item['screen_val']} | {txt['card_val']}: {item['card_val']} &nbsp; <b>[{status_text}]</b>
        </div>
        """,
            unsafe_allow_html=True,
        )

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>© Roman Bernyk</div>",
    unsafe_allow_html=True,
)
