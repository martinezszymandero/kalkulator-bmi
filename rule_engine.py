"""
BODYLAB Rule Engine + Insight Generator 2.0

Combines already-computed BODYLAB module outputs into concise, prioritized
insights. It does not recalculate metrics, diagnose, or infer missing data.

Public API:
    generate_insights(analysis: dict) -> dict
"""

from __future__ import annotations

from typing import Any

VERSION = "2.0"

_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _add(
    items: list[dict[str, Any]],
    *,
    insight_id: str,
    title: str,
    summary: str,
    classification: str,
    priority: str,
    sources: list[str],
    recommendation: str | None = None,
) -> None:
    """Append a normalized insight, avoiding duplicate IDs."""
    if any(item["id"] == insight_id for item in items):
        return
    item: dict[str, Any] = {
        "id": insight_id,
        "title": title,
        "summary": summary,
        "classification": classification,
        "priority": priority,
        "sources": sources,
    }
    if recommendation:
        item["recommendation"] = recommendation
    items.append(item)



def generate_insights(analysis: dict[str, Any]) -> dict[str, Any]:
    """
    Generate cross-module insights from the result of analyze_body().

    Missing sections are treated as unavailable, never as zero or negative.
    The input is expected to be the complete analysis dictionary returned by
    BODYLAB's existing analysis engine.
    """
    if not isinstance(analysis, dict):
        raise ValueError("analysis must be a dictionary.")

    insights: list[dict[str, Any]] = []

    composition = analysis.get("body_composition_intelligence")
    composition = composition if isinstance(composition, dict) else {}
    consistency = _text(composition.get("consistency"))

    # One combined composition insight rather than repeating each metric signal.
    if consistency == "convergent_signal":
        _add(
            insights,
            insight_id="composition_convergent",
            title="Zgodne sygnały we wskaźnikach obwodowych",
            summary=(
                "WHtR i WHR osiągają lub przekraczają zastosowane progi orientacyjne. "
                "To zgodny sygnał przesiewowy, a nie diagnoza."
            ),
            classification="FACT",
            priority="high",
            sources=["body_composition_intelligence"],
            recommendation=(
                "Zweryfikuj technikę pomiaru talii i bioder oraz obserwuj wyniki "
                "w kolejnych pomiarach. W razie wątpliwości omów je ze specjalistą."
            ),
        )
    elif consistency == "mixed_central_signal":
        _add(
            insights,
            insight_id="composition_mixed",
            title="Niejednoznaczny obraz wskaźników obwodowych",
            summary=(
                "WHtR i WHR nie dają zgodnego sygnału względem zastosowanych "
                "progów orientacyjnych. Nie należy rozstrzygać oceny na podstawie "
                "jednego wskaźnika."
            ),
            classification="FACT",
            priority="medium",
            sources=["body_composition_intelligence"],
            recommendation=(
                "Sprawdź poprawność obu pomiarów i porównuj je w podobnych warunkach."
            ),
        )
    elif consistency == "no_elevated_central_signal":
        _add(
            insights,
            insight_id="composition_no_elevated_signal",
            title="Wskaźniki obwodowe poniżej progów orientacyjnych",
            summary=(
                "WHtR i WHR pozostają poniżej zastosowanych progów orientacyjnych. "
                "Nie jest to pełna ocena zdrowia."
            ),
            classification="FACT",
            priority="low",
            sources=["body_composition_intelligence"],
        )

    # Weight module owns direction-vs-goal interpretation.
    weight = analysis.get("weight_intelligence")
    weight = weight if isinstance(weight, dict) else {}
    alignment = _text(weight.get("goal_alignment"))
    if weight.get("status") == "available":
        if alignment == "opposite":
            _add(
                insights,
                insight_id="weight_goal_opposite",
                title="Kierunek zmiany masy różni się od wybranego celu",
                summary=(
                    "Zapisany kierunek zmiany masy jest przeciwny do wybranego celu. "
                    "To opis pomiarów, nie ocena przyczyny ani skuteczności działań."
                ),
                classification="FACT",
                priority="medium",
                sources=["weight_intelligence"],
                recommendation=(
                    "Sprawdź, czy cel w profilu jest aktualny, i oceniaj kilka kolejnych "
                    "pomiarów zamiast pojedynczego odczytu."
                ),
            )
        elif alignment == "aligned":
            _add(
                insights,
                insight_id="weight_goal_aligned",
                title="Kierunek zmiany masy jest zgodny z wybranym celem",
                summary=(
                    "Kierunek zapisanej zmiany masy odpowiada wybranemu celowi. "
                    "Sam kierunek nie określa tempa ani bezpieczeństwa zmiany."
                ),
                classification="FACT",
                priority="low",
                sources=["weight_intelligence"],
            )
        elif alignment == "stable":
            _add(
                insights,
                insight_id="weight_goal_stable",
                title="Masa pozostaje względnie stabilna w zapisanym okresie",
                summary=(
                    "W module Weight Intelligence zmiana została zaklasyfikowana "
                    "jako stabilna względem wybranego celu."
                ),
                classification="FACT",
                priority="low",
                sources=["weight_intelligence"],
            )

    # Progress module adds context about stability and recording patterns.
    progress = analysis.get("progress_intelligence")
    progress = progress if isinstance(progress, dict) else {}
    stagnation = progress.get("stagnation")
    stagnation = stagnation if isinstance(stagnation, dict) else {}
    if stagnation.get("status") == "possible_stability" and alignment != "stable":
        _add(
            insights,
            insight_id="progress_possible_stability",
            title="Możliwa stabilność masy w ostatnim okresie",
            summary=(
                "W ostatnich zapisach masa była względnie stabilna przez wymagany "
                "okres obserwacji. Stabilność nie oznacza automatycznie stagnacji "
                "ani niepowodzenia celu."
            ),
            classification="FACT",
            priority="low",
            sources=["progress_intelligence"],
            recommendation=(
                "Interpretuj ten sygnał razem z wybranym celem i dłuższym trendem."
            ),
        )
    elif stagnation.get("status") == "insufficient_data":
        # Do not create a separate warning: missing history is surfaced only
        # when no other meaningful insight can be generated.
        pass

    # Energy checks are represented only when the existing engine explicitly
    # reports an inconsistency; this module does not recalculate calories.
    energy = analysis.get("energy_profile")
    energy = energy if isinstance(energy, dict) else {}
    energy_findings = energy.get("findings", [])
    if isinstance(energy_findings, list):
        for finding in energy_findings:
            if not isinstance(finding, dict):
                continue
            title = _text(finding.get("title"))
            description = _text(finding.get("description"))
            level = _text(finding.get("level")).lower()
            if title == "Spójność celu" and level == "attention" and description:
                _add(
                    insights,
                    insight_id="energy_goal_check",
                    title="Sprawdź założenia celu kalorycznego",
                    summary=description,
                    classification="ESTIMATE",
                    priority="medium",
                    sources=["energy_profile"],
                    recommendation=(
                        "Zweryfikuj wybrany cel i wartości BMR/TDEE. Są to szacunki, "
                        "a nie bezpośredni pomiar wydatku energetycznego."
                    ),
                )
                break

    # Keep the output useful when all modules have insufficient data.
    if not insights:
        _add(
            insights,
            insight_id="insufficient_data",
            title="Potrzeba więcej danych do wniosków łączonych",
            summary=(
                "Dostępne wyniki nie pozwalają obecnie utworzyć wiarygodnego "
                "wniosku łączącego kilka obszarów analizy."
            ),
            classification="FACT",
            priority="low",
            sources=[],
            recommendation=(
                "Dodaj kolejne pomiary i uzupełnij dostępne dane profilu. "
                "Brak danych nie oznacza wyniku zerowego."
            ),
        )

    insights.sort(
        key=lambda item: (
            _PRIORITY_ORDER.get(item["priority"], 99),
            item["id"],
        )
    )

    insights = insights[:3]

    return {
        "module": "BODYLAB Insight Synthesis",
        "version": VERSION,
        "status": "available" if insights and insights[0]["id"] != "insufficient_data" else "insufficient_data",
        "insight_count": len(insights),
        "insights": insights,
        "classification_legend": {
            "FACT": "Opis danych lub wyniku zwróconego przez istniejący moduł.",
            "ESTIMATE": "Ostrożna interpretacja oparta na szacunkach.",
            "RECOMMENDATION": "Ogólna wskazówka, a nie indywidualne zalecenie medyczne.",
        },
        "limitations": [
            "Moduł łączy wyniki istniejących analiz; nie przelicza ponownie wskaźników.",
            "Brak danych nie jest interpretowany jako zero ani jako wynik prawidłowy.",
            "Wnioski mają charakter informacyjny i edukacyjny, nie diagnostyczny.",
            "Wnioski są wybierane tak, aby ograniczać powtórzenia między modułami.",
        ],
    }


__all__ = ["generate_insights", "VERSION"]
