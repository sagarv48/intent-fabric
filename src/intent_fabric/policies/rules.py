"""Policy rule data model for YAML-configurable policy evaluation."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from enum import Enum


class RuleDecision(str, Enum):
    """Outcome a rule produces when it matches an action."""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRES_APPROVAL = "requires_approval"


@dataclass(slots=True)
class PolicyRule:
    """A single configurable policy rule.

    Rules are matched against action_type strings using fnmatch glob patterns.
    Higher priority wins when multiple rules match the same action.

    Attributes:
        action_pattern: Glob pattern matched against action_type.
                        Examples: "ticket_*", "db_drop", "*"
        decision: Outcome when the rule matches.
        reason: Human-readable explanation included in PolicyDecision.reasons.
        priority: Rules with higher priority win over lower ones when both match.
                  Default 0. Use 100 for hard-deny rules.
        conditions: Optional key→value conditions checked against the IntentRequest
                    metadata (e.g. {"risk_tolerance": "high"}).
    """

    action_pattern: str
    decision: RuleDecision
    reason: str
    priority: int = 0
    conditions: dict[str, str] = field(default_factory=dict)

    def matches(self, action_type: str, intent_metadata: dict[str, object] | None = None) -> bool:
        """Return True if this rule applies to the given action_type and context."""
        if not fnmatch.fnmatch(action_type, self.action_pattern):
            return False
        if self.conditions and intent_metadata:
            for key, expected in self.conditions.items():
                if str(intent_metadata.get(key, "")) != expected:
                    return False
        return True


@dataclass
class PolicyRuleSet:
    """An ordered collection of rules evaluated against a plan step."""

    rules: list[PolicyRule] = field(default_factory=list)

    def evaluate(
        self,
        action_type: str,
        intent_metadata: dict[str, object] | None = None,
    ) -> tuple[RuleDecision, str]:
        """Evaluate all rules against action_type and return (decision, reason).

        Matching rule with the highest priority wins.
        Falls back to REQUIRES_APPROVAL if no rule matches.
        """
        matching = [
            rule for rule in self.rules
            if rule.matches(action_type, intent_metadata)
        ]
        if not matching:
            return (
                RuleDecision.REQUIRES_APPROVAL,
                f"No policy rule matched action type '{action_type}'. Defaulting to requires_approval.",
            )
        best = max(matching, key=lambda r: r.priority)
        return best.decision, best.reason
