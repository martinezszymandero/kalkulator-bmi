
"""
BODYLAB Smart Body Analysis 2.2
Independent analysis engine. Pure Python; no Streamlit/Supabase dependencies.

This module provides transparent, rule-based observations. It is not a medical
diagnostic tool and does not assign a composite "body score".
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from math import isfinite
from typing import Any

from progress_intelligence import analyze_progress


VERSION = "2.2"


def _number(value: Any, field: str, *, minimum: float | None = None) -> float | None:
    """Return a finite float or None; raise ValueError for invalid supplied data."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a number, not a boolean.")
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be numeric.") from None
    if not isfinite(result):
        raise ValueError(f"{field} must be finite.")
    if minimum is not None and result < minimum:
        raise ValueError(f"{field} must be at least {minimum}.")
    return result


def _normalise_sex(value: Any) -> str | None:
    if value is None or value == "":
        return None
    text = str(value).strip().lower()
    if text in {"m", "male", "man", "mężczyzna", "mezczyzna"}:
        return "male"
    if text in {"f", "female", "woman", "kobieta"}:
        return "female"
    raise ValueError("sex must identify male or female, or be left empty.")


def _parse_date(value: Any) -> datetime | None:
    """
    Parse a measurement date and normalize it to timezone-aware UTC.

    Naive dates/timestamps are treated as UTC because database timestamps
    are expected to represent a single shared timeline. This guarantees
    that mixed ISO strings, date objects, and datetime objects can be
    sorted and subtracted safely.
    """
    if value is None or value == "":
        return None

    parsed: datetime | None = None

    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime.combine(value, datetime.min.time())
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    if parsed is None:
        return None

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def _finding(title: str, description: str, level: str = "info") -> dict[str, str]:
    return {"title": title, "description": description, "level": level}


def _history_rows(history: Any) -> list[dict[str, Any]]:
    if history is None:
        return []
    if not isinstance(history, (list, tuple)):
        raise ValueError("history must be a list of measurement dictionaries.")

    rows = []
    for index, row in enumerate(history):
        if not isinstance(row, dict):
            raise ValueError(f"history[{index}] must be a dictionary.")

        parsed = _parse_date(row.get("created_at"))
        if parsed is None:
            continue

        clean = {"created_at": parsed}
        for key in ("weight", "bmi", "waist"):
            clean[key] = _number(
                row.get(key),
                f"history[{index}].{key}",
                minimum=0
            )
        rows.append(clean)

    return sorted(rows, key=lambda item: item["created_at"])


