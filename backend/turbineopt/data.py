from __future__ import annotations

from .models import BaselineResponse, PlantState


PLANT_STATE = PlantState(
    plant_name="TurbineOpt Demo CCGT Campus",
    location="Synthetic AI data center energy island",
    configuration="2x1 combined-cycle block with grid interconnect",
    gas_turbines=2,
    steam_turbines=1,
    max_capacity_mw=720,
    current_load_mw=520,
    current_heat_rate_btu_per_kwh=6820,
    baseline_annual_fuel_cost=80_000_000,
    data_label="Synthetic demo data - not SCADA connected",
)


BASELINE = BaselineResponse(
    methodology=(
        "Savings are estimated against a normalized historical baseline using load, "
        "ambient temperature, humidity, turbine availability, compressor fouling, "
        "maintenance status, gas price, and grid price."
    ),
    normalized_factors=[
        "Data center load profile",
        "Ambient temperature and humidity",
        "Natural gas price",
        "Grid buy and sell prices",
        "Turbine availability",
        "Compressor fouling",
        "Maintenance risk",
        "Carbon price",
    ],
    historical_months=[
        {"month": "Jan", "load_mw": 486, "heat_rate": 6750, "fuel_cost_m": 6.1},
        {"month": "Feb", "load_mw": 492, "heat_rate": 6765, "fuel_cost_m": 6.0},
        {"month": "Mar", "load_mw": 501, "heat_rate": 6790, "fuel_cost_m": 6.3},
        {"month": "Apr", "load_mw": 512, "heat_rate": 6815, "fuel_cost_m": 6.5},
        {"month": "May", "load_mw": 526, "heat_rate": 6880, "fuel_cost_m": 6.8},
        {"month": "Jun", "load_mw": 548, "heat_rate": 6960, "fuel_cost_m": 7.2},
        {"month": "Jul", "load_mw": 563, "heat_rate": 7045, "fuel_cost_m": 7.5},
        {"month": "Aug", "load_mw": 558, "heat_rate": 7025, "fuel_cost_m": 7.4},
        {"month": "Sep", "load_mw": 541, "heat_rate": 6950, "fuel_cost_m": 7.0},
        {"month": "Oct", "load_mw": 519, "heat_rate": 6860, "fuel_cost_m": 6.7},
        {"month": "Nov", "load_mw": 503, "heat_rate": 6795, "fuel_cost_m": 6.4},
        {"month": "Dec", "load_mw": 491, "heat_rate": 6760, "fuel_cost_m": 6.1},
    ],
    baseline_heat_rate_btu_per_kwh=6820,
    baseline_fuel_cost_annual=80_000_000,
)

