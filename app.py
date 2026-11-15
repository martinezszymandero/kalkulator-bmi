
import streamlit as st


# ============================================================
# BODYLAB | BMI & BODY ANALYTICS
# Version 1.3.0
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

.stApp {
    background-color: #F3F6FA;
    color: #172B45;
}

.block-container {
    max-width: 1180px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

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

/* NAGŁÓWKI */

.section-title {
    font-size: 21px;
    font-weight: 750;
    color: #142D4E;
    margin-top: 15px;
    margin-bottom: 15px;
}

/* KARTY */

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
    font-size: 30px;
    font-weight: 800;
    margin-top: 15px;
}

.metric-description {
    color: #8492A6;
    font-size: 12px;
    margin-top: 8px;
    line-height: 1.5;
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

/* ANALIZA */

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

.tip-card {
    background: #FFFFFF;
    border: 1px solid #E5EAF1;
    border-radius: 12px;
    padding: 18px;
    height: 100%;
    color: #43546A;
    font-size: 13px;
    line-height: 1.6;
}

.tip-heading {
    color: #142D4E;
    font-weight: 750;
    font-size: 14px;
    margin-bottom: 8px;
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
        font-size: 25px;
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
    """Renderuje HTML w aplikacji Streamlit."""
    st.html(html)


def format_number(value, decimals=2):
    """Formatuje liczby z polskim separatorem dziesiętnym."""
    return (
        f"{value:,.{decimals}f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


# ============================================================
# 4. SILNIK OBLICZENIOWY BMI
# ============================================================

def calculate_bmi(weight, height_cm):
    """Oblicza BMI na podstawie masy i wzrostu."""

    height_m = height_cm / 100
    return weight / (height_m ** 2)


# ============================================================
# 5. KLASYFIKACJA BMI
# ============================================================

def get_bmi_category(bmi):
    """Klasyfikacja BMI dla osób dorosłych."""

    if bmi < 16:
        return {
            "name": "Znaczna niedowaga",
            "color": "#2563EB",
            "description": (
                "BMI znajduje się znacznie poniżej "
                "standardowego zakresu."
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
                "Wynik wskazuje na niedowagę "
                "według klasyfikacji BMI."
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
                "Wynik wskazuje na otyłość I stopnia."
            )
        }

    elif bmi < 40:
        return {
            "name": "Otyłość II stopnia",
            "color": "#DC2626",
            "description": (
                "Wynik wskazuje na otyłość II stopnia."
            )
        }

    else:
        return {
            "name": "Otyłość III stopnia",
            "color": "#991B1B",
            "description": (
                "Wynik wskazuje na otyłość III stopnia."
            )
        }


# ============================================================
# 6. ZAKRES PRAWIDŁOWEJ MASY CIAŁA
# ============================================================

def calculate_healthy_weight(height_cm):
    """
    Oblicza zakres masy odpowiadający BMI 18,5–24,9.
    """

    height_m = height_cm / 100

    min_weight = 18.5 * (height_m ** 2)
    max_weight = 24.9 * (height_m ** 2)

    return round(min_weight, 1), round(max_weight, 1)


# ============================================================
# 7. ANALIZA RÓŻNICY MASY CIAŁA
# ============================================================

def calculate_weight_difference(weight, min_weight, max_weight):
    """
    Określa odległość aktualnej masy od zakresu
    odpowiadającego BMI 18,5–24,9.
    """

    if weight < min_weight:
        difference = min_weight - weight

        return {
            "value": difference,
            "direction": "poniżej",
            "description": (
                "Tyle kilogramów dzieli aktualną masę "
                "od dolnej granicy zakresu BMI 18,5–24,9."
            )
        }

    elif weight > max_weight:
        difference = weight - max_weight

        return {
            "value": difference,
            "direction": "powyżej",
            "description": (
                "Tyle kilogramów dzieli aktualną masę "
                "od górnej granicy zakresu BMI 18,5–24,9."
            )
        }

    else:
        return {
            "value": 0,
            "direction": "w zakresie",
            "description": (
                "Aktualna masa mieści się w zakresie "
                "odpowiadającym BMI 18,5–24,9."
            )
        }


# ============================================================
# 8. ROZSZERZONA INTERPRETACJA BMI
# ============================================================

def get_bmi_insight(bmi):

    if bmi < 16:
        return (
            "Wynik znajduje się w zakresie znacznej niedowagi. "
            "Tak niskie BMI może wiązać się ze zwiększonym "
            "ryzykiem niedożywienia i innych problemów zdrowotnych. "
            "Warto skonsultować wynik z lekarzem, szczególnie "
            "jeśli niska masa ciała pojawiła się niezamierzenie."
        )

    elif bmi < 17:
        return (
            "BMI wskazuje na umiarkowaną niedowagę. Warto "
            "przyjrzeć się zmianom masy ciała, sposobowi "
            "odżywiania i ogólnemu samopoczuciu. Jeśli masa "
            "spada bez wyraźnej przyczyny, wskazana jest "
            "konsultacja ze specjalistą."
        )

    elif bmi < 18.5:
        return (
            "Wynik wskazuje na łagodną niedowagę. Warto ocenić, "
            "czy aktualna masa ciała jest stabilna oraz czy "
            "dieta dostarcza odpowiedniej ilości energii "
            "i składników odżywczych."
        )

    elif bmi < 25:
        return (
            "Wynik mieści się w standardowym zakresie BMI. "
            "To korzystna informacja, ale nie oznacza automatycznie "
            "pełnej oceny zdrowia. Dla szerszego obrazu warto "
            "uwzględnić obwód talii, skład ciała, aktywność "
            "fizyczną i ogólną kondycję organizmu."
        )

    elif bmi < 27:
        return (
            "Wynik znajduje się w dolnej części zakresu nadwagi. "
            "BMI jest wskaźnikiem przesiewowym i nie rozróżnia "
            "tkanki tłuszczowej od mięśniowej. Warto rozszerzyć "
            "analizę o obwód talii oraz skład ciała."
        )

    elif bmi < 30:
        return (
            "Wynik znajduje się w wyższej części zakresu nadwagi. "
            "Warto przyjrzeć się obwodowi talii, poziomowi "
            "aktywności i zmianom masy ciała w czasie. "
            "Sam wskaźnik BMI nie pozwala określić ilości "
            "tkanki tłuszczowej."
        )

    elif bmi < 35:
        return (
            "BMI wskazuje na otyłość I stopnia. Warto potraktować "
            "wynik jako sygnał do szerszej oceny zdrowia, "
            "uwzględniającej między innymi obwód talii, ciśnienie "
            "tętnicze i parametry metaboliczne. Pomocna może być "
            "konsultacja z lekarzem lub dietetykiem."
        )

    elif bmi < 40:
        return (
            "BMI wskazuje na otyłość II stopnia. Warto skonsultować "
            "wynik z lekarzem i przeprowadzić szerszą ocenę "
            "czynników zdrowotnych. BMI samo w sobie nie określa "
            "indywidualnego stanu zdrowia ani składu ciała."
        )

    else:
        return (
            "BMI wskazuje na otyłość III stopnia. Wskazana jest "
            "konsultacja lekarska i indywidualna ocena stanu "
            "zdrowia. Dalsze postępowanie powinno uwzględniać "
            "całość sytuacji zdrowotnej, a nie wyłącznie "
            "wartość wskaźnika BMI."
        )


# ============================================================
# 9. INTELIGENTNE WSKAZÓWKI
# ============================================================

def get_bmi_tips(bmi):

    if bmi < 18.5:
        return [
            {
                "title": "Ocena masy ciała",
                "text": (
                    "Zwróć uwagę na stabilność masy ciała "
                    "i ewentualne niezamierzone spadki."
                )
            },
            {
                "title": "Odżywianie",
                "text": (
                    "Warto ocenić regularność posiłków "
                    "i podaż energii oraz składników odżywczych."
                )
            },
            {
                "title": "Kolejny krok",
                "text": (
                    "Rozważ konsultację ze specjalistą, "
                    "szczególnie jeśli niska masa ciała "
                    "jest nowym zjawiskiem."
                )
            }
        ]

    elif bmi < 25:
        return [
            {
                "title": "Monitoruj obwód talii",
                "text": (
                    "Obwód talii dostarcza dodatkowych "
                    "informacji o rozmieszczeniu tkanki tłuszczowej."
                )
            },
            {
                "title": "Dbaj o aktywność",
                "text": (
                    "Regularny ruch wspiera kondycję, "
                    "sprawność i zdrowie metaboliczne."
                )
            },
            {
                "title": "Rozszerz analizę",
                "text": (
                    "Rozważ analizę składu ciała, jeśli chcesz "
                    "uzyskać pełniejszy obraz swoich parametrów."
                )
            }
        ]

    else:
        return [
            {
                "title": "Sprawdź obwód talii",
                "text": (
                    "To ważny parametr uzupełniający BMI "
                    "w ocenie rozmieszczenia tkanki tłuszczowej."
                )
            },
            {
                "title": "Przeanalizuj aktywność",
                "text": (
                    "Uwzględnij codzienny ruch, trening "
                    "i czas spędzany w pozycji siedzącej."
                )
            },
            {
                "title": "Rozważ szerszą ocenę",
                "text": (
                    "Konsultacja ze specjalistą może pomóc "
                    "dobrać dalsze kroki do indywidualnej sytuacji."
                )
            }
        ]


# ============================================================
# 10. NAGŁÓWEK APLIKACJI
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
# 11. FORMULARZ DANYCH
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
# 12. OBLICZENIA I ZAPIS WYNIKÓW
# ============================================================

if submitted:

    bmi = calculate_bmi(weight, height)

    category = get_bmi_category(bmi)

    min_weight, max_weight = calculate_healthy_weight(height)

    insight = get_bmi_insight(bmi)

    weight_difference = calculate_weight_difference(
        weight,
        min_weight,
        max_weight
    )

    tips = get_bmi_tips(bmi)

    st.session_state["bmi_result"] = {
        "bmi": round(bmi, 2),
        "weight": weight,
        "height": height,
        "category": category,
        "min_weight": min_weight,
        "max_weight": max_weight,
        "insight": insight,
        "weight_difference": weight_difference,
        "tips": tips
    }


# ============================================================
# 13. DASHBOARD WYNIKÓW
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
    # TRZY KARTY GŁÓWNE
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(3)

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

    with col3:

        difference = result["weight_difference"]

        if difference["direction"] == "w zakresie":
            difference_value = "0,0 kg"
            difference_label = "Masa w zakresie"
        else:
            difference_value = (
                f"{format_number(difference['value'], 1)} kg"
            )
            difference_label = (
                f"{difference['direction']} zakresu"
            )

        render_html(f"""
        <div class="metric-card">

            <div class="metric-label">
                RÓŻNICA DO ZAKRESU BMI
            </div>

            <div class="metric-value">
                {difference_value}
            </div>

            <div class="metric-description">
                {difference_label}
                <br>
                {difference["description"]}
            </div>

        </div>
        """)


    # ========================================================
    # 14. WIZUALIZACJA SKALI BMI
    # ========================================================

    render_html("""
    <div class="section-title">
        Pozycja na skali BMI
    </div>
    """)

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
    # 15. ROZSZERZONA ANALIZA I INTERPRETACJA
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
    # 16. INTELIGENTNE WSKAZÓWKI
    # ========================================================

    render_html("""
    <div class="section-title">
        Rekomendowane kolejne kroki
    </div>
    """)

    tip_columns = st.columns(3)

    for index, tip in enumerate(result["tips"]):

        with tip_columns[index]:

            render_html(f"""
            <div class="tip-card">

                <div class="tip-heading">
                    {tip["title"]}
                </div>

                {tip["text"]}

            </div>
            """)


    # ========================================================
    # 17. OGRANICZENIA BMI
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

        Zakres masy ciała prezentowany przez aplikację
        jest obliczeniem matematycznym opartym na BMI,
        a nie indywidualnym celem terapeutycznym.

    </div>
    """)


# ============================================================
# 18. STOPKA
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
