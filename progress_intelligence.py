"""
BODYLAB Progress Intelligence
Pure-Python analysis of measurement history. No Streamlit/Supabase dependencies.

Windows are anchored to the newest valid measurement, not the machine's current
date. The module describes recorded data only; it does not diagnose or infer causes.
"""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from math import isfinite
from statistics import median
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
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) and number >= 0 else None


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
        if measured_at is None:
            continue
        rows.append({
            "created_at": measured_at,
            "weight": _number(row.get("weight")),
            "bmi": _number(row.get("bmi")),
            "waist": _number(row.get("waist")),
        })
    return sorted(rows, key=lambda item: item["created_at"])


def _metric_trend(rows: list[dict[str, Any]], key: str, label: str, unit: str) -> dict[str, Any]:
    valid = [r for r in rows if r[key] is not None]
    if len(valid) < 2:
        return {
            "status": "insufficient_data",
            "measurement_count": len(valid),
            "message": f"Za mało zapisów, aby ocenić trend: {label.lower()}."
        }

    first, last = valid[0], valid[-1]
    days = (last["created_at"] - first["created_at"]).total_seconds() / 86400
    if days <= 0:
        return {
            "status": "insufficient_data",
            "measurement_count": len(valid),
            "message": f"Pomiary {label.lower()} nie obejmują odstępu czasu."
        }

    delta = last[key] - first[key]
    return {
        "status": "available",
        "measurement_count": len(valid),
        "start_value": round(first[key], 2),
        "end_value": round(last[key], 2),
        "change": round(delta, 2),
        "change_per_30_days": round(delta / days * 30, 2),
        "period_days": round(days, 1),
        "direction": "increase" if delta > 0 else "decrease" if delta < 0 else "unchanged",
        "unit": unit,
        "label": label,
    }


def _window_summary(rows: list[dict[str, Any]], days: int) -> dict[str, Any]:
    if not rows:
        return {"status": "insufficient_data", "measurement_count": 0}

    end = rows[-1]["created_at"]
    start = end.timestamp() - days * 86400
    window = [r for r in rows if r["created_at"].timestamp() >= start]
    weights = [r["weight"] for r in window if r["weight"] is not None]

    result: dict[str, Any] = {
        "status": "available" if window else "insufficient_data",
        "measurement_count": len(window),
        "window_days": days,
    }
    if weights:
        result["weight_min"] = round(min(weights), 2)
        result["weight_max"] = round(max(weights), 2)
        result["weight_range"] = round(max(weights) - min(weights), 2)
        result["first_weight"] = round(weights[0], 2)
        result["last_weight"] = round(weights[-1], 2)
        result["weight_change"] = round(weights[-1] - weights[0], 2)
    else:
        result["weight_status"] = "insufficient_data"
    return result


def _regularity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if len(rows) < 2:
        return {
            "status": "insufficient_data",
            "measurement_count": len(rows),
            "message": "Potrzebne są co najmniej dwa pomiary z poprawnymi datami."
        }
    intervals = [
        (rows[i]["created_at"] - rows[i - 1]["created_at"]).total_seconds() / 86400
        for i in range(1, len(rows))
    ]
    positive = [gap for gap in intervals if gap > 0]
    if not positive:
        return {
            "status": "insufficient_data",
            "measurement_count": len(rows),
            "message": "Daty nie pozwalają określić odstępów między pomiarami."
        }
    return {
        "status": "available",
        "measurement_count": len(rows),
        "median_interval_days": round(median(positive), 1),
        "shortest_interval_days": round(min(positive), 1),
        "longest_interval_days": round(max(positive), 1),
        "message": "Odstępy opisują częstotliwość zapisów, a nie jakość ani skuteczność działań."
    }


def _stagnation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if rows:
        cutoff = rows[-1]["created_at"].timestamp() - 90 * 86400
        rows = [r for r in rows if r["created_at"].timestamp() >= cutoff]
    weights = [r for r in rows if r["weight"] is not None]
    if len(weights) < 3:
        return {
            "status": "insufficient_data",
            "message": "Do ostrożnej oceny stabilności masy potrzeba co najmniej trzech pomiarów."
        }
    first, last = weights[0], weights[-1]
    days = (last["created_at"] - first["created_at"]).total_seconds() / 86400
    if days < 28 or first["weight"] <= 0:
        return {
            "status": "insufficient_data",
            "message": "Potrzebny jest okres co najmniej 28 dni i trzy pomiary masy."
        }
    change_pct = abs((last["weight"] - first["weight"]) / first["weight"]) * 100
    if change_pct <= 0.5:
        return {
            "status": "possible_stability",
            "period_days": round(days, 1),
            "change_percent": round((last["weight"] - first["weight"]) / first["weight"] * 100, 2),
            "message": "Masa była względnie stabilna między pierwszym a ostatnim zapisem. To opis danych, nie ocena postępu."
        }
    return {
        "status": "change_observed",
        "period_days": round(days, 1),
        "change_percent": round((last["weight"] - first["weight"]) / first["weight"] * 100, 2),
        "message": "W zapisanym okresie widoczna jest zmiana masy; nie określa ona sama w sobie jej przyczyny ani znaczenia."
    }


def _fluctuations(rows: list[dict[str, Any]]) -> dict[str, Any]:
    weights = [r["weight"] for r in rows if r["weight"] is not None]
    if len(weights) < 3:
        return {
            "status": "insufficient_data",
            "message": "Do opisu wahań potrzeba co najmniej trzech pomiarów masy."
        }
    return {
        "status": "available",
        "measurement_count": len(weights),
        "minimum": round(min(weights), 2),
        "maximum": round(max(weights), 2),
        "range": round(max(weights) - min(weights), 2),
        "message": "Zakres pokazuje różnicę między najniższym i najwyższym zapisanym wynikiem; nie wyjaśnia przyczyn wahań."
    }


def analyze_progress(history: Any) -> dict[str, Any]:
    """Return structured 7/30/90-day progress, trend, regularity and stability."""
    rows = _clean_history(history)
    if not rows:
        return {
            "version": VERSION,
            "status": "insufficient_data",
            "measurement_count": 0,
            "windows": {"7_days": _window_summary(rows, 7),
                        "30_days": _window_summary(rows, 30),
                        "90_days": _window_summary(rows, 90)},
            "trends": {},
            "regularity": _regularity(rows),
            "stagnation": _stagnation(rows),
            "fluctuations": _fluctuations(rows),
        }

    return {
        "version": VERSION,
        "status": "available" if len(rows) >= 2 else "insufficient_data",
        "measurement_count": len(rows),
        "latest_measurement": rows[-1]["created_at"].isoformat(),
        "windows": {
            "7_days": _window_summary(rows, 7),
            "30_days": _window_summary(rows, 30),
            "90_days": _window_summary(rows, 90),
        },
        "trends": {
            "weight": _metric_trend(rows, "weight", "Masa ciała", "kg"),
            "bmi": _metric_trend(rows, "bmi", "BMI", "pkt"),
            "waist": _metric_trend(rows, "waist", "Obwód talii", "cm"),
        },
        "regularity": _regularity(rows),
        "stagnation": _stagnation(rows),
        "fluctuations": _fluctuations(rows),
        "limitations": [
            "Okna 7, 30 i 90 dni są liczone wstecz od najnowszego zapisanego pomiaru.",
            "Analiza opisuje wyłącznie zapisane dane; brak pomiaru nie oznacza braku zmiany.",
            "Wahania masy mogą mieć wiele przyczyn, których ten moduł nie ustala.",
            "Stabilność masy nie jest automatycznie stagnacją ani oceną niepowodzenia celu.",
        ],
    }
