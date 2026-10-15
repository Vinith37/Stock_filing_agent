"""Tests for the JEV (Journal Entry Verification) agent"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.jev_agent import calculate_probability


class TestCalculateProbability:
    """Test the JEV probability scoring engine"""

    def test_high_probability_bullish_filing(self):
        """Bullish + high impact + clean data = high probability"""
        analysis = {
            "sentiment": "bullish",
            "impact_score": 8,
            "data_quality": 0.9,
            "risk_flags": [],
            "category": "Financial Results",
        }
        prob, factors = calculate_probability(analysis)
        assert prob >= 0.65, f"Expected >= 0.65, got {prob}"
        assert "Bullish sentiment" in factors[0]

    def test_low_probability_poor_data(self):
        """Low quality + many risk flags + neutral = low probability"""
        analysis = {
            "sentiment": "neutral",
            "impact_score": 2,
            "data_quality": 0.3,
            "risk_flags": ["Audit qualification", "Going concern", "RPT"],
            "category": "Other",
        }
        prob, factors = calculate_probability(analysis)
        assert prob < 0.65, f"Expected < 0.65, got {prob}"

    def test_probability_never_exceeds_one(self):
        """Edge case: perfect scores should not exceed 1.0"""
        analysis = {
            "sentiment": "bullish",
            "impact_score": 10,
            "data_quality": 1.0,
            "risk_flags": [],
            "category": "Financial Results",
        }
        prob, _ = calculate_probability(analysis)
        assert prob <= 1.0, f"Probability exceeded 1.0: {prob}"

    def test_probability_minimum_zero(self):
        """Worst case should still be >= 0"""
        analysis = {
            "sentiment": "neutral",
            "impact_score": 1,
            "data_quality": 0.0,
            "risk_flags": ["flag1", "flag2", "flag3", "flag4"],
            "category": "Other",
        }
        prob, _ = calculate_probability(analysis)
        assert prob >= 0.0, f"Probability went negative: {prob}"

    def test_bearish_sentiment_scores(self):
        """Bearish sentiment should score between neutral and bullish"""
        analysis_bearish = {
            "sentiment": "bearish",
            "impact_score": 5,
            "data_quality": 0.7,
            "risk_flags": [],
            "category": "Financial Results",
        }
        analysis_neutral = {
            "sentiment": "neutral",
            "impact_score": 5,
            "data_quality": 0.7,
            "risk_flags": [],
            "category": "Financial Results",
        }
        prob_bearish, _ = calculate_probability(analysis_bearish)
        prob_neutral, _ = calculate_probability(analysis_neutral)
        assert prob_bearish > prob_neutral

    def test_high_relevance_category_boost(self):
        """Market-relevant categories should score higher"""
        base = {
            "sentiment": "neutral",
            "impact_score": 5,
            "data_quality": 0.7,
            "risk_flags": [],
        }
        analysis_high = {**base, "category": "Financial Results"}
        analysis_low = {**base, "category": "Other"}

        prob_high, _ = calculate_probability(analysis_high)
        prob_low, _ = calculate_probability(analysis_low)
        assert prob_high > prob_low

    def test_risk_flags_reduce_probability(self):
        """More risk flags should reduce the probability"""
        base = {
            "sentiment": "bullish",
            "impact_score": 7,
            "data_quality": 0.8,
            "category": "Board Meeting",
        }
        analysis_clean = {**base, "risk_flags": []}
        analysis_risky = {**base, "risk_flags": ["a", "b", "c"]}

        prob_clean, _ = calculate_probability(analysis_clean)
        prob_risky, _ = calculate_probability(analysis_risky)
        assert prob_clean > prob_risky

    def test_factors_list_has_five_entries(self):
        """Should always return exactly 5 confidence factors"""
        analysis = {
            "sentiment": "bullish",
            "impact_score": 5,
            "data_quality": 0.5,
            "risk_flags": ["flag1"],
            "category": "Other",
        }
        _, factors = calculate_probability(analysis)
        assert len(factors) == 5, f"Expected 5 factors, got {len(factors)}"
