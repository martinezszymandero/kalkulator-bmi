"""
BODYLAB Weight Intelligence
Goal-aware interpretation of recorded body-weight changes.
Pure Python: no Streamlit, Supabase, or external API dependencies.

This module describes the direction and pace of recorded measurements.
It does not set a target weight, prescribe a rate of loss/gain, or diagnose.
"""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from math import isfinite
from typing import Any


VERSION = "1.0"


def _parse_date(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    parsed: datetime | None = None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime.combine(value, time.min)
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


def _number(value: Any) -> float | None:
    if value is None or value == "" or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if isfinite(result) and result > 0 else None


def _goal_type(value: Any) -> str | None:
    goal = str(value or "").strip().lower()
    if any(term in goal for term in ("redukc", "reduction", "lose", "weight loss")):
        return "reduction"
    if any(term in goal for term in ("utrzym", "maint", "maintenance")):
        return "maintenance"
    if any(term in goal for term in ("zwiększ", "zwieksz", "przyrost", "gain", "muscle")):
        return "gain"
    return None


def _clean_history(history: Any) -> list[dict[str, Any]]:
    if history is None:
        return []
    if not isinstance(history, (list, tuple)):
        raise ValueError("history must be a list of measurement dictionaries.")
    rows = []
    for row in history:
        if not isinstance(row, dict):
            continue
        measured_at = _parse_date(row.get("created_at"))
        weight = _number(row.get("weight"))
        if measured_at is not None and weight is not None:
            rows.append({"created_at": measured_at, "weight": weight})
    return sorted(rows, key=lambda row: row["created_at"])


def analyze_weight(history: Any, goal: Any = None, current_weight: Any = None) -> dict[str, Any]:
    """Analyze recorded weight direction and pace in relation to a broad goal."""
    rows = _clean_history(history)
    goal_type = _goal_type(goal)

    result: dict[str, Any] = {
        "version": VERSION,
        "status": "insufficient_data",
        "goal_type": goal_type,
        "measurement_count": len(rows),
        "observations": [],
        "limitations": [
            "Analiza opisuje zapisane pomiary i nie ustala przyczyn zmian masy.",
            "Bez docelowej masy ciała nie można obliczyć dystansu do konkretnego celu.",
            "Tempo zmian nie jest samo w sobie oceną bezpieczeństwa ani skuteczności.",
        ],
    }

    latest_weight = _number(current_weight)
    if latest_weight is not None:
        result["current_weight"] = round(latest_weight, 2)
    elif rows:
        latest_weight = rows[-1]["weight"]
        result["current_weight"] = round(latest_weight, 2)

    if len(rows) < 2:
        result["observations"].append({
            "type": "insufficient_data",
            "title": "Za mało pomiarów masy",
            "description": "Do oceny kierunku zmian potrzebne są co najmniej dwa pomiary masy z poprawnymi datami.",
            "classification": "FACT",
        })
        return result

    first, last = rows[0], rows[-1]
    days = (last["created_at"] - first["created_at"]).total_seconds() / 86400
    if days <= 0:
        result["observations"].append({
            "type": "insufficient_data",
            "title": "Brak odstępu czasu",
            "description": "Daty pomiarów nie pozwalają obliczyć tempa zmian masy.",
            "classification": "FACT",
        })
        return result

    change = last["weight"] - first["weight"]
    rate_30 = change / days * 30
    percent_change = (change / first["weight"]) * 100

    result.update({
        "status": "available",
        "period_days": round(days, 1),
        "start_weight": round(first["weight"], 2),
        "latest_recorded_weight": round(last["weight"], 2),
        "change_kg": round(change, 2),
        "change_percent": round(percent_change, 2),
        "change_per_30_days_kg": round(rate_30, 2),
        "direction": "decrease" if change < 0 else "increase" if change > 0 else "unchanged",
    })

    direction_text = (
        "spadek" if change < 0 else "wzrost" if change > 0 else "brak zmiany"
    )
    result["observations"].append({
        "type": "weight_change",
        "title": "Zmiana masy w zapisanym okresie",
        "description": (
            f"Od pierwszego do ostatniego pomiaru odnotowano {direction_text} "
            f"o {abs(change):.2f} kg ({percent_change:+.2f}%). "
            f"Średnia zmiana wyniosła {rate_30:+.2f} kg na 30 dni."
        ),
        "classification": "FACT",
    })

    if goal_type is None:
        alignment = "goal_not_recognized"
        description = "Nie rozpoznano celu masy ciała; nie oceniono zgodności kierunku zmian z celem."
    elif goal_type == "reduction":
        alignment = "aligned" if change < 0 else "opposite" if change > 0 else "stable"
        description = (
            "Kierunek zapisanej zmiany jest zgodny z celem redukcji."
            if alignment == "aligned" else
            "Kierunek zapisanej zmiany jest przeciwny do celu redukcji."
            if alignment == "opposite" else
            "W zapisanym okresie masa nie uległa zmianie."
        )
    elif goal_type == "gain":
        alignment = "aligned" if change > 0 else "opposite" if change < 0 else "stable"
        description = (
            "Kierunek zapisanej zmiany jest zgodny z celem zwiększenia masy."
            if alignment == "aligned" else
            "Kierunek zapisanej zmiany jest przeciwny do celu zwiększenia masy."
            if alignment == "opposite" else
            "W zapisanym okresie masa nie uległa zmianie."
        )
    else:
        alignment = "stable" if abs(percent_change) <= 0.5 else "change_observed"
        description = (
            "Masa była względnie stabilna między pierwszym i ostatnim pomiarem (zmiana do 0,5%)."
            if alignment == "stable" else
            "W zapisanym okresie odnotowano zmianę masy; sam wynik nie przesądza o realizacji celu utrzymania."
        )

    result["goal_alignment"] = alignment
    result["observations"].append({
        "type": "goal_alignment",
        "title": "Kierunek zmian a wybrany cel",
        "description": description,
        "classification": "FACT" if goal_type is not None else "ESTIMATE",
    })
    return result
