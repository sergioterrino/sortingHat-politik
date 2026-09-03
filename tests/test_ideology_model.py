import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import calculate_profile, summarize_profile


def test_profile_is_balanced_for_centered_answers():
    profile = calculate_profile([5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5])
    assert profile["economic"] == 0
    assert profile["social"] == 0
    assert profile["identity"] == 0
    assert profile["closest_ideology"] in {
        "socialdemocracia",
        "liberalismo",
        "conservadurismo",
        "nacionalismo",
        "libertarismo",
    }


def test_progressive_left_score_is_detected():
    profile = calculate_profile([9, 1, 9, 9, 9, 1, 9, 1, 8, 1, 9, 1])
    assert profile["economic"] > 40
    assert profile["social"] > 40
    assert profile["closest_ideology"] in {"socialismo", "socialdemocracia", "comunismo"}


def test_profile_summary_mentions_mixture_when_ideological_distance_is_small():
    summary = summarize_profile({
        "economic": 25,
        "social": -10,
        "identity": 15,
        "closest_ideology": "socialdemocracia",
        "top_matches": ["socialdemocracia", "liberalismo"],
        "distance_to_top": 40,
    })
    assert "mixto" in summary.lower() or "socialdemocracia" in summary.lower()
