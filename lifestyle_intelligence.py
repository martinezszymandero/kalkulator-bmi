"""BODYLAB Lifestyle Intelligence 1.0

A lightweight, rule-based educational layer using only fields already
collected by BODYLAB. It does not collect lifestyle data, diagnose, or
repeat the numerical analyses performed by other BODYLAB modules.
"""

from __future__ import annotations

from typing import Any

VERSION = "1.0"

_ACTIVITY_GUIDANCE = {
    "siedzący tryb życia": (
        "Wybrany poziom aktywności wskazuje na siedzący tryb życia i małą ilość ruchu.",
        "Jeśli jest to zgodne z Twoimi możliwościami, rozważ stopniowe włączanie codziennego ruchu, np. spacerów. Zacznij od poziomu, który możesz regularnie utrzymać.",
    ),
    "niska aktywność": (
        "Wybrany poziom aktywności jest niski.",
        "Jeśli jest to zgodne z Twoimi możliwościami, rozważ stopniowe włączanie codziennego ruchu, np. spacerów. Zacznij od poziomu, który możesz regularnie utrzymać.",
    ),
    "brak aktywności": (
        "W profilu wskazano brak lub bardzo niski poziom aktywności.",
        "Możesz rozważyć łagodne zwiększanie codziennego ruchu. Ważniejsza od jednorazowego wysiłku jest regularność i dostosowanie aktywności do swoich możliwości.",
    ),
    "lekka aktywność": (
        "Wybrany poziom aktywności odpowiada lekkiej aktywności.",
        "Utrzymuj powtarzalny rytm ruchu w tygodniu. Jeśli chcesz zwiększać aktywność, rób to stopniowo, bez gwałtownych zmian.",
    ),
    "umiarkowana aktywność": (
        "Wybrany poziom aktywności odpowiada umiarkowanej aktywności.",
        "Dbaj o regularność i równowagę między ruchem a regeneracją. Nie zakładaj, że pojedynczy intensywny trening odzwierciedla typowy tydzień.",
    ),
    "bardzo wysoka aktywność": (
        "Wybrany poziom aktywności jest bardzo wysoki.",
        "Przy dużej aktywności szczególnie istotne jest dopasowanie odpoczynku i odżywiania do obciążeń. Wartość TDEE pozostaje orientacyjnym oszacowaniem.",
    ),
    "wysoka aktywność": (
        "Wybrany poziom aktywności jest wysoki.",
        "Zwracaj uwagę na regenerację i regularność. Zapotrzebowanie energetyczne w aplikacji jest szacunkiem, dlatego warto oceniać je w szerszym kontekście i nie traktować jako dokładnego pomiaru.",
    ),
}

_GOAL_GUIDANCE = {
    "redukcja masy ciała": "W przypadku redukcji skup się na możliwych do utrzymania nawykach i spokojnej, długofalowej konsekwencji. Nie oceniaj postępów na podstawie pojedynczego dnia.",
    "utrzymanie masy ciała": "Przy utrzymaniu masy ciała pomocna jest powtarzalność codziennych nawyków i obserwowanie długoterminowego kierunku zmian, a nie pojedynczych wahań.",
    "zwiększenie masy ciała": "Przy zwiększaniu masy ciała stawiaj na regularność i realistyczne tempo. Sam szacunkowy cel kaloryczny nie przesądza o jakości ani przyczynie zmian masy.",
}


def _normalise(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def analyze_lifestyle(profile: dict[str, Any]) -> dict[str, Any]:
    """Create concise lifestyle guidance from BODYLAB's existing profile.

    Expected existing fields: activity_level and goal. Missing or unknown
    values are reported as not assessed; no values are inferred.
    """
    if not isinstance(profile, dict):
        raise ValueError("profile must be a dictionary.")

    activity = _normalise(profile.get("activity_level"))
    goal = _normalise(profile.get("goal"))

    activity_result = None
    for key, guidance in _ACTIVITY_GUIDANCE.items():
        if key in activity:
            activity_result = {
                "status": "available",
                "source": "activity_level",
                "observation": guidance[0],
                "recommendation": guidance[1],
            }
            break

    goal_result = None
    for key, recommendation in _GOAL_GUIDANCE.items():
        if key in goal:
            goal_result = {
                "status": "available",
                "source": "goal",
                "recommendation": recommendation,
            }
            break

    findings = [item for item in (activity_result, goal_result) if item]
    available = bool(findings)

    if not available:
        summary = "Brak wystarczających danych do wskazówek dotyczących stylu życia."
        status = "insufficient_data"
    elif activity_result and goal_result:
        summary = "Wskazówki uwzględniają wybrany poziom aktywności i cel użytkownika."
        status = "available"
    else:
        summary = "Dostępne są częściowe wskazówki na podstawie podanych danych."
        status = "partial"

    return {
        "module": "Lifestyle Intelligence",
        "version": VERSION,
        "status": status,
        "overall_summary": summary,
        "activity_guidance": activity_result,
        "goal_guidance": goal_result,
        "findings": findings,
        "limitations": [
            "Moduł korzysta wyłącznie z poziomu aktywności i celu już podanych w BODYLAB.",
            "Wybrany poziom aktywności jest deklaracją użytkownika, a nie pomiarem rzeczywistego ruchu.",
            "Moduł nie ocenia snu, nawodnienia, diety ani stanu zdrowia, ponieważ BODYLAB nie zbiera tych danych.",
            "Wskazówki mają charakter ogólny i edukacyjny; nie stanowią indywidualnego zalecenia medycznego ani dietetycznego.",
        ],
        "disclaimer": "Lifestyle Intelligence nie diagnozuje i nie ustala przyczyn zmian masy ciała.",
    }
