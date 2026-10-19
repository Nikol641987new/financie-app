import unittest

import pandas as pd

from build_dashboard_data import _growth_trend


class GrowthTrendTests(unittest.TestCase):
    def setUp(self):
        self.rising = pd.Series(range(100, 353), dtype=float)
        self.falling = pd.Series(range(353, 100, -1), dtype=float)

    def classify(self, close, sma_short, sma_long, rsi):
        conversion_to_eur = 0.9
        return _growth_trend(
            close=close,
            sma_short=sma_short * conversion_to_eur,
            sma_long=sma_long * conversion_to_eur,
            price_eur=float(close.iloc[-1]) * conversion_to_eur,
            conversion_to_eur=conversion_to_eur,
            asset_date="19.10.2026",
            rsi=rsi,
        )

    def test_confirmed_uptrend_with_moderate_rsi_is_possible_entry(self):
        result = self.classify(self.rising, 340, 300, 55)

        self.assertEqual(result["status"], "Možný vstup")
        self.assertGreater(result["return_3m_pct"], 0)
        self.assertGreater(result["return_6m_pct"], 0)

    def test_overbought_uptrend_is_wait(self):
        result = self.classify(self.rising, 340, 300, 72)

        self.assertEqual(result["status"], "Vyčkať")

    def test_confirmed_downtrend_is_weak_trend(self):
        result = self.classify(self.falling, 120, 160, 35)

        self.assertEqual(result["status"], "Slabý trend")

    def test_insufficient_history_is_not_classified(self):
        result = self.classify(self.rising.iloc[-252:], 340, 300, 55)

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
