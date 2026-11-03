from turbineopt.models import ScenarioInput
from turbineopt.simulation import dispatch_decision, optimize_scenario


def test_optimization_response_has_positive_savings_for_default_scenario():
    response = optimize_scenario(ScenarioInput())

    assert response.operator_approval_required is True
    assert response.savings.gross_savings_annual > 0
    assert response.savings.optimized_fuel_cost_annual < response.savings.baseline_fuel_cost_annual
    assert len(response.recommendations) == 7
    assert len(response.timeline) == 24


def test_dispatch_buys_grid_when_grid_is_cheaper_than_self_generation():
    scenario = ScenarioInput(gas_price_per_mmbtu=12, grid_price_per_mwh=42)
    decision = dispatch_decision(scenario)

    assert decision.decision == "buy_from_grid"
    assert decision.grid_purchase_mw > 0


def test_high_maintenance_risk_caps_aggressive_dispatch():
    scenario = ScenarioInput(maintenance_risk_pct=90, gas_price_per_mmbtu=3.6, grid_price_per_mwh=140)
    response = optimize_scenario(scenario)
    maintenance = next(agent for agent in response.recommendations if agent.name == "Maintenance Agent")

    assert maintenance.risk == "high"
    assert response.savings.confidence < 0.75


def test_agent_fallback_is_deterministic_without_credentials():
    first = optimize_scenario(ScenarioInput(data_center_load_mw=610))
    second = optimize_scenario(ScenarioInput(data_center_load_mw=610))

    assert first.recommendations == second.recommendations
    assert first.savings == second.savings

