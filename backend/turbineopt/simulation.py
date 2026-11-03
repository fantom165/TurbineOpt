from __future__ import annotations

import math

from .data import PLANT_STATE
from .models import (
    AgentRecommendation,
    DispatchDecision,
    OptimizationResponse,
    SavingsResult,
    ScenarioInput,
    TimeSeriesPoint,
)

HOURS_PER_YEAR = 8760
MMBTU_PER_BTU = 1_000_000
MWH_TO_KWH = 1000
CO2_TON_PER_MMBTU_NAT_GAS = 0.05306
GAIN_SHARE = 0.30


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def baseline_heat_rate(scenario: ScenarioInput) -> float:
    temp_penalty = max(0, scenario.ambient_temp_f - 59) * 9.5
    humidity_penalty = scenario.humidity_pct * 1.8
    fouling_penalty = scenario.compressor_fouling_pct * 75
    risk_penalty = scenario.maintenance_risk_pct * 2.2
    derate_penalty = max(0, 100 - scenario.turbine_availability_pct) * 18
    return 6400 + temp_penalty + humidity_penalty + fouling_penalty + risk_penalty + derate_penalty


def optimization_improvement_pct(scenario: ScenarioInput) -> float:
    base = 0.021
    fouling_gain = min(0.016, scenario.compressor_fouling_pct * 0.0025)
    dispatch_gain = 0.011 if scenario.grid_price_per_mwh < marginal_self_cost(scenario) else 0.006
    weather_gain = 0.006 if scenario.ambient_temp_f > 82 else 0.003
    maintenance_cap = 1 - clamp((scenario.maintenance_risk_pct - 65) / 120, 0, 0.32)
    return clamp((base + fouling_gain + dispatch_gain + weather_gain) * maintenance_cap, 0.012, 0.067)


def marginal_self_cost(scenario: ScenarioInput) -> float:
    heat_rate = baseline_heat_rate(scenario)
    return (heat_rate / MMBTU_PER_BTU) * MWH_TO_KWH * scenario.gas_price_per_mmbtu


def calculate_savings(scenario: ScenarioInput) -> SavingsResult:
    baseline_hr = baseline_heat_rate(scenario)
    improvement = optimization_improvement_pct(scenario)
    optimized_hr = baseline_hr * (1 - improvement)

    annual_mwh = scenario.data_center_load_mw * HOURS_PER_YEAR
    baseline_mmbtu = baseline_hr * annual_mwh * MWH_TO_KWH / MMBTU_PER_BTU
    optimized_mmbtu = optimized_hr * annual_mwh * MWH_TO_KWH / MMBTU_PER_BTU
    baseline_cost = baseline_mmbtu * scenario.gas_price_per_mmbtu
    optimized_cost = optimized_mmbtu * scenario.gas_price_per_mmbtu

    gross_savings = max(0, baseline_cost - optimized_cost)
    turbineopt_revenue = gross_savings * GAIN_SHARE
    customer_share = gross_savings - turbineopt_revenue
    emissions_delta = (optimized_mmbtu - baseline_mmbtu) * CO2_TON_PER_MMBTU_NAT_GAS
    confidence = clamp(0.91 - scenario.maintenance_risk_pct / 350 - scenario.compressor_fouling_pct / 250, 0.68, 0.94)

    return SavingsResult(
        baseline_fuel_cost_annual=round(baseline_cost, 0),
        optimized_fuel_cost_annual=round(optimized_cost, 0),
        gross_savings_annual=round(gross_savings, 0),
        customer_share_annual=round(customer_share, 0),
        turbineopt_revenue_annual=round(turbineopt_revenue, 0),
        savings_pct=round((gross_savings / baseline_cost) * 100, 2) if baseline_cost else 0,
        baseline_heat_rate_btu_per_kwh=round(baseline_hr, 0),
        optimized_heat_rate_btu_per_kwh=round(optimized_hr, 0),
        heat_rate_improvement_pct=round(improvement * 100, 2),
        emissions_delta_tons_annual=round(emissions_delta, 0),
        confidence=round(confidence, 2),
    )


