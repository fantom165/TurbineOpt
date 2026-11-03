from __future__ import annotations

from typing import Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from turbineopt.agents import adk_available
from turbineopt.data import BASELINE, PLANT_STATE
from turbineopt.models import BaselineResponse, OptimizationResponse, PlantState, ScenarioInput
from turbineopt.simulation import optimize_scenario

app = FastAPI(
    title="TurbineOpt Combined Cycle Optimization Agent",
    version="0.1.0",
    description="Executive POC for guaranteed fuel cost reduction in AI data center power operations.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_SCENARIO = ScenarioInput()
LATEST_RESPONSE = optimize_scenario(DEFAULT_SCENARIO)


@app.get("/api/health")
def health() -> dict[str, Union[str, bool]]:
    return {"status": "ok", "adk_live": adk_available()}


@app.get("/api/plant-state", response_model=PlantState)
def plant_state() -> PlantState:
    return PLANT_STATE


@app.get("/api/baseline", response_model=BaselineResponse)
def baseline() -> BaselineResponse:
    return BASELINE


@app.get("/api/agents/status")
def agents_status() -> dict[str, object]:
    return {
        "mode": "live_adk" if adk_available() else "deterministic_fallback",
        "operator_approval_required": True,
        "agents": [agent.model_dump() for agent in LATEST_RESPONSE.recommendations],
    }


@app.post("/api/scenario/optimize", response_model=OptimizationResponse)
def scenario_optimize(scenario: ScenarioInput) -> OptimizationResponse:
    global LATEST_RESPONSE
    LATEST_RESPONSE = optimize_scenario(scenario)
    return LATEST_RESPONSE
