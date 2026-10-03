import json
from google import genai
from google.genai import types
from PIL import Image
import streamlit as st

st.set_page_config(
    page_title="Valve Calibration Check", page_icon="⚙️", layout="wide"
)

# Переклади інтерфейсу
LANG = {
    "UK": {
        "title": "⚙️ Перевірка калібрування клапанів",
        "lang_select": "Мова / Język / Language",
        "api_key": "Gemini API Key",
        "card1": "📸 Фото 1 (Картка фактичних вимірів)",
        "card2": "📸 Фото 2 (Картка толеранцій)",
        "screen": "🖥️ Фото 3 (Екран монітора)",
        "btn": "Розпочати порівняння",
        "t1": "1. Перевірка толеранцій (Екран vs Картка 2)",
        "t2": "2. Перевірка фактичного виміру (Екран vs Картка 1)",
        "param": "Параметр",
        "screen_val": "Значення на екрані",
        "card_val": "Значення на картці",
        "status": "Результат",
        "err_upload": "Будь ласка, завантажте всі 3 фото та вкажіть API Key.",
    },
    "PL": {
        "title": "⚙️ Weryfikacja kalibracji zaworów",
        "lang_select": "Мова / Język / Language",
        "api_key": "Gemini API Key",
        "card1": "📸 Zdjęcie 1 (Karta pomiarów rzeczywistych)",
        "card2": "📸 Zdjęcie 2 (Karta tolerancji)",
        "screen": "🖥️ Zdjęcie 3 (Ekran monitora)",
        "btn": "Rozpocznij porównanie",
        "t1": "1. Porównanie tolerancji (Ekran vs Karta 2)",
        "t2": "2. Porównanie pomiaru rzeczywistego (Ekran vs Karta 1)",
        "param": "Parametr",
        "screen_val": "Ekran",
        "card_val": "Karta",
        "status": "Wynik",
        "err_upload": "Proszę przesłać wszystkie 3 zdjęcia i wprowadzić klucz API.",
    },
    "EN": {
        "title": "⚙️ Valve Calibration Verification",
        "lang_select": "Мова / Język / Language",
        "api_key": "Gemini API Key",
        "card1": "📸 Photo 1 (Actual Measurements Card)",
        "card2": "📸 Photo 2 (Tolerances Card)",
        "screen": "🖥️ Photo 3 (Monitor Screen)",
        "btn": "Run Analysis",
        "t1": "1. Tolerance Check (Screen vs Card 2)",
        "t2": "2. Actual Measurement Check (Screen vs Card 1)",
        "param": "Parameter",
        "screen_val": "Screen Value",
        "card_val": "Card Value",
        "status": "Status",
        "err_upload": "Please upload all 3 photos and provide an API Key.",
    },
}

# Вибір мови в боковому меню
selected_lang = st.sidebar.selectbox("Language / Мова / Język", ["UK", "PL", "EN"])
txt = LANG[selected_lang]

st.title(txt["title"])

# Введення API ключа
api_key_input = "AQ.Ab8RN6JIedCxGgZl5Qvdhg_xSFgJ1NV678wQplpHy4BCnNvjZw"

# Завантаження фотографій
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
    # Видаляємо випадкові пробіли на початку чи в кінці ключа
    clean_key = key.strip()
    client = genai.Client(api_key=clean_key)

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

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[i1, i2, i3, prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        ),
    )
    return json.loads(response.text)


# Перевірка перед запуском
if st.button(txt["btn"], type="primary", use_container_width=True):
    if not api_key_input or len(api_key_input.strip()) < 10:
        st.error(
            "Будь ласка, перевірте API Key у боковому меню (значок >> зверху)."
        )
    elif not (img1_file and img2_file and img3_file):
        st.error("Будь ласка, завантажте всі 3 фотографії.")
    else:
        with st.spinner("Аналіз зображень через Gemini AI..."):
            try:
                st.session_state["analysis_result"] = analyze_images(
                    img1_file, img2_file, img3_file, api_key_input
                )
            except Exception as e:
                st.error(f"Помилка авторизації або обробки: {str(e)}")
# Копірайт
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>© Roman BERNYK</div>",
    unsafe_allow_html=True,
)