def _body_metrics(
    profile: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, str]], list[dict[str, str]]]:

    bmi = _number(profile.get("bmi"), "bmi", minimum=0)
    whtr = _number(profile.get("whtr"), "whtr", minimum=0)
    whr = _number(profile.get("whr"), "whr", minimum=0)
    sex = _normalise_sex(profile.get("sex"))

    findings: list[dict[str, str]] = []
    strengths: list[dict[str, str]] = []
    attention: list[dict[str, str]] = []

    if bmi is not None:
        if bmi < 18.5:
            findings.append(_finding(
                "BMI poniżej typowego zakresu",
                "BMI jest poniżej 18,5. Sam wskaźnik nie wyjaśnia przyczyny ani składu ciała.",
                "attention"
            ))
            attention.append(_finding(
                "BMI poniżej typowego zakresu",
                "Warto interpretować wynik w kontekście samopoczucia, historii masy ciała i innych danych.",
                "attention"
            ))

        elif bmi < 25:
            findings.append(_finding(
                "BMI w typowym zakresie",
                "BMI mieści się w przedziale 18,5–24,9. BMI nie rozróżnia tkanki tłuszczowej od mięśniowej.",
                "positive"
            ))
            strengths.append(_finding(
                "BMI w typowym zakresie",
                "Aktualny wskaźnik BMI mieści się w przedziale 18,5–24,9.",
                "positive"
            ))

        elif bmi < 30:
            findings.append(_finding(
                "BMI powyżej typowego zakresu",
                "BMI mieści się w przedziale 25–29,9. Wskaźnik nie określa samodzielnie składu ciała.",
                "attention"
            ))
            attention.append(_finding(
                "BMI powyżej typowego zakresu",
                "Warto zestawić BMI z obwodem talii i pozostałymi informacjami.",
                "attention"
            ))

        else:
            findings.append(_finding(
                "BMI w zakresie otyłości według klasyfikacji BMI",
                "BMI wynosi co najmniej 30. To klasyfikacja wskaźnika, a nie diagnoza stanu zdrowia.",
                "attention"
            ))
            attention.append(_finding(
                "Podwyższone BMI",
                "Wynik warto omówić w szerszym kontekście zdrowotnym; BMI nie jest diagnozą.",
                "attention"
            ))

    if whtr is not None:
        if bmi is not None and bmi >= 35:
            findings.append(_finding(
                "WHtR pominięty w interpretacji",
                "W BODYLAB interpretacja WHtR jest ograniczana przy BMI ≥ 35; wynik nie jest tu klasyfikowany."
            ))

        elif whtr < 0.4:
            findings.append(_finding(
                "WHtR poniżej typowego przedziału",
                "WHtR jest niższy niż 0,40. Interpretuj go razem z pozostałymi pomiarami."
            ))

        elif whtr < 0.5:
            findings.append(_finding(
                "WHtR w typowym przedziale",
                "WHtR mieści się w przedziale 0,40–0,49.",
                "positive"
            ))
            strengths.append(_finding(
                "WHtR w typowym przedziale",
                "Wartość WHtR mieści się w przedziale 0,40–0,49.",
                "positive"
            ))

        elif whtr < 0.6:
            findings.append(_finding(
                "Podwyższony WHtR",
                "WHtR mieści się w przedziale 0,50–0,59. Jest to wskaźnik przesiewowy, nie diagnoza.",
                "attention"
            ))
            attention.append(_finding(
                "Podwyższony WHtR",
                "Obwód talii w relacji do wzrostu zasługuje na uwagę i obserwację w czasie.",
                "attention"
            ))

        else:
            findings.append(_finding(
                "Wysoki WHtR",
                "WHtR wynosi co najmniej 0,60. Wskaźnik nie stanowi samodzielnej diagnozy.",
                "attention"
            ))
            attention.append(_finding(
                "Wysoki WHtR",
                "Warto zweryfikować pomiar i rozważyć konsultację z profesjonalistą.",
                "attention"
            ))

    if whr is not None and sex is not None:
        threshold = 0.90 if sex == "male" else 0.85

        if whr >= threshold:
            findings.append(_finding(
                "WHR powyżej przyjętego progu",
                f"WHR wynosi co najmniej {threshold:.2f} dla wskazanej płci. To wskaźnik przesiewowy, nie diagnoza.",
                "attention"
            ))
            attention.append(_finding(
                "WHR powyżej przyjętego progu",
                "Warto zestawić wynik z WHtR, obwodem talii i historią pomiarów.",
                "attention"
            ))

        else:
            findings.append(_finding(
                "WHR poniżej przyjętego progu",
                f"WHR jest niższy niż {threshold:.2f} dla wskazanej płci.",
                "positive"
            ))
            strengths.append(_finding(
                "WHR poniżej przyjętego progu",
                "Aktualny WHR znajduje się poniżej przyjętego progu dla wskazanej płci.",
                "positive"
            ))

    elif whr is not None:
        findings.append(_finding(
            "WHR bez klasyfikacji zależnej od płci",
            "Podano WHR, ale brakuje rozpoznawalnej wartości płci; nie zastosowano progu."
        ))

    if bmi is not None and whtr is not None and bmi < 35:
        if bmi >= 25 and whtr < 0.5:
            findings.append(_finding(
                "Rozbieżność BMI i WHtR",
                "BMI jest podwyższone, a WHtR pozostaje poniżej 0,50. Wskaźniki opisują różne aspekty i nie powinny być traktowane zamiennie."
            ))

        elif bmi < 25 and whtr >= 0.5:
            findings.append(_finding(
                "Rozbieżność BMI i WHtR",
                "BMI jest poniżej 25, a WHtR wynosi co najmniej 0,50. Samo BMI może nie opisywać rozmieszczenia tkanki tłuszczowej."
            ))

    status = "available" if findings else "insufficient_data"

    return {
        "status": status,
        "findings": findings
    }, strengths, attention


