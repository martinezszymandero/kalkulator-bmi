
"""Unit tests for BODYLAB Smart Body Analysis 2.1 (run: python -m unittest -v)."""

import unittest
from smart_body_analysis_v2 import analyze_body


def base_profile(**overrides):
    profile = {
        "weight": 79.0,
        "height": 179.0,
        "age": 35,
        "sex": "Mężczyzna",
        "bmi": 24.66,
        "whtr": 0.45,
        "whr": 0.88,
        "waist": 81.0,
        "hips": 92.0,
        "bmr": 1740,
        "tdee": 2697,
        "calorie_target": 2292,
        "activity_level": "Umiarkowana aktywność",
        "goal": "Redukcja masy ciała",
        "history": [],
    }
    profile.update(overrides)
    return profile


class SmartBodyAnalysisTests(unittest.TestCase):
    def test_typical_metrics_and_male_whr_below_threshold(self):
        report = analyze_body(base_profile())
        self.assertEqual(report["version"], "2.1")
        titles = [x["title"] for x in report["body_metrics"]["findings"]]
        self.assertIn("WHR poniżej przyjętego progu", titles)
        self.assertIn("WHtR w typowym przedziale", titles)

    def test_high_bmi_with_typical_whtr_disagreement(self):
        report = analyze_body(base_profile(bmi=28, whtr=0.46, whr=0.88))
        titles = [x["title"] for x in report["body_metrics"]["findings"]]
        self.assertIn("Rozbieżność BMI i WHtR", titles)

    def test_normal_bmi_but_elevated_waist_ratio(self):
        report = analyze_body(base_profile(bmi=23, whtr=0.53, whr=0.92))
        self.assertTrue(report["attention_areas"])
        self.assertIn("Podwyższony WHtR", [x["title"] for x in report["body_metrics"]["findings"]])

    def test_bmi_35_disables_whtr_classification(self):
        report = analyze_body(base_profile(bmi=36, whtr=0.61))
        titles = [x["title"] for x in report["body_metrics"]["findings"]]
        self.assertIn("WHtR pominięty w interpretacji", titles)
        self.assertNotIn("Wysoki WHtR", titles)

    def test_low_bmi_is_flagged(self):
        report = analyze_body(base_profile(bmi=17.5, whtr=0.43))
        self.assertIn("BMI poniżej typowego zakresu", [x["title"] for x in report["attention_areas"]])

    def test_female_whr_threshold(self):
        report = analyze_body(base_profile(sex="Kobieta", whr=0.86))
        self.assertIn("WHR powyżej przyjętego progu", [x["title"] for x in report["body_metrics"]["findings"]])

    def test_energy_goal_consistency(self):
        report = analyze_body(base_profile(tdee=2500, calorie_target=2200))
        matches = [x for x in report["energy_profile"]["findings"] if x["title"] == "Spójność celu"]
        self.assertTrue(matches)
        self.assertEqual(matches[0]["level"], "positive")

    def test_energy_goal_inconsistency(self):
        report = analyze_body(base_profile(tdee=2200, calorie_target=2400))
        matches = [x for x in report["energy_profile"]["findings"] if x["title"] == "Spójność celu"]
        self.assertEqual(matches[0]["level"], "attention")

    def test_history_trend_is_sorted_and_calculated(self):
        history = [
            {"created_at": "2026-02-01T08:00:00", "weight": 80, "bmi": 25, "waist": 90},
            {"created_at": "2026-01-01T08:00:00", "weight": 82, "bmi": 25.6, "waist": 94},
        ]
        report = analyze_body(base_profile(history=history))
        self.assertEqual(report["progress_analysis"]["status"], "available")
        weight_finding = next(x for x in report["progress_analysis"]["findings"] if x["title"] == "Masa ciała")
        self.assertIn("Spadek o 2.00 kg", weight_finding["description"])

    def test_one_history_record_is_insufficient(self):
        history = [{"created_at": "2026-01-01", "weight": 80, "bmi": 25, "waist": 90}]
        report = analyze_body(base_profile(history=history))
        self.assertEqual(report["progress_analysis"]["status"], "insufficient_data")

    def test_missing_profile_data_returns_partial_report(self):
        report = analyze_body({})
        self.assertEqual(report["body_metrics"]["status"], "insufficient_data")
        self.assertTrue(report["limitations"])
        self.assertTrue(report["recommendations"])

    def test_invalid_numeric_input_raises_value_error(self):
        with self.assertRaises(ValueError):
            analyze_body(base_profile(bmi="not-a-number"))

    def test_history_must_be_a_list(self):
        with self.assertRaises(ValueError):
            analyze_body(base_profile(history="not a list"))

    def test_elevated_whtr_recommends_waist_observation(self):
        report = analyze_body(base_profile(whtr=0.53))
        titles = [x["title"] for x in report["recommendations"]]
        self.assertIn("Obserwuj obwód talii", titles)

    def test_whr_without_sex_recommends_profile_completion(self):
        report = analyze_body(base_profile(sex=None, whr=0.92))
        titles = [x["title"] for x in report["recommendations"]]
        self.assertIn("Uzupełnij płeć w profilu", titles)

    def test_bmi_whtr_disagreement_recommends_combined_interpretation(self):
        report = analyze_body(base_profile(bmi=28, whtr=0.46))
        titles = [x["title"] for x in report["recommendations"]]
        self.assertIn("Nie opieraj oceny na jednym wskaźniku", titles)

    def test_insufficient_history_recommends_building_measurement_history(self):
        report = analyze_body(base_profile(history=[]))
        titles = [x["title"] for x in report["recommendations"]]
        self.assertIn("Zbuduj historię pomiarów", titles)

    def test_reduction_goal_has_specific_recommendation(self):
        report = analyze_body(base_profile(goal="Redukcja masy ciała"))
        titles = [x["title"] for x in report["recommendations"]]
        self.assertIn("Kontroluj założenia celu redukcyjnego", titles)

    def test_maintenance_goal_has_specific_recommendation(self):
        report = analyze_body(base_profile(goal="Utrzymanie masy ciała"))
        titles = [x["title"] for x in report["recommendations"]]
        self.assertIn("Weryfikuj utrzymanie na podstawie trendu", titles)

    def test_gain_goal_has_specific_recommendation(self):
        report = analyze_body(base_profile(goal="Przyrost masy mięśniowej"))
        titles = [x["title"] for x in report["recommendations"]]
        self.assertIn("Monitoruj przyrost w szerszym kontekście", titles)


if __name__ == "__main__":
    unittest.main()
