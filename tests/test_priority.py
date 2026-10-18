
from src.priority import assess_priority


def test_critical_incident_receives_critical_attention():
    result = assess_priority("Critical", 0, "Verified")

    assert result["priority_score"] == 70
    assert result["priority_level"] == "Critical Attention"


def test_affected_people_increase_score():
    result = assess_priority("High", 25, "Verified")

    assert result["priority_score"] == 60
    assert result["priority_level"] == "High Attention"


def test_unverified_report_is_flagged():
    result = assess_priority("Medium", 10, "Unverified")

    assert result["priority_score"] == 33
    assert result["priority_level"] == "Moderate Attention"
    assert result["review_flags"]
    assert result["requires_human_review"] is True


def test_verification_does_not_change_score():
    verified = assess_priority("High", 25, "Verified")
    pending = assess_priority("High", 25, "Pending")

    assert verified["priority_score"] == pending["priority_score"]
    assert verified["priority_level"] == pending["priority_level"]
    assert not verified["review_flags"]
    assert pending["review_flags"]


def test_negative_people_count_is_rejected():
    try:
        assess_priority("High", -1, "Verified")
        assert False, "Expected ValueError"
    except ValueError:
        pass