def _energy_profile(
    profile: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, str]]]:

    bmr = _number(profile.get("bmr"), "bmr", minimum=0)
    tdee = _number(profile.get("tdee"), "tdee", minimum=0)
    target = _number(profile.get("calorie_target"), "calorie_target", minimum=0)

    goal = str(profile.get("goal") or "").strip().lower()
    findings: list[dict[str, str]] = []

    if bmr is not None:
        findings.append(_finding(
            "Podstawowa przemiana materii (BMR)",
            f"Podana wartość BMR wynosi około {bmr:.0f} kcal/dzień. Jest to szacunek energii spoczynkowej, a nie zalecany limit spożycia."
        ))

    if tdee is not None:
        findings.append(_finding(
            "Całkowite zapotrzebowanie (TDEE)",
            f"Podana wartość TDEE wynosi około {tdee:.0f} kcal/dzień. To szacunek zależny m.in. od przyjętego poziomu aktywności."
        ))

    if target is not None and tdee is not None:
        difference = target - tdee

        findings.append(_finding(
            "Relacja celu kalorycznego do TDEE",
            f"Cel kaloryczny jest {abs(difference):.0f} kcal/dzień {'powyżej' if difference > 0 else 'poniżej' if difference < 0 else 'na poziomie'} podanego TDEE."
        ))

        if any(word in goal for word in ("redukc", "reduction", "lose", "weight loss")):
            consistent = difference < 0

            findings.append(_finding(
                "Spójność celu",
                "Cel kaloryczny jest niższy od TDEE." if consistent else "Cel redukcyjny nie jest niższy od podanego TDEE; sprawdź ustawienia celu i obliczenia.",
                "positive" if consistent else "attention"
            ))

        elif any(word in goal for word in ("utrzym", "maint", "maintenance")):
            consistent = abs(difference) <= max(50, tdee * 0.03)

            findings.append(_finding(
                "Spójność celu",
                "Cel kaloryczny jest zbliżony do TDEE." if consistent else "Cel utrzymania odbiega od podanego TDEE; sprawdź ustawienia.",
                "positive" if consistent else "attention"
            ))

        elif any(word in goal for word in ("przyrost", "masa", "gain", "muscle")):
            consistent = difference > 0

            findings.append(_finding(
                "Spójność celu",
                "Cel kaloryczny jest wyższy od TDEE." if consistent else "Cel na przyrost masy nie jest wyższy od podanego TDEE; sprawdź ustawienia.",
                "positive" if consistent else "attention"
            ))

        else:
            findings.append(_finding(
                "Spójność celu",
                "Nie rozpoznano celu; nie oceniono zgodności celu kalorycznego z TDEE."
            ))

    elif target is not None:
        findings.append(_finding(
            "Brak TDEE do porównania",
            "Podano cel kaloryczny, ale brakuje TDEE; nie można porównać tych wartości."
        ))

    return {
        "status": "available" if findings else "insufficient_data",
        "findings": findings
    }, []


