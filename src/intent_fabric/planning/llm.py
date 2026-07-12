"""LLM-backed planner implementations.

Two providers are available:
  - OllamaLLMPlanner  — calls a local Ollama server, free, no API key required
  - OpenAILLMPlanner  — calls the OpenAI chat-completions API

Both implement the Planner protocol and can be passed to IntentFabricMCPTools as a
drop-in replacement for RuleBasedPlanner.

Selecting a planner via environment variable:
    INTENT_PLANNER=ollama   → OllamaLLMPlanner.from_env()
    INTENT_PLANNER=openai   → OpenAILLMPlanner.from_env()
    INTENT_PLANNER=rule_based (default) → RuleBasedPlanner

Ollama quick-start:
    brew install ollama
    ollama serve
    ollama pull llama3   # or mistral, phi3, etc.
    export INTENT_PLANNER=ollama OLLAMA_PLAN_MODEL=llama3

OpenAI quick-start:
    export INTENT_PLANNER=openai OPENAI_API_KEY=sk-...
"""

from __future__ import annotations

import json
import os
import urllib.request
from hashlib import sha1

from intent_fabric.models import (
    ActionContract,
    EvidencePackageReference,
    IntentRequest,
    Plan,
    PlanStep,
)

_SYSTEM_PROMPT = """You are an enterprise action planner.
Given a user intent and a list of evidence snippets, return a JSON plan.

The JSON must have this exact shape:
{
  "summary": "one sentence describing the plan",
  "steps": [
    {
      "title": "short step title",
      "description": "one sentence",
      "action_type": "one of: ticket_create, document_update, notification_send, analysis_review",
      "target": "system or artifact name",
      "justification": "why this step is needed"
    }
  ]
}

Rules:
- Return valid JSON only. No markdown fences, no prose outside the JSON.
- Keep steps minimal — one to three steps is almost always enough.
- action_type must be exactly one of the four values listed.
- If the intent is read-only or analytical, use analysis_review.
- If uncertain, default to analysis_review.
"""


def _stable_id(prefix: str, seed: str) -> str:
    return f"{prefix}_{sha1(seed.encode('utf-8')).hexdigest()[:12]}"


def _build_user_message(intent: IntentRequest, evidence: EvidencePackageReference) -> str:
    snippets = "\n".join(
        f"[{i + 1}] (score={item.score:.3f}) {item.snippet[:300]}"
        for i, item in enumerate(evidence.items[:5])
    )
    return (
        f"User intent: {intent.user_request}\n\n"
        f"Evidence ({len(evidence.items)} items):\n{snippets or '(no evidence provided)'}"
    )


def _parse_llm_plan(raw_json: str, intent: IntentRequest, evidence: EvidencePackageReference) -> Plan:
    """Parse LLM JSON output into a Plan, falling back gracefully on parse errors."""
    try:
        data = json.loads(raw_json.strip())
    except json.JSONDecodeError:
        # If the model returned garbage, fall back to a single analysis step
        data = {
            "summary": f"Analysis plan for: {intent.user_request}",
            "steps": [
                {
                    "title": "Review evidence",
                    "description": "Review the available evidence and produce a summary.",
                    "action_type": "analysis_review",
                    "target": "knowledge-artifact",
                    "justification": "LLM response could not be parsed; defaulting to safe review step.",
                }
            ],
        }

    plan_id = _stable_id("plan", intent.intent_id)
    steps: list[PlanStep] = []
    for index, raw_step in enumerate(data.get("steps", []), start=1):
        step_id = _stable_id("step", f"{plan_id}:{index}")
        contract_id = _stable_id("contract", step_id)
        action_type = raw_step.get("action_type", "analysis_review")
        if action_type not in {"ticket_create", "document_update", "notification_send", "analysis_review"}:
            action_type = "analysis_review"
        contract = ActionContract(
            contract_id=contract_id,
            action_type=action_type,
            target=str(raw_step.get("target", "knowledge-artifact")),
            intent=intent.user_request,
            simulated=False,  # LLM plans are real proposals, not simulated
            parameters={"evidence_items": len(evidence.items)},
            justification=str(raw_step.get("justification", "")),
        )
        steps.append(
            PlanStep(
                step_id=step_id,
                title=str(raw_step.get("title", f"Step {index}")),
                description=str(raw_step.get("description", "")),
                action_contract=contract,
                depends_on=[steps[-1].step_id] if steps else [],
            )
        )

    return Plan(
        plan_id=plan_id,
        intent_id=intent.intent_id,
        summary=str(data.get("summary", f"LLM plan for: {intent.user_request}")),
        steps=steps,
        metadata={"evidence_query_text": evidence.query_text, "planner": "llm"},
    )


class OllamaLLMPlanner:
    """Calls a local Ollama server to create real AI-generated plans.

    Environment variables:
        OLLAMA_BASE_URL      default: http://localhost:11434
        OLLAMA_PLAN_MODEL    default: llama3
    """

    def __init__(self, model: str, base_url: str) -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")

    @classmethod
    def from_env(cls) -> "OllamaLLMPlanner":
        return cls(
            model=os.environ.get("OLLAMA_PLAN_MODEL", "llama3"),
            base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        )

    def create_plan(self, intent: IntentRequest, evidence: EvidencePackageReference) -> Plan:
        user_message = _build_user_message(intent, evidence)
        body = json.dumps(
            {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                "stream": False,
                "format": "json",
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self._base_url}/api/chat",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
        raw_json = result["message"]["content"]
        return _parse_llm_plan(raw_json, intent, evidence)


class OpenAILLMPlanner:
    """Calls the OpenAI chat-completions API to create real AI-generated plans.

    Environment variables (required):
        OPENAI_API_KEY
        OPENAI_PLAN_MODEL    default: gpt-4o-mini
    """

    def __init__(self, model: str, api_key: str) -> None:
        self._model = model
        self._api_key = api_key

    @classmethod
    def from_env(cls) -> "OpenAILLMPlanner":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY environment variable is required")
        return cls(
            model=os.environ.get("OPENAI_PLAN_MODEL", "gpt-4o-mini"),
            api_key=api_key,
        )

    def create_plan(self, intent: IntentRequest, evidence: EvidencePackageReference) -> Plan:
        user_message = _build_user_message(intent, evidence)
        body = json.dumps(
            {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.2,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
        raw_json = result["choices"][0]["message"]["content"]
        return _parse_llm_plan(raw_json, intent, evidence)


def build_planner(planner_name: str = "") -> "OllamaLLMPlanner | OpenAILLMPlanner | None":
    """Factory that reads INTENT_PLANNER env var and returns the right planner.

    Returns None to signal "use the default RuleBasedPlanner".

    INTENT_PLANNER=ollama   → OllamaLLMPlanner.from_env()
    INTENT_PLANNER=openai   → OpenAILLMPlanner.from_env()
    (anything else)         → None (caller should use RuleBasedPlanner)
    """
    name = (planner_name or os.environ.get("INTENT_PLANNER", "")).lower().strip()
    if name == "ollama":
        return OllamaLLMPlanner.from_env()
    if name == "openai":
        return OpenAILLMPlanner.from_env()
    return None