def dispatch_decision(scenario: ScenarioInput) -> DispatchDecision:
    available_mw = PLANT_STATE.max_capacity_mw * scenario.turbine_availability_pct / 100
    self_cost = marginal_self_cost(scenario)

    if scenario.grid_price_per_mwh + 6 < self_cost:
        grid_mw = min(scenario.data_center_load_mw * 0.22, scenario.data_center_load_mw)
        self_mw = scenario.data_center_load_mw - grid_mw
        decision = "buy_from_grid"
        summary = "Buy a controlled block from the grid while keeping turbines in an efficient operating band."
    elif available_mw > scenario.data_center_load_mw + 30 and scenario.sell_price_per_mwh > self_cost + 10:
        excess = min(available_mw - scenario.data_center_load_mw, 80)
        self_mw = scenario.data_center_load_mw + excess
        grid_mw = 0
        decision = "sell_excess"
        summary = "Generate above campus load and sell excess power while market spread is favorable."
    elif scenario.maintenance_risk_pct > 76:
        grid_mw = min(scenario.data_center_load_mw * 0.18, scenario.data_center_load_mw)
        self_mw = scenario.data_center_load_mw - grid_mw
        decision = "hybrid"
        summary = "Use a hybrid dispatch to avoid high-wear operating points until maintenance risk falls."
    else:
        grid_mw = 0
        self_mw = min(scenario.data_center_load_mw, available_mw)
        decision = "self_generate"
        summary = "Self-generate demand because marginal fuel economics beat grid purchase."

    excess_sale = max(0, self_mw - scenario.data_center_load_mw)
    return DispatchDecision(
        decision=decision,
        summary=summary,
        self_generation_mw=round(self_mw, 1),
        grid_purchase_mw=round(grid_mw, 1),
        excess_sale_mw=round(excess_sale, 1),
        marginal_self_cost_per_mwh=round(self_cost, 2),
        grid_price_per_mwh=round(scenario.grid_price_per_mwh, 2),
    )


def create_timeline(scenario: ScenarioInput, savings: SavingsResult, dispatch: DispatchDecision) -> list[TimeSeriesPoint]:
    points: list[TimeSeriesPoint] = []
    for hour in range(24):
        daily_shape = 1 + 0.055 * math.sin((hour - 7) / 24 * 2 * math.pi) + 0.025 * math.sin(hour / 24 * 4 * math.pi)
        load = scenario.data_center_load_mw * daily_shape
        self_share = dispatch.self_generation_mw / max(scenario.data_center_load_mw, 1)
        grid_share = dispatch.grid_purchase_mw / max(scenario.data_center_load_mw, 1)
        fuel_cost = load * savings.baseline_heat_rate_btu_per_kwh * scenario.gas_price_per_mmbtu / 1000
        optimized_cost = load * savings.optimized_heat_rate_btu_per_kwh * scenario.gas_price_per_mmbtu / 1000
        points.append(
            TimeSeriesPoint(
                hour=hour,
                load_mw=round(load, 1),
                self_generation_mw=round(load * self_share, 1),
                grid_mw=round(load * grid_share, 1),
                fuel_cost_usd=round(fuel_cost, 0),
                optimized_fuel_cost_usd=round(optimized_cost, 0),
            )
        )
    return points


