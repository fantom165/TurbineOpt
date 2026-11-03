from __future__ import annotations

from typing import Literal, Optional, Union

from pydantic import BaseModel, Field


class ScenarioInput(BaseModel):
    data_center_load_mw: float = Field(520, ge=150, le=900)
    ambient_temp_f: float = Field(88, ge=-10, le=125)
    humidity_pct: float = Field(62, ge=0, le=100)
    gas_price_per_mmbtu: float = Field(4.25, ge=1, le=30)
    grid_price_per_mwh: float = Field(92, ge=-50, le=600)
    sell_price_per_mwh: float = Field(74, ge=-50, le=600)
    turbine_availability_pct: float = Field(96, ge=50, le=100)
    compressor_fouling_pct: float = Field(3.5, ge=0, le=15)
    maintenance_risk_pct: float = Field(28, ge=0, le=100)
    carbon_price_per_ton: float = Field(18, ge=0, le=250)


class MetricCard(BaseModel):
    label: str
    value: float
    unit: str
    delta_pct: Optional[float] = None
    tone: Literal["positive", "neutral", "warning"] = "neutral"


class AgentRecommendation(BaseModel):
    name: str
    role: str
    recommendation: str
    confidence: float = Field(ge=0, le=1)
    contribution_usd: float
    rationale: str
    risk: Literal["low", "medium", "high"]


class DispatchDecision(BaseModel):
    decision: Literal["self_generate", "buy_from_grid", "sell_excess", "hybrid"]
    summary: str
    self_generation_mw: float
    grid_purchase_mw: float
    excess_sale_mw: float
    marginal_self_cost_per_mwh: float
    grid_price_per_mwh: float


class SavingsResult(BaseModel):
    baseline_fuel_cost_annual: float
    optimized_fuel_cost_annual: float
    gross_savings_annual: float
    customer_share_annual: float
    turbineopt_revenue_annual: float
    savings_pct: float
    baseline_heat_rate_btu_per_kwh: float
    optimized_heat_rate_btu_per_kwh: float
    heat_rate_improvement_pct: float
    emissions_delta_tons_annual: float
    confidence: float


class TimeSeriesPoint(BaseModel):
    hour: int
    load_mw: float
    self_generation_mw: float
    grid_mw: float
    fuel_cost_usd: float
    optimized_fuel_cost_usd: float


class OptimizationResponse(BaseModel):
    scenario: ScenarioInput
    savings: SavingsResult
    dispatch: DispatchDecision
    recommendations: list[AgentRecommendation]
    timeline: list[TimeSeriesPoint]
    assumptions: list[str]
    operator_approval_required: bool = True


class PlantState(BaseModel):
    plant_name: str
    location: str
    configuration: str
    gas_turbines: int
    steam_turbines: int
    max_capacity_mw: float
    current_load_mw: float
    current_heat_rate_btu_per_kwh: float
    baseline_annual_fuel_cost: float
    data_label: str


class BaselineResponse(BaseModel):
    methodology: str
    normalized_factors: list[str]
    historical_months: list[dict[str, Union[float, str]]]
    baseline_heat_rate_btu_per_kwh: float
    baseline_fuel_cost_annual: float
