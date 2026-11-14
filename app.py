import streamlit as st

# === KALKULATOR BMI ===

st.title("Kalkulator BMI")

# Podanie danych przez użytkownika
waga = st.number_input(
    "Podaj swoją wagę w kg:",
    min_value=1.0,
    max_value=300.0,
)

wzrost = st.number_input(
    "Podaj swój wzrost w metrach:",
    min_value=0.5,
    max_value=2.5,

)

# Przycisk obliczania
if st.button("Oblicz BMI"):

    bmi = round(waga / (wzrost ** 2), 2)

    st.write(f"Twoje BMI wynosi: {bmi}")

    # Interpretacja wyniku
    if bmi >= 25.0:
        st.warning("Masz nadwagę")

    elif bmi >= 18.5 and bmi <= 24.9:
        st.success("Waga prawidłowa. Gratulacje!")

    else:
        st.info("Niedowaga")
