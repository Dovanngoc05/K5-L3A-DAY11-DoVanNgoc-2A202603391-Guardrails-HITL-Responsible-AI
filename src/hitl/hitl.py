"""
Lab 11 — Optional enrichment: Human-in-the-Loop Design
  (Không chấm — tham khảo. Tóm tắt nộp do scripts/grade.py tự sinh,
   không viết report/*.md tay.)
  - Confidence Router
  - 3 HITL decision points
"""
from dataclasses import dataclass


# ============================================================
# Optional enrichment: ConfidenceRouter (không chấm)
#
# Route agent responses based on confidence scores:
#   - HIGH (>= 0.9): Auto-send to user
#   - MEDIUM (0.7 - 0.9): Queue for human review
#   - LOW (< 0.7): Escalate to human immediately
#
# Special case: if the action is HIGH_RISK (e.g., money transfer,
# account deletion), ALWAYS escalate regardless of confidence.
#
# Implement the route() method.
# ============================================================

HIGH_RISK_ACTIONS = [
    "transfer_money",
    "close_account",
    "change_password",
    "delete_data",
    "update_personal_info",
]


@dataclass
class RoutingDecision:
    """Result of the confidence router."""
    action: str          # "auto_send", "queue_review", "escalate"
    confidence: float
    reason: str
    priority: str        # "low", "normal", "high"
    requires_human: bool


class ConfidenceRouter:
    """Route agent responses based on confidence and risk level.

    Thresholds:
        HIGH:   confidence >= 0.9 -> auto-send
        MEDIUM: 0.7 <= confidence < 0.9 -> queue for review
        LOW:    confidence < 0.7 -> escalate to human

    High-risk actions always escalate regardless of confidence.
    """

    HIGH_THRESHOLD = 0.9
    MEDIUM_THRESHOLD = 0.7

    def route(self, response: str, confidence: float,
              action_type: str = "general") -> RoutingDecision:
        """Route a response based on confidence score and action type.

        Args:
            response: The agent's response text
            confidence: Confidence score between 0.0 and 1.0
            action_type: Type of action (e.g., "general", "transfer_money")

        Returns:
            RoutingDecision with routing action and metadata
        """
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        normalized_action = action_type.strip().lower()
        high_risk_actions = {action.lower() for action in HIGH_RISK_ACTIONS}
        if normalized_action in high_risk_actions:
            return RoutingDecision(
                action="escalate",
                confidence=confidence,
                reason=f"High-risk action: {normalized_action}",
                priority="high",
                requires_human=True,
            )

        if confidence >= self.HIGH_THRESHOLD:
            return RoutingDecision(
                action="auto_send",
                confidence=confidence,
                reason="High confidence",
                priority="low",
                requires_human=False,
            )

        if confidence >= self.MEDIUM_THRESHOLD:
            return RoutingDecision(
                action="queue_review",
                confidence=confidence,
                reason="Medium confidence — needs review",
                priority="normal",
                requires_human=True,
            )

        return RoutingDecision(
            action="escalate",
            confidence=confidence,
            reason="Low confidence — escalating",
            priority="high",
            requires_human=True,
        )


# ============================================================
# Optional enrichment: 3 HITL decision points (không chấm)
# Không bắt buộc điền. Tóm tắt bài nộp: chạy scripts/grade.py
# (tự sinh lab_report.md) — không viết report tay.
#
# For each decision point, define:
# - trigger: What condition activates this HITL check?
# - hitl_model: Which model? (human-in-the-loop, human-on-the-loop,
#   human-as-tiebreaker)
# - context_needed: What info does the human reviewer need?
# - example: A concrete scenario
# - approval_path: What approve/reject/timeout decision is recorded?
# - audit_fields: Which correlation ID, intent and proposed action/diff are logged?
#
# Think about real banking scenarios where human judgment is critical.
# ============================================================

hitl_decision_points = [
    {
        "id": 1,
        "name": "High-value transfer approval",
        "trigger": "A transfer exceeds the configured review threshold, uses a new beneficiary, or has a fraud signal.",
        "hitl_model": "human-in-the-loop",
        "context_needed": "Verified customer identity, amount, source account, masked destination, beneficiary age, risk signals, and policy checks.",
        "example": "A customer requests a large transfer to a beneficiary added moments ago.",
        "approval_path": "Hold the transfer pending review; approve only after required identity checks, reject on suspected fraud, and deny on timeout.",
        "audit_fields": "correlation_id, customer_id, intent, amount, masked_source, masked_destination, risk_signals, reviewer_id, decision, reason, timestamp",
    },
    {
        "id": 2,
        "name": "Account security and profile changes",
        "trigger": "A request changes credentials, recovery methods, contact details, or other security-sensitive account data.",
        "hitl_model": "human-in-the-loop",
        "context_needed": "Authentication result, requested field and masked before/after values, recent device and session signals, and relevant account history.",
        "example": "A customer asks to replace the account recovery phone number from a newly registered device.",
        "approval_path": "Pause the change until step-up verification and reviewer approval; reject failed verification or suspicious requests; deny if review times out.",
        "audit_fields": "correlation_id, customer_id, intent, changed_field, masked_before, masked_after, device_id, verification_result, reviewer_id, decision, timestamp",
    },
    {
        "id": 3,
        "name": "Fraud alert and disputed transaction review",
        "trigger": "The system flags a transaction or the customer disputes a charge, but available evidence does not support a confident automated decision.",
        "hitl_model": "human-as-tiebreaker",
        "context_needed": "Transaction metadata, customer dispute, relevant account activity, fraud indicators, and evidence supporting or contradicting the alert.",
        "example": "A card payment is flagged as unusual, while the customer reports that they may have made the purchase.",
        "approval_path": "Keep the case open for a reviewer; record whether to clear, investigate, or block the transaction; send the customer a status update; escalate unresolved cases.",
        "audit_fields": "correlation_id, customer_id, transaction_id, intent, fraud_signals, evidence_refs, reviewer_id, decision, reason, customer_notification, timestamp",
    },
]


# ============================================================
# Quick tests
# ============================================================

def test_confidence_router():
    """Test ConfidenceRouter with sample scenarios."""
    router = ConfidenceRouter()

    test_cases = [
        ("Balance inquiry", 0.95, "general"),
        ("Interest rate question", 0.82, "general"),
        ("Ambiguous request", 0.55, "general"),
        ("Transfer $50,000", 0.98, "transfer_money"),
        ("Close my account", 0.91, "close_account"),
    ]

    print("Testing ConfidenceRouter:")
    print("=" * 80)
    print(f"{'Scenario':<25} {'Conf':<6} {'Action Type':<18} {'Decision':<15} {'Priority':<10} {'Human?'}")
    print("-" * 80)

    for scenario, conf, action_type in test_cases:
        decision = router.route(scenario, conf, action_type)
        print(
            f"{scenario:<25} {conf:<6.2f} {action_type:<18} "
            f"{decision.action:<15} {decision.priority:<10} "
            f"{'Yes' if decision.requires_human else 'No'}"
        )

    print("=" * 80)


def test_hitl_points():
    """Display HITL decision points."""
    print("\nHITL Decision Points:")
    print("=" * 60)
    for point in hitl_decision_points:
        print(f"\n  Decision Point #{point['id']}: {point['name']}")
        print(f"    Trigger:  {point['trigger']}")
        print(f"    Model:    {point['hitl_model']}")
        print(f"    Context:  {point['context_needed']}")
        print(f"    Example:  {point['example']}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_confidence_router()
    test_hitl_points()