def deterministic_agent_recommendations(
    scenario: ScenarioInput,
    savings: SavingsResult,
    dispatch: DispatchDecision,
) -> list[AgentRecommendation]:
    gross = savings.gross_savings_annual
    maint_risk = "high" if scenario.maintenance_risk_pct > 74 else "medium" if scenario.maintenance_risk_pct > 45 else "low"
    return [
        AgentRecommendation(
            name="Fuel Agent",
            role="Natural gas economics",
            recommendation="Lock next-day gas volume for the optimized heat-rate plan and avoid spot exposure during high-load hours.",
            confidence=0.88,
            contribution_usd=round(gross * 0.22, 0),
            rationale=f"Gas at ${scenario.gas_price_per_mmbtu:.2f}/MMBtu makes heat-rate reduction the largest savings lever.",
            risk="low",
        ),
        AgentRecommendation(
            name="Weather Agent",
            role="Ambient condition forecast",
            recommendation="Pre-position inlet cooling and adjust load split before the afternoon ambient-temperature penalty peaks.",
            confidence=0.84,
            contribution_usd=round(gross * 0.14, 0),
            rationale=f"{scenario.ambient_temp_f:.0f}F ambient temperature raises turbine heat rate and compressor work.",
            risk="medium" if scenario.ambient_temp_f > 95 else "low",
        ),
        AgentRecommendation(
            name="Dispatch Agent",
            role="Self-generate vs grid economics",
            recommendation=dispatch.summary,
            confidence=0.86,
            contribution_usd=round(gross * 0.24, 0),
            rationale=f"Marginal self-generation is ${dispatch.marginal_self_cost_per_mwh:.2f}/MWh vs grid at ${dispatch.grid_price_per_mwh:.2f}/MWh.",
            risk="low",
        ),
        AgentRecommendation(
            name="Maintenance Agent",
            role="Wear and outage risk",
            recommendation="Avoid aggressive ramping and reserve compressor wash planning until risk score declines.",
            confidence=0.81,
            contribution_usd=round(gross * 0.12, 0),
            rationale=f"Maintenance risk is {scenario.maintenance_risk_pct:.0f}%, so the optimizer caps high-wear recommendations.",
            risk=maint_risk,
        ),
        AgentRecommendation(
            name="Carbon Agent",
            role="Emissions and regulatory cost",
            recommendation="Use the optimized dispatch plan to reduce gas burn and report avoided emissions against normalized baseline.",
            confidence=0.9,
            contribution_usd=round(gross * 0.08, 0),
            rationale=f"Estimated annual emissions change is {savings.emissions_delta_tons_annual:,.0f} tons CO2.",
            risk="low",
        ),
        AgentRecommendation(
            name="Digital Twin Agent",
            role="Combined-cycle simulation",
            recommendation="Run the HRSG and steam turbine at the modeled recovery target while holding GT exhaust temperature inside advisory bounds.",
            confidence=0.83,
            contribution_usd=round(gross * 0.13, 0),
            rationale="The simulated combined-cycle block shows steam-side recovery improves without forcing excess GT fuel burn.",
            risk="medium" if scenario.compressor_fouling_pct > 8 else "low",
        ),
        AgentRecommendation(
            name="Master Optimization Agent",
            role="Cross-agent synthesis",
            recommendation="Approve the advisory plan for the next operating window and measure savings against the normalized baseline.",
            confidence=savings.confidence,
            contribution_usd=round(gross * 0.07, 0),
            rationale="Specialist recommendations converge on fuel reduction while preserving operator approval and maintenance constraints.",
            risk="medium" if scenario.maintenance_risk_pct > 60 else "low",
        ),
    ]


def optimize_scenario(scenario: ScenarioInput) -> OptimizationResponse:
    savings = calculate_savings(scenario)
    dispatch = dispatch_decision(scenario)
    recommendations = deterministic_agent_recommendations(scenario, savings, dispatch)
    timeline = create_timeline(scenario, savings, dispatch)
    assumptions = [
        "Synthetic data is used for POC demonstration only.",
        "All recommendations are advisory and require operator approval.",
        "Savings are measured against a normalized historical baseline.",
        "Optimization avoids operating points that materially increase maintenance risk.",
        "Gain-share example uses 30% of verified gross savings.",
    ]
    return OptimizationResponse(
        scenario=scenario,
        savings=savings,
        dispatch=dispatch,
        recommendations=recommendations,
        timeline=timeline,
        assumptions=assumptions,
    )
