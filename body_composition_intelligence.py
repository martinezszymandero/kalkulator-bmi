"""
BODYLAB – Body Composition Intelligence, v1.0
Independent rule-based interpretation of BMI, WHtR and WHR.
Educational only; not a medical diagnosis.
"""

import math

MODULE_VERSION = "1.0"

BMI_BANDS = (
    (16.0, "Znaczna niedowaga"),
    (17.0, "Umiarkowana niedowaga"),
    (18.5, "Łagodna niedowaga"),
    (25.0, "Masa prawidłowa"),
    (30.0, "Nadwaga"),
    (35.0, "Otyłość I stopnia"),
    (40.0, "Otyłość II stopnia"),
    (math.inf, "Otyłość III stopnia"),
)

WHR_THRESHOLDS = {"male": 0.90, "female": 0.85}

LIMITATIONS = [
    "BMI nie rozróżnia tkanki tłuszczowej od masy mięśniowej ani nie pokazuje rozmieszczenia tkanki tłuszczowej.",
    "WHtR i WHR są wskaźnikami przesiewowymi, a nie diagnozą ani pełną oceną składu ciała.",
    "Interpretacja WHR wymaga punktu odniesienia; w tym module zależy on od podanej płci.",
    "Wyniki mogą być mniej miarodajne m.in. u osób bardzo umięśnionych, w ciąży lub w okresie wzrastania.",
]


def _number(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) and result > 0 else None


def _sex(value):
    if not isinstance(value, str):
        return None
    aliases = {
        "male": "male", "m": "male", "man": "male",
        "mezczyzna": "male", "mężczyzna": "male",
        "female": "female", "f": "female", "woman": "female",
        "kobieta": "female",
    }
    return aliases.get(value.strip().lower())


def _bmi_result(value):
    if value is None:
        return {"value": None, "status": "insufficient_data",
                "label": "Brak danych",
                "interpretation": "Nie podano prawidłowej wartości BMI."}
    for upper, label in BMI_BANDS:
        if value < upper:
            break
    return {"value": round(value, 2), "status": "available",
            "label": label,
            "interpretation": f"Wartość BMI mieści się w kategorii: {label.lower()}."}


def _whtr_result(value, bmi):
    if value is None:
        return {"value": None, "status": "insufficient_data",
                "label": "Brak danych",
                "interpretation": "Nie podano prawidłowej wartości WHtR."}
    if bmi is not None and bmi >= 35:
        return {
            "value": round(value, 3), "status": "limited",
            "label": "Ograniczona interpretacja",
            "interpretation": (
                "Przy BMI równym lub wyższym niż 35 BODYLAB nie stosuje "
                "standardowej klasyfikacji WHtR. Wynik pozostaje widoczny, "
                "ale nie jest uwzględniany w ocenie zgodności wskaźników. "
                "Wskazana jest indywidualna ocena specjalistyczna."
            ),
        }
    elevated = value >= 0.5
    return {
        "value": round(value, 3), "status": "available",
        "label": ("Na poziomie lub powyżej orientacyjnego progu 0,50"
                  if elevated else "Poniżej orientacyjnego progu 0,50"),
        "interpretation": (
            "WHtR osiąga lub przekracza często stosowany próg 0,50."
            if elevated else
            "WHtR pozostaje poniżej często stosowanego progu 0,50."
        ),
        "reference_threshold": 0.5,
    }


def _whr_result(value, sex):
    if value is None:
        return {"value": None, "status": "insufficient_data",
                "label": "Brak danych",
                "interpretation": "Nie podano prawidłowej wartości WHR."}
    if sex is None:
        return {"value": round(value, 3), "status": "needs_reference",
                "label": "Brak punktu odniesienia",
                "interpretation": "Do zastosowania orientacyjnego progu WHR potrzebna jest informacja o płci."}
    threshold = WHR_THRESHOLDS[sex]
    elevated = value >= threshold
    return {
        "value": round(value, 3), "status": "available",
        "label": ("Na poziomie lub powyżej orientacyjnego progu"
                  if elevated else "Poniżej orientacyjnego progu"),
        "interpretation": (
            f"WHR osiąga lub przekracza często stosowany próg {threshold:.2f}."
            if elevated else
            f"WHR pozostaje poniżej często stosowanego progu {threshold:.2f}."
        ),
        "reference_threshold": threshold,
    }


