
"""Explainable, deterministic incident-priority assessment.

This module supports human review. It does not dispatch resources
or replace emergency-service protocols.
"""


def assess_priority(severity, people_affected, verification_status):
    """Return a transparent priority score, reasons, and review flags."""

    severity_points = {
        "Critical": 70,
        "High": 45,
        "Medium": 25,
        "Low": 10,
    }

    if severity not in severity_points:
        raise ValueError(f"Unknown severity: {severity}")

    if isinstance(people_affected, bool) or not isinstance(
        people_affected, int
    ):
        raise ValueError("People affected must be a non-negative integer.")

    if people_affected < 0:
        raise ValueError("People affected cannot be negative.")

    allowed_verification = {"Verified", "Pending", "Unverified"}

    if verification_status not in allowed_verification:
        raise ValueError(
            f"Unknown verification status: {verification_status}"
        )

    score = severity_points[severity]
    reasons = [f"Reported severity: {severity} (+{score})"]
    review_flags = []

    # Additional points reflect the reported number of people affected.
    if people_affected >= 50:
        score += 25
        reasons.append("50 or more people reported affected (+25)")
    elif people_affected >= 20:
        score += 15
        reasons.append("20–49 people reported affected (+15)")
    elif people_affected >= 5:
        score += 8
        reasons.append("5–19 people reported affected (+8)")
    else:
        reasons.append("Fewer than 5 people reported affected (+0)")

    # Verification does not reduce or increase the priority score.
    if verification_status != "Verified":
        review_flags.append(
            f"Report verification is {verification_status.lower()}."
        )
        review_flags.append(
            "Human verification is required before treating the "
            "report as confirmed."
        )

    # Thresholds are explicit and deterministic.
    if score >= 70:
        priority = "Critical Attention"
    elif score >= 50:
        priority = "High Attention"
    elif score >= 25:
        priority = "Moderate Attention"
    else:
        priority = "Routine Review"

    if severity == "Critical":
        reasons.append(
            "Critical reported severity independently warrants urgent review."
        )

    reasons.append(
        "Score is based on reported severity and reported people affected."
    )

    return {
        "priority_score": score,
        "priority_level": priority,
        "reasons": reasons,
        "review_flags": review_flags,
        "requires_human_review": True,
    }
