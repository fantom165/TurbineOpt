import {
  AlertTriangle,
  BadgeDollarSign,
  BarChart3,
  CheckCircle2,
  Factory,
  Flame,
  Gauge,
  LineChart,
  ShieldCheck,
  Zap
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { defaultScenario, getBaseline, getPlantState, optimizeScenario, presets } from './api';
import type { AgentRecommendation, BaselineResponse, OptimizationResponse, PlantState, ScenarioInput } from './types';

const money = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });
const compactMoney = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', notation: 'compact', maximumFractionDigits: 1 });
const number = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 });

function formatMoney(value: number) {
  return money.format(value);
}

function App() {
  const [scenario, setScenario] = useState<ScenarioInput>(defaultScenario);
  const [result, setResult] = useState<OptimizationResponse | null>(null);
  const [plant, setPlant] = useState<PlantState | null>(null);
  const [baseline, setBaseline] = useState<BaselineResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runOptimization(nextScenario = scenario) {
    setLoading(true);
    setError(null);
    try {
      const response = await optimizeScenario(nextScenario);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Optimization failed');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    Promise.all([getPlantState(), getBaseline(), optimizeScenario(defaultScenario)])
      .then(([plantResponse, baselineResponse, optimizationResponse]) => {
        setPlant(plantResponse);
        setBaseline(baselineResponse);
        setResult(optimizationResponse);
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Unable to load demo'));
  }, []);

  const savings = result?.savings;
  const agentContributionMax = useMemo(
    () => Math.max(...(result?.recommendations.map((agent) => agent.contribution_usd) ?? [1])),
    [result]
  );

  return (
    <main className="app-shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">Synthetic advisory POC</p>
          <h1>TurbineOpt</h1>
          <p className="subhead">Guaranteed fuel cost reduction for jet-powered AI data centers.</p>
        </div>
        <div className="approval-pill">
          <ShieldCheck size={18} />
          Operator approval required
        </div>
      </section>

      {error && <div className="error-banner">Backend unavailable: {error}. Start FastAPI on port 8000.</div>}

      <section className="hero-grid">
        <div className="executive-card primary-card">
          <div className="card-header">
            <div>
              <p className="eyebrow">Annualized value at current scenario</p>
              <h2>{savings ? formatMoney(savings.gross_savings_annual) : 'Loading'}</h2>
            </div>
            <BadgeDollarSign size={34} />
          </div>
          <div className="split-metric">
            <span>Customer keeps</span>
            <strong>{savings ? formatMoney(savings.customer_share_annual) : '-'}</strong>
          </div>
          <div className="split-metric">
            <span>TurbineOpt gain-share</span>
            <strong>{savings ? formatMoney(savings.turbineopt_revenue_annual) : '-'}</strong>
          </div>
          <div className="note">No savings, no fee. 30% of verified gross savings.</div>
        </div>

        <MetricCard icon={<Flame />} label="Fuel cost avoided" value={savings ? `${savings.savings_pct}%` : '-'} detail="Normalized baseline delta" />
        <MetricCard icon={<Gauge />} label="Heat-rate improvement" value={savings ? `${savings.heat_rate_improvement_pct}%` : '-'} detail={`${savings?.optimized_heat_rate_btu_per_kwh ?? '-'} Btu/kWh optimized`} />
        <MetricCard icon={<Factory />} label="CO2 change" value={savings ? `${number.format(Math.abs(savings.emissions_delta_tons_annual))} tons` : '-'} detail="Annual emissions avoided" />
        <MetricCard icon={<CheckCircle2 />} label="Confidence" value={savings ? `${Math.round(savings.confidence * 100)}%` : '-'} detail="Scenario-specific advisory confidence" />
      </section>

      <section className="workspace-grid">
        <ScenarioPanel scenario={scenario} setScenario={setScenario} onRun={runOptimization} loading={loading} />

        <div className="panel chart-panel">
          <PanelTitle icon={<BarChart3 />} title="Baseline vs Optimized Fuel Cost" />
          {result && <CostChart result={result} />}
        </div>

        <div className="panel chart-panel">
          <PanelTitle icon={<LineChart />} title="24-Hour Dispatch Profile" />
          {result && <DispatchChart result={result} />}
        </div>

        <div className="panel dispatch-panel">
          <PanelTitle icon={<Zap />} title="Dispatch Decision" />
          {result && (
            <>
              <div className="decision">{result.dispatch.decision.replace(/_/g, ' ')}</div>
              <p>{result.dispatch.summary}</p>
              <div className="dispatch-grid">
                <MiniStat label="Self-generation" value={`${result.dispatch.self_generation_mw} MW`} />
                <MiniStat label="Grid purchase" value={`${result.dispatch.grid_purchase_mw} MW`} />
                <MiniStat label="Excess sale" value={`${result.dispatch.excess_sale_mw} MW`} />
                <MiniStat label="Self cost" value={money.format(result.dispatch.marginal_self_cost_per_mwh)} />
              </div>
            </>
          )}
        </div>
      </section>

      <section className="lower-grid">
        <div className="panel agents-panel">
          <PanelTitle icon={<Factory />} title="Agent Recommendations" />
          <div className="agents-list">
            {result?.recommendations.map((agent) => (
              <AgentRow key={agent.name} agent={agent} max={agentContributionMax} />
            ))}
          </div>
        </div>

        <div className="panel">
          <PanelTitle icon={<ShieldCheck />} title="Measurement Methodology" />
          <p className="methodology">{baseline?.methodology}</p>
          <div className="factor-list">
            {baseline?.normalized_factors.map((factor) => <span key={factor}>{factor}</span>)}
          </div>
          <div className="baseline-strip">
            <MiniStat label="Baseline heat rate" value={`${baseline?.baseline_heat_rate_btu_per_kwh ?? '-'} Btu/kWh`} />
            <MiniStat label="Baseline fuel cost" value={baseline ? compactMoney.format(baseline.baseline_fuel_cost_annual) : '-'} />
            <MiniStat label="Data source" value={plant?.data_label ?? 'Synthetic'} />
          </div>
        </div>
      </section>
    </main>
  );
}

function ScenarioPanel({
  scenario,
  setScenario,
  onRun,
  loading
}: {
  scenario: ScenarioInput;
  setScenario: (scenario: ScenarioInput) => void;
  onRun: (scenario?: ScenarioInput) => void;
  loading: boolean;
}) {
  function update(key: keyof ScenarioInput, value: number) {
    setScenario({ ...scenario, [key]: value });
  }

  return (
    <div className="panel scenario-panel">
      <PanelTitle icon={<Gauge />} title="Scenario Controls" />
      <div className="preset-row">
        {Object.entries(presets).map(([name, preset]) => (
          <button
            key={name}
            className="preset-button"
            onClick={() => {
              setScenario(preset);
              onRun(preset);
            }}
          >
            {name}
          </button>
        ))}
      </div>
      <Slider label="Data center load" unit="MW" min={150} max={900} value={scenario.data_center_load_mw} onChange={(value) => update('data_center_load_mw', value)} />
      <Slider label="Ambient temp" unit="F" min={20} max={120} value={scenario.ambient_temp_f} onChange={(value) => update('ambient_temp_f', value)} />
      <Slider label="Humidity" unit="%" min={0} max={100} value={scenario.humidity_pct} onChange={(value) => update('humidity_pct', value)} />
      <Slider label="Gas price" unit="$/MMBtu" min={1} max={20} step={0.25} value={scenario.gas_price_per_mmbtu} onChange={(value) => update('gas_price_per_mmbtu', value)} />
      <Slider label="Grid price" unit="$/MWh" min={0} max={300} value={scenario.grid_price_per_mwh} onChange={(value) => update('grid_price_per_mwh', value)} />
      <Slider label="Turbine availability" unit="%" min={50} max={100} value={scenario.turbine_availability_pct} onChange={(value) => update('turbine_availability_pct', value)} />
      <Slider label="Compressor fouling" unit="%" min={0} max={15} step={0.5} value={scenario.compressor_fouling_pct} onChange={(value) => update('compressor_fouling_pct', value)} />
      <Slider label="Maintenance risk" unit="%" min={0} max={100} value={scenario.maintenance_risk_pct} onChange={(value) => update('maintenance_risk_pct', value)} />
      <button className="run-button" onClick={() => onRun()} disabled={loading}>
        {loading ? 'Optimizing' : 'Run Optimization'}
      </button>
    </div>
  );
}

function Slider({
  label,
  value,
  min,
  max,
  step = 1,
  unit,
  onChange
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  unit: string;
  onChange: (value: number) => void;
}) {
  return (
    <label className="slider-row">
      <span>
        {label}
        <strong>
          {value} {unit}
        </strong>
      </span>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(event) => onChange(Number(event.target.value))} />
    </label>
  );
}

function MetricCard({ icon, label, value, detail }: { icon: React.ReactNode; label: string; value: string; detail: string }) {
  return (
    <div className="executive-card metric-card">
      <div className="metric-icon">{icon}</div>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}

function PanelTitle({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <div className="panel-title">
      {icon}
      <h3>{title}</h3>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="mini-stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function CostChart({ result }: { result: OptimizationResponse }) {
  const baseline = result.savings.baseline_fuel_cost_annual;
  const optimized = result.savings.optimized_fuel_cost_annual;
  return (
    <div className="bar-chart">
      <Bar label="Baseline" value={baseline} max={baseline} tone="baseline" />
      <Bar label="Optimized" value={optimized} max={baseline} tone="optimized" />
      <Bar label="Customer share" value={result.savings.customer_share_annual} max={baseline} tone="share" />
      <Bar label="TurbineOpt share" value={result.savings.turbineopt_revenue_annual} max={baseline} tone="revenue" />
    </div>
  );
}

function Bar({ label, value, max, tone }: { label: string; value: number; max: number; tone: string }) {
  return (
    <div className="bar-row">
      <span>{label}</span>
      <div className="bar-track">
        <div className={`bar-fill ${tone}`} style={{ width: `${Math.max(4, (value / max) * 100)}%` }} />
      </div>
      <strong>{compactMoney.format(value)}</strong>
    </div>
  );
}

function DispatchChart({ result }: { result: OptimizationResponse }) {
  const maxLoad = Math.max(...result.timeline.map((point) => point.load_mw));
  return (
    <div className="dispatch-chart">
      {result.timeline.map((point) => (
        <div className="hour-column" key={point.hour}>
          <div className="hour-stack" title={`${point.hour}:00 ${point.load_mw} MW`}>
            <div className="self-gen" style={{ height: `${(point.self_generation_mw / maxLoad) * 100}%` }} />
            <div className="grid-gen" style={{ height: `${(point.grid_mw / maxLoad) * 100}%` }} />
          </div>
          <span>{point.hour % 4 === 0 ? point.hour : ''}</span>
        </div>
      ))}
    </div>
  );
}

function AgentRow({ agent, max }: { agent: AgentRecommendation; max: number }) {
  return (
    <article className="agent-row">
      <div className="agent-heading">
        <div>
          <h4>{agent.name}</h4>
          <span>{agent.role}</span>
        </div>
        <RiskBadge risk={agent.risk} />
      </div>
      <p>{agent.recommendation}</p>
      <div className="agent-progress">
        <div style={{ width: `${Math.max(6, (agent.contribution_usd / max) * 100)}%` }} />
      </div>
      <div className="agent-footer">
        <span>{compactMoney.format(agent.contribution_usd)} attributed</span>
        <span>{Math.round(agent.confidence * 100)}% confidence</span>
      </div>
    </article>
  );
}

function RiskBadge({ risk }: { risk: AgentRecommendation['risk'] }) {
  return (
    <span className={`risk risk-${risk}`}>
      {risk === 'high' && <AlertTriangle size={14} />}
      {risk} risk
    </span>
  );
}

export { App };
