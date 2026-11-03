import type { BaselineResponse, OptimizationResponse, PlantState, ScenarioInput } from './types';

export const defaultScenario: ScenarioInput = {
  data_center_load_mw: 520,
  ambient_temp_f: 88,
  humidity_pct: 62,
  gas_price_per_mmbtu: 4.25,
  grid_price_per_mwh: 92,
  sell_price_per_mwh: 74,
  turbine_availability_pct: 96,
  compressor_fouling_pct: 3.5,
  maintenance_risk_pct: 28,
  carbon_price_per_ton: 18
};

export const presets: Record<string, ScenarioInput> = {
  Base: defaultScenario,
  'Hot day': { ...defaultScenario, ambient_temp_f: 103, humidity_pct: 74 },
  'Gas spike': { ...defaultScenario, gas_price_per_mmbtu: 9.5, grid_price_per_mwh: 108 },
  'Grid price spike': { ...defaultScenario, grid_price_per_mwh: 215, sell_price_per_mwh: 148 },
  'Turbine derate': { ...defaultScenario, turbine_availability_pct: 82, maintenance_risk_pct: 58 },
  'AI demand surge': { ...defaultScenario, data_center_load_mw: 680, gas_price_per_mmbtu: 5.2, grid_price_per_mwh: 136 }
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export function getPlantState() {
  return request<PlantState>('/api/plant-state');
}

export function getBaseline() {
  return request<BaselineResponse>('/api/baseline');
}

export function optimizeScenario(scenario: ScenarioInput) {
  return request<OptimizationResponse>('/api/scenario/optimize', {
    method: 'POST',
    body: JSON.stringify(scenario)
  });
}

