
import streamlit as st
import textwrap


# ============================================================
# BODYLAB | BMI & BODY ANALYTICS
# Version 1.1
# Python + Streamlit
# ============================================================


# ============================================================
# 1. KONFIGURACJA APLIKACJI
# ============================================================

st.set_page_config(
    page_title="BODYLAB | BMI Analysis",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# 2. KONFIGURACJA CSS
# ============================================================

st.markdown("""
<style>

/* GŁÓWNE TŁO */

.stApp {
    background-color: #F3F6FA;
    color: #172B45;
}

.block-container {
    max-width: 1180px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* UKRYCIE ELEMENTÓW STREAMLIT */

#MainMenu,
footer {
    visibility: hidden;
}

header[data-testid="stHeader"] {
    background: transparent;
}

/* BRANDING */

.brand {
    font-size: 34px;
    font-weight: 850;
    letter-spacing: 2px;
    color: #142D4E;
}

.brand-accent {
    color: #0D9488;
}

.subtitle {
    color: #718096;
    font-size: 12px;
    letter-spacing: 1.5px;
    margin-bottom: 25px;
}

/* NAGŁÓWKI SEKCJI */

.section-title {
    font-size: 21px;
    font-weight: 750;
    color: #142D4E;
    margin-top: 15px;
    margin-bottom: 15px;
}

/* KARTY WYNIKÓW */

.metric-card,
.result-card {
    background: #FFFFFF;
    border: 1px solid #E5EAF1;
    border-radius: 16px;
    padding: 24px;
    min-height: 175px;
    box-shadow: 0 4px 15px rgba(20,45,78,0.04);
    box-sizing: border-box;
    height: 100%;
}

.metric-label {
    color: #718096;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}

.metric-value {
    color: #142D4E;
    font-size: 34px;
    font-weight: 800;
    margin-top: 12px;
}

.metric-description {
    color: #8492A6;
    font-size: 12px;
    margin-top: 5px;
}

.bmi-number {
    color: #142D4E;
    font-size: 62px;
    font-weight: 850;
    line-height: 1.2;
    margin-top: 10px;
}

.category-label {
    font-size: 20px;
    font-weight: 750;
    margin-top: 10px;
}

.result-description {
    color: #718096;
    font-size: 13px;
    line-height: 1.6;
    margin-top: 12px;
}

/* SKALA BMI */

.bmi-scale {
    width: 100%;
    height: 15px;
    border-radius: 20px;
    position: relative;

    background: linear-gradient(
        to right,
        #60A5FA 0%,
        #60A5FA 14%,
        #34D399 14%,
        #34D399 40%,
        #FBBF24 40%,
        #FBBF24 60%,
        #FB923C 60%,
        #FB923C 80%,
        #EF4444 80%,
        #EF4444 100%
    );
}

.bmi-marker {
    position: absolute;
    top: -8px;
    width: 5px;
    height: 31px;
    background: #142D4E;
    border: 2px solid white;
    border-radius: 5px;
    transform: translateX(-50%);
    box-shadow: 0 1px 5px rgba(0,0,0,0.25);
}

.scale-labels {
    position: relative;
    height: 25px;
    margin-top: 12px;
}

.scale-label {
    position: absolute;
    transform: translateX(-50%);
    color: #718096;
    font-size: 11px;
}

.scale-label:first-child {
    transform: none;
}

.scale-label:last-child {
    transform: translateX(-100%);
}

/* KOMENTARZ ANALITYCZNY */

.insight-card {
    background: #FFFFFF;
    border: 1px solid #E5EAF1;
    border-left: 5px solid #0D9488;
    border-radius: 12px;
    padding: 20px;
    margin-top: 12px;
    color: #43546A;
    line-height: 1.7;
}

.insight-heading {
    color: #142D4E;
    font-weight: 750;
    font-size: 16px;
    margin-bottom: 10px;
}

/* INFORMACJE EDUKACYJNE */

.disclaimer {
    background: #E8EEF5;
    border-radius: 12px;
    padding: 18px;
    color: #607086;
    font-size: 12px;
    line-height: 1.7;
    margin-top: 20px;
}

/* STOPKA */

.footer {
    text-align: center;
    color: #94A3B8;
    font-size: 11px;
    padding: 20px;
}

/* PRZYCISKI */

div.stButton > button,
div.stFormSubmitButton > button {
    background: #142D4E;
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 700;
    min-height: 45px;
    transition: background 0.2s ease;
}

div.stButton > button:hover,
div.stFormSubmitButton > button:hover {
    background: #0D9488;
    color: white;
}

/* POLA LICZBOWE */

[data-testid="stNumberInput"] input {
    border-radius: 9px;
}

/* RESPONSYWNOŚĆ */

@media (max-width: 768px) {

    .brand {
        font-size: 28px;
    }

    .bmi-number {
        font-size: 48px;
    }

    .metric-value {
        font-size: 28px;
    }

    .result-card,
    .metric-card {
        padding: 20px;
    }
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# 3. FUNKCJE POMOCNICZE
# ============================================================

def render_html(html):
    """
    Usuwa zbędne wcięcia z HTML
    i przekazuje kod do renderowania w Streamlit.
    """

    st.markdown(
        textwrap.dedent(html).strip(),
        unsafe_allow_html=True
    )


def format_number(value, decimals=2):
    """
    Formatuje liczby z polskim separatorem dziesiętnym.
    """

    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ============================================================
# 4. SILNIK OBLICZENIOWY BMI
# ============================================================

def calculate_bmi(weight, height_cm):
    """
    Oblicza BMI.

    weight – masa ciała w kg
    height_cm – wzrost w cm
    """

    height_m = height_cm / 100

    return weight / (height_m ** 2)


# ============================================================
# 5. KLASYFIKACJA BMI
# ============================================================

def get_bmi_category(bmi):
    """
    Klasyfikacja BMI dla osób dorosłych.
    """

    if bmi < 16:

        return {
            "name": "Znaczna niedowaga",
            "color": "#2563EB",
            "description": (
                "Wynik znajduje się znacznie poniżej "
                "standardowego zakresu BMI."
            )
        }

    elif bmi < 17:

        return {
            "name": "Umiarkowana niedowaga",
            "color": "#3B82F6",
            "description": (
                "Wynik wskazuje na umiarkowaną niedowagę."
            )
        }

    elif bmi < 18.5:

        return {
            "name": "Łagodna niedowaga",
            "color": "#60A5FA",
            "description": (
                "Wynik wskazuje na niedowagę."
            )
        }

    elif bmi < 25:

        return {
            "name": "Masa prawidłowa",
            "color": "#059669",
            "description": (
                "Wynik mieści się w standardowym "
                "zakresie BMI."
            )
        }

    elif bmi < 30:

        return {
            "name": "Nadwaga",
            "color": "#D97706",
            "description": (
                "Wynik wskazuje na nadwagę "
                "według klasyfikacji BMI."
            )
        }

    elif bmi < 35:

        return {
            "name": "Otyłość I stopnia",
            "color": "#EA580C",
            "description": (
                "Wynik wskazuje na otyłość I stopnia "
                "według klasyfikacji BMI."
            )
        }

    elif bmi < 40:

        return {
            "name": "Otyłość II stopnia",
            "color": "#DC2626",
            "description": (
                "Wynik wskazuje na otyłość II stopnia "
                "według klasyfikacji BMI."
            )
        }

    else:

        return {
            "name": "Otyłość III stopnia",
            "color": "#991B1B",
            "description": (
                "Wynik wskazuje na otyłość III stopnia "
                "według klasyfikacji BMI."
            )
        }


# ============================================================
# 6. ZAKRES PRAWIDŁOWEJ MASY CIAŁA
# ============================================================

def calculate_healthy_weight(height_cm):
    """
    Oblicza zakres masy odpowiadający BMI 18.5–24.9.
    """

    height_m = height_cm / 100

    min_weight = 18.5 * (height_m ** 2)
    max_weight = 24.9 * (height_m ** 2)

    return round(min_weight, 1), round(max_weight, 1)


# ============================================================
# 7. INTERPRETACJA WYNIKÓW
# ============================================================

def get_bmi_insight(bmi):

    if bmi < 18.5:

        return (
            "Warto przyjrzeć się podaży energii i składników "
            "odżywczych. Jeżeli niska masa ciała jest "
            "niezamierzona, warto skonsultować ją "
            "ze specjalistą."
        )

    elif bmi < 25:

        return (
            "Wynik mieści się w standardowym zakresie BMI. "
            "Dla pełniejszej oceny warto również uwzględnić "
            "obwód talii, skład ciała i poziom aktywności."
        )

    else:

        return (
            "Warto rozszerzyć analizę o obwód talii, "
            "skład ciała i aktywność fizyczną. BMI nie "
            "rozróżnia tkanki tłuszczowej od mięśniowej."
        )


# ============================================================
# 8. NAGŁÓWEK APLIKACJI
# ============================================================

render_html("""
<div class="brand">
    🧬 BODY<span class="brand-accent">LAB</span>
</div>

<div class="subtitle">
    BODY COMPOSITION & HEALTH ANALYTICS
    &nbsp; | &nbsp; BMI ANALYSIS
</div>
""")

st.divider()


# ============================================================
# 9. FORMULARZ DANYCH
# ============================================================

render_html("""
<div class="section-title">
    Twoje parametry
</div>
""")

with st.form("bmi_form"):

    col1, col2 = st.columns(2)

    with col1:

        weight = st.number_input(
            "Masa ciała (kg)",
            min_value=1.0,
            max_value=300.0,
            value=70.0,
            step=0.1,
            format="%.2f"
        )

    with col2:

        height = st.number_input(
            "Wzrost (cm)",
            min_value=100.0,
            max_value=250.0,
            value=175.0,
            step=1.0,
            format="%.2f"
        )

    submitted = st.form_submit_button(
        "ANALIZUJ MOJE BMI",
        use_container_width=True
    )


# ============================================================
# 10. OBLICZENIA I ZAPIS WYNIKÓW
# ============================================================

if submitted:

    bmi = calculate_bmi(weight, height)

    category = get_bmi_category(bmi)

    min_weight, max_weight = calculate_healthy_weight(height)

    insight = get_bmi_insight(bmi)

    st.session_state["bmi_result"] = {

        "bmi": round(bmi, 2),

        "weight": weight,

        "height": height,

        "category": category,

        "min_weight": min_weight,

        "max_weight": max_weight,

        "insight": insight

    }


# ============================================================
# 11. DASHBOARD WYNIKÓW
# ============================================================

result = st.session_state.get("bmi_result")

if result:

    bmi = result["bmi"]

    category = result["category"]

    st.divider()

    render_html("""
    <div class="section-title">
        Twoje wyniki analizy
    </div>
    """)

    # --------------------------------------------------------
    # DWIE GŁÓWNE KARTY
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        bmi_formatted = format_number(bmi, 2)

        render_html(f"""
        <div class="result-card">

            <div class="metric-label">
                TWÓJ WSKAŹNIK BMI
            </div>

            <div class="bmi-number">
                {bmi_formatted}
            </div>

            <div class="category-label"
                 style="color: {category["color"]};">

                {category["name"]}

            </div>

            <div class="result-description">
                {category["description"]}
            </div>

        </div>
        """)

    with col2:

        min_weight = format_number(result["min_weight"], 1)

        max_weight = format_number(result["max_weight"], 1)

        render_html(f"""
        <div class="metric-card">

            <div class="metric-label">
                PRAWIDŁOWY ZAKRES MASY CIAŁA
            </div>

            <div class="metric-value">
                {min_weight}–{max_weight}
            </div>

            <div class="metric-description">
                kg | Zakres odpowiadający BMI 18,5–24,9
            </div>

        </div>
        """)


    # ========================================================
    # 12. WIZUALIZACJA SKALI BMI
    # ========================================================

    render_html("""
    <div class="section-title">
        Pozycja na skali BMI
    </div>
    """)

    # Skala obejmuje wartości od BMI 15 do BMI 40.

    marker_position = ((bmi - 15) / 25) * 100

    marker_position = max(0, min(100, marker_position))

    scale_thresholds = [
        (15, "15"),
        (18.5, "18,5"),
        (25, "25"),
        (30, "30"),
        (35, "35"),
        (40, "40+")
    ]

    labels_html = ""

    for value, label in scale_thresholds:

        position = ((value - 15) / 25) * 100

        labels_html += f"""
        <span class="scale-label"
              style="left: {position}%;">
            {label}
        </span>
        """

    render_html(f"""
    <div style="padding: 15px 5px 25px 5px;">

        <div class="bmi-scale">

            <div class="bmi-marker"
                 style="left: {marker_position}%;">

            </div>

        </div>

        <div class="scale-labels">

            {labels_html}

        </div>

    </div>
    """)


    # ========================================================
    # 13. KOMENTARZ ANALITYCZNY
    # ========================================================

    render_html("""
    <div class="section-title">
        Analiza i interpretacja
    </div>
    """)

    render_html(f"""
    <div class="insight-card">

        <div class="insight-heading">
            {category["name"]}
        </div>

        {result["insight"]}

    </div>
    """)


    # ========================================================
    # 14. OGRANICZENIA BMI
    # ========================================================

    with st.expander("Dowiedz się więcej o wskaźniku BMI"):

        st.markdown("""
        ### Czym jest BMI?

        BMI (Body Mass Index) to wskaźnik masy ciała
        obliczany na podstawie masy i wzrostu.

        Jest narzędziem przesiewowym, a nie diagnozą
        medyczną.

        ### Czego BMI nie określa?

        - Procentowej zawartości tkanki tłuszczowej.
        - Ilości masy mięśniowej.
        - Rozmieszczenia tkanki tłuszczowej.
        - Indywidualnego stanu zdrowia.

        ### Ograniczenia wskaźnika

        U osób o dużej masie mięśniowej BMI może
        zawyżać ocenę nadmiernej masy ciała.

        BMI nie powinno być interpretowane w oderwaniu
        od pozostałych parametrów organizmu.

        Klasyfikacja przedstawiona w BODYLAB dotyczy
        osób dorosłych. U dzieci i młodzieży stosuje
        się interpretację uwzględniającą wiek i płeć.
        """)

    render_html("""
    <div class="disclaimer">

        <b>INFORMACJA EDUKACYJNA</b>

        <br><br>

        BODYLAB jest narzędziem edukacyjnym i analitycznym.

        Wyniki nie stanowią diagnozy medycznej ani
        indywidualnej porady lekarskiej.

        BMI jest jednym z wielu parametrów wykorzystywanych
        do oceny masy ciała i nie stanowi pełnej oceny
        stanu zdrowia.

    </div>
    """)


# ============================================================
# 15. STOPKA
# ============================================================

st.divider()

render_html("""
<div class="footer">

    🧬 BODYLAB © 2026

    <br>

    BODY COMPOSITION & HEALTH ANALYTICS

    <br><br>

    Educational tool – not a medical diagnostic system.

</div>
""")