def analyze_body_composition(bmi, whtr, whr, sex=None):
    """Return a structured interpretation of BMI, WHtR and WHR.

    bmi: kg/m²; whtr: waist/height; whr: waist/hip.
    sex: 'male' or 'female' (Polish aliases are also accepted) for WHR context.
    Invalid or missing values are never treated as zero.
    """
    bmi_v, whtr_v, whr_v = _number(bmi), _number(whtr), _number(whr)
    sex_v = _sex(sex)

    metrics = {
        "bmi": _bmi_result(bmi_v),
        "whtr": _whtr_result(whtr_v, bmi_v),
        "whr": _whr_result(whr_v, sex_v),
    }
    available = [k for k, v in metrics.items() if v["status"] == "available"]

    central = []
    whtr_interpretable = whtr_v is not None and not (bmi_v is not None and bmi_v >= 35)
    if whtr_interpretable:
        central.append(whtr_v >= 0.5)
    if whr_v is not None and sex_v is not None:
        central.append(whr_v >= WHR_THRESHOLDS[sex_v])

    signals = []
    if bmi_v is not None and bmi_v >= 25:
        signals.append("BMI znajduje się w kategorii nadwagi lub otyłości.")
    elif bmi_v is not None and bmi_v < 18.5:
        signals.append("BMI znajduje się poniżej zakresu masy prawidłowej.")
    if whtr_interpretable and whtr_v >= 0.5:
        signals.append("WHtR osiąga lub przekracza orientacyjny próg 0,50.")
    if whr_v is not None and sex_v and whr_v >= WHR_THRESHOLDS[sex_v]:
        signals.append("WHR osiąga lub przekracza orientacyjny próg dla podanej płci.")

    if not available:
        status, consistency = "insufficient_data", "insufficient_data"
        summary = "Brakuje prawidłowych danych do interpretacji. Uzupełnij co najmniej jeden wskaźnik."
    elif len(available) == 1:
        status, consistency = "partial", "not_assessed"
        summary = "Dostępny jest tylko jeden sklasyfikowany wskaźnik. Interpretacja jest ograniczona."
    else:
        status = "available"
        if len(central) == 2 and all(central):
            consistency = "convergent_signal"
            summary = "WHtR i WHR wskazują zgodnie na wartości na poziomie lub powyżej zastosowanych progów orientacyjnych. BMI należy interpretować razem z nimi."
        elif len(central) == 2 and not any(central):
            consistency = "no_elevated_central_signal"
            summary = "WHtR i WHR pozostają poniżej zastosowanych progów orientacyjnych. Nie jest to pełna ocena zdrowia."
        elif len(central) == 2:
            consistency = "mixed_central_signal"
            summary = "WHtR i WHR dają niejednoznaczny obraz: jeden osiąga próg orientacyjny, a drugi pozostaje poniżej niego."
        else:
            consistency = "partial_central_assessment"
            summary = "Dostępne dane pozwalają na częściową interpretację. Do porównania obu wskaźników obwodowych potrzebne są WHtR i WHR z punktem odniesienia."

    if bmi_v is not None and central:
        if (bmi_v >= 25) != any(central):
            signals.append("BMI i wskaźniki obwodowe nie dają w pełni zgodnego obrazu; nie należy opierać oceny na jednym wskaźniku.")
    if not signals and available:
        signals.append("Dostępne dane nie wskazują na przekroczenie zastosowanych progów orientacyjnych.")

    return {
        "module": "body_composition_intelligence",
        "version": MODULE_VERSION,
        "status": status,
        "overall_summary": summary,
        "consistency": consistency,
        "metrics": metrics,
        "signals": signals,
        "available_metrics": available,
        "limitations": LIMITATIONS.copy(),
        "disclaimer": "To edukacyjna interpretacja wskaźników, a nie diagnoza medyczna. Progi są orientacyjne i nie uwzględniają wszystkich indywidualnych uwarunkowań.",
    }


__all__ = ["analyze_body_composition", "MODULE_VERSION"]