def _progress_analysis(
    history: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, str]]]:

    findings: list[dict[str, str]] = []

    if len(history) < 2:
        return {
            "status": "insufficient_data",
            "findings": [
                _finding(
                    "Za mało danych do analizy trendu",
                    "Do porównania zmian potrzebne są co najmniej dwa pomiary z poprawną datą."
                )
            ]
        }, []

    first, last = history[0], history[-1]

    days = (
        last["created_at"] - first["created_at"]
    ).total_seconds() / 86400

    if days <= 0:
        return {
            "status": "insufficient_data",
            "findings": [
                _finding(
                    "Brak odstępu czasu",
                    "Daty pomiarów nie pozwalają obliczyć tempa zmian."
                )
            ]
        }, []

    strengths: list[dict[str, str]] = []

    for key, label, unit in (
        ("weight", "Masa ciała", "kg"),
        ("bmi", "BMI", "pkt"),
        ("waist", "Obwód talii", "cm")
    ):
        start, end = first.get(key), last.get(key)

        if start is None or end is None:
            continue

        delta = end - start
        per_30_days = delta / days * 30

        direction = (
            "wzrost" if delta > 0
            else "spadek" if delta < 0
            else "brak zmiany"
        )

        findings.append(_finding(
            label,
            f"{direction.capitalize()} o {abs(delta):.2f} {unit} między pierwszym a ostatnim pomiarem; średnia zmiana to {per_30_days:+.2f} {unit} na 30 dni."
        ))

    findings.append(_finding(
        "Interpretacja trendu",
        "Zmiana masy ciała nie jest automatycznie dobra ani zła. Znaczenie trendu zależy od celu, samopoczucia, czasu obserwacji i pozostałych danych."
    ))

    return {
        "status": "available" if len(findings) > 1 else "insufficient_data",
        "findings": findings
    }, strengths


