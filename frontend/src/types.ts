export type ScenarioInput = {
  data_center_load_mw: number;
  ambient_temp_f: number;
  humidity_pct: number;
  gas_price_per_mmbtu: number;
  grid_price_per_mwh: number;
  sell_price_per_mwh: number;
  turbine_availability_pct: number;
  compressor_fouling_pct: number;
  maintenance_risk_pct: number;
  carbon_price_per_ton: number;
};

export type SavingsResult = {
  baseline_fuel_cost_annual: number;
  optimized_fuel_cost_annual: number;
  gross_savings_annual: number;
  customer_share_annual: number;
  turbineopt_revenue_annual: number;
  savings_pct: number;
  baseline_heat_rate_btu_per_kwh: number;
  optimized_heat_rate_btu_per_kwh: number;
  heat_rate_improvement_pct: number;
  emissions_delta_tons_annual: number;
  confidence: number;
};

export type AgentRecommendation = {
  name: string;
  role: string;
  recommendation: string;
  confidence: number;
  contribution_usd: number;
  rationale: string;
  risk: 'low' | 'medium' | 'high';
};

export type DispatchDecision = {
  decision: 'self_generate' | 'buy_from_grid' | 'sell_excess' | 'hybrid';
  summary: string;
  self_generation_mw: number;
  grid_purchase_mw: number;
  excess_sale_mw: number;
  marginal_self_cost_per_mwh: number;
  grid_price_per_mwh: number;
};

export type TimeSeriesPoint = {
  hour: number;
  load_mw: number;
  self_generation_mw: number;
  grid_mw: number;
  fuel_cost_usd: number;
  optimized_fuel_cost_usd: number;
};

export type OptimizationResponse = {
  scenario: ScenarioInput;
  savings: SavingsResult;
  dispatch: DispatchDecision;
  recommendations: AgentRecommendation[];
  timeline: TimeSeriesPoint[];
  assumptions: string[];
  operator_approval_required: boolean;
};

export type PlantState = {
  plant_name: string;
  location: string;
  configuration: string;
  gas_turbines: number;
  steam_turbines: number;
  max_capacity_mw: number;
  current_load_mw: number;
  current_heat_rate_btu_per_kwh: number;
  baseline_annual_fuel_cost: number;
  data_label: string;
};

export type BaselineResponse = {
  methodology: string;
  normalized_factors: string[];
  historical_months: Array<Record<string, number | string>>;
  baseline_heat_rate_btu_per_kwh: number;
  baseline_fuel_cost_annual: number;
};

