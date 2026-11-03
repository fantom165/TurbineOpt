from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .models import AgentRecommendation, DispatchDecision, SavingsResult, ScenarioInput
from .simulation import deterministic_agent_recommendations

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")
load_dotenv(ROOT_DIR / "backend" / ".env")


def adk_available() -> bool:
    try:
        import google.adk  # type: ignore  # noqa: F401
    except Exception:
        return False
    use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true"
    has_vertex_config = bool(os.getenv("GOOGLE_CLOUD_PROJECT") and os.getenv("GOOGLE_CLOUD_LOCATION"))
    return bool(os.getenv("GOOGLE_API_KEY") or (use_vertex and has_vertex_config))


def build_adk_agent_registry() -> dict[str, Any]:
    """Return ADK agent definitions when ADK and credentials are present.

    The POC intentionally keeps deterministic output as the default so demos are
    repeatable. This registry is the integration point for live ADK execution.
    """
    if not adk_available():
        return {}

    from google.adk import Agent  # type: ignore

    model = os.getenv("TURBINEOPT_ADK_MODEL", "gemini-3.5-flash")
    roles = {
        "fuel_agent": "Forecast natural gas economics and fuel procurement exposure.",
        "weather_agent": "Reason about ambient conditions and turbine efficiency.",
        "dispatch_agent": "Compare self-generation, grid purchase, and excess sale economics.",
        "maintenance_agent": "Identify operating choices that increase wear or outage risk.",
        "carbon_agent": "Estimate emissions and carbon cost impact.",
        "digital_twin_agent": "Evaluate combined-cycle performance under the scenario.",
        "master_optimization_agent": "Synthesize specialist recommendations into one advisory strategy.",
    }
    return {
        name: Agent(
            name=name,
            model=model,
            instruction=instruction + " Return concise structured recommendations for an operator-approved advisory POC.",
        )
        for name, instruction in roles.items()
    }


def run_agent_team(
    scenario: ScenarioInput,
    savings: SavingsResult,
    dispatch: DispatchDecision,
) -> list[AgentRecommendation]:
    # Live ADK calls can be added here once credentials and model policy are set.
    # Until then, keep demo outputs deterministic and auditable.
    return deterministic_agent_recommendations(scenario, savings, dispatch)