def analyze_body(profile: dict[str, Any]) -> dict[str, Any]:
    """
    Analyse one BODYLAB profile.

    Required input: dictionary. Missing optional fields are allowed. History
    entries may contain created_at (ISO string/date/datetime), weight, bmi,
    and waist. Invalid supplied numeric values raise ValueError.
    """

    if not isinstance(profile, dict):
        raise ValueError("profile must be a dictionary.")

    body, strengths, attention = _body_metrics(profile)
    energy, _ = _energy_profile(profile)

    history = _history_rows(profile.get("history", []))
    progress, _ = _progress_analysis(history)
    progress_intelligence = analyze_progress(history)

    recommendations: list[dict[str, str]] = []

    bmi = _number(profile.get("bmi"), "bmi", minimum=0)
    whtr = _number(profile.get("whtr"), "whtr", minimum=0)
    whr = _number(profile.get("whr"), "whr", minimum=0)

    sex = _normalise_sex(profile.get("sex"))
    goal = str(profile.get("goal") or "").strip().lower()

    if body["status"] == "insufficient_data":
        recommendations.append(_finding(
            "Uzupełnij pomiary",
            "Dodaj wzrost i masę ciała, aby obliczyć BMI. Jeśli masz obwód talii i bioder, uzupełnij je również — pozwoli to rozszerzyć analizę o WHtR i WHR."
        ))

    if whtr is not None and not (bmi is not None and bmi >= 35):
        if whtr >= 0.5:
            recommendations.append(_finding(
                "Obserwuj obwód talii",
                "Powtarzaj pomiar talii w podobnych warunkach i porównuj go w czasie. WHtR jest wskaźnikiem przesiewowym, dlatego nie wyciągaj wniosków z pojedynczego odczytu.",
                "attention"
            ))

        elif whtr < 0.4:
            recommendations.append(_finding(
                "Zweryfikuj pomiar talii",
                "Warto upewnić się, że talia i wzrost zostały zmierzone prawidłowo. Nietypowo niski WHtR sam w sobie nie określa stanu zdrowia."
            ))

    if whr is not None and sex is None:
        recommendations.append(_finding(
            "Uzupełnij płeć w profilu",
            "Dzięki temu BODYLAB będzie mógł zastosować odpowiedni próg interpretacyjny WHR. Bez tej informacji wskaźnik pozostaje bez klasyfikacji."
        ))

    if bmi is not None and whtr is not None and bmi < 35:
        if (bmi >= 25 and whtr < 0.5) or (bmi < 25 and whtr >= 0.5):
            recommendations.append(_finding(
                "Nie opieraj oceny na jednym wskaźniku",
                "BMI i WHtR opisują różne cechy. Sprawdź technikę pomiaru talii i interpretuj oba wyniki łącznie, zamiast uznawać jeden z nich za rozstrzygający."
            ))

    if progress["status"] == "insufficient_data":
        recommendations.append(_finding(
            "Zbuduj historię pomiarów",
            "Zapisuj masę ciała i obwód talii regularnie, w możliwie podobnych warunkach. Co najmniej dwa pomiary z datami pozwolą porównać zmianę w czasie."
        ))

    elif progress["status"] == "available":
        recommendations.append(_finding(
            "Oceniaj trend, nie pojedynczy odczyt",
            "Porównuj kilka kolejnych pomiarów i zestawiaj je z celem oraz samopoczuciem. Różnica między pierwszym i ostatnim pomiarem nie wyjaśnia przyczyny zmiany."
        ))

    if energy["status"] == "insufficient_data":
        recommendations.append(_finding(
            "Uzupełnij profil energetyczny",
            "Podaj dostępne wartości BMR, TDEE, cel i cel kaloryczny, aby BODYLAB mógł sprawdzić ich wzajemną relację."
        ))

    elif any(word in goal for word in ("redukc", "reduction", "lose", "weight loss")):
        recommendations.append(_finding(
            "Kontroluj założenia celu redukcyjnego",
            "Porównuj cel kaloryczny z aktualnym szacunkiem TDEE i okresowo weryfikuj postępy. TDEE jest estymacją, a nie stałą wartością."
        ))

    elif any(word in goal for word in ("utrzym", "maint", "maintenance")):
        recommendations.append(_finding(
            "Weryfikuj utrzymanie na podstawie trendu",
            "Sam cel kaloryczny nie potwierdza utrzymania masy. Obserwuj średni trend masy ciała w dłuższym okresie."
        ))

    elif any(word in goal for word in ("przyrost", "masa", "gain", "muscle")):
        recommendations.append(_finding(
            "Monitoruj przyrost w szerszym kontekście",
            "Oprócz masy ciała obserwuj obwód talii i regularność treningów. Sam wzrost masy nie określa, jaka część zmiany wynika z mięśni."
        ))

    if not recommendations:
        recommendations.append(_finding(
            "Kontynuuj regularną obserwację",
            "Interpretuj wskaźniki łącznie i zapisuj pomiary w podobnych warunkach. Pojedynczy pomiar nie pokazuje całego obrazu."
        ))

    limitations = [
        "Raport ma charakter informacyjny i nie stanowi diagnozy ani porady medycznej.",
        "BMI nie rozróżnia tkanki tłuszczowej i mięśniowej ani nie opisuje rozmieszczenia tkanki tłuszczowej.",
        "WHtR i WHR są wskaźnikami przesiewowymi; wynik zależy od poprawności pomiaru i kontekstu.",
        "BMR i TDEE są szacunkami, a nie bezpośrednim pomiarem wydatku energetycznego.",
        "Analiza trendu opisuje różnice między zapisanymi pomiarami; nie ustala ich przyczyny.",
    ]

    if attention:
        summary_title = "Wyniki wymagają szerszego kontekstu"
        summary_description = "Co najmniej jeden wskaźnik lub obszar profilu zasługuje na dodatkową uwagę. Przeczytaj szczegóły i nie traktuj ich jako diagnozy."

    elif body["status"] == "available":
        summary_title = "Brak wyraźnych sygnałów ostrzegawczych w dostępnych wskaźnikach"
        summary_description = "Dostępne wskaźniki nie wskazują w tej analizie na obszar wymagający szczególnego wyróżnienia. Nie jest to potwierdzenie pełnego zdrowia."

    else:
        summary_title = "Potrzeba więcej danych"
        summary_description = "Dostępne informacje nie wystarczają do pełnej analizy. Raport pokazuje tylko te obszary, które można ocenić."

    return {
        "version": VERSION,
        "overall_summary": {
            "title": summary_title,
            "description": summary_description
        },
        "body_metrics": body,
        "energy_profile": energy,
        "progress_analysis": progress,
        "progress_intelligence": progress_intelligence,
        "strengths": strengths,
        "attention_areas": attention,
        "recommendations": recommendations,
        "limitations": limitations,
    }


# Convenient alias for callers who prefer the longer function name.
def get_smart_body_analysis_v2(profile: dict[str, Any]) -> dict[str, Any]:
    return analyze_body(profile)
