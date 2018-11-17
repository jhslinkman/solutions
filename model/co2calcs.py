"""CO2 Calcs module.

Computes reductions in CO2-equivalent emissions.
"""

import math

import numpy as np
import pandas as pd

import advanced_controls


class CO2Calcs:
  """CO2 Calcs module.
    Arguments:
    ac = advanced_cost.py object, storing settings to control
      model operation.
    """
  def __init__(self, ac):
    self.ac = ac

  def co2_mmt_reduced(self, co2_reduced_grid_emissions, co2_replaced_grid_emissions,
      co2eq_direct_reduced_emissions, co2eq_reduced_fuel_emissions,
      co2eq_net_indirect_emissions, co2_increased_grid_usage_emissions):
    """CO2 MMT Reduced
       Annual CO2 reductions by region and year are calculated by adding reduced emissions
       derived from the electric grid, the replaced emissions derived from clean renewables,
       the net direct emissions derived from non-electric/non-fuel consumption, and the reduced
       emissions derived from fuel efficiency, and then subtracting the net indirect emissions.
       Most solutions will not utilize all of the defined factors.

       NOTE: The emissions values used are from the regional future grid BAU CO2 emission
       intensity values (by year) from the AMPERE 3 MESSAGE Base model used in the IPCC 5th
       Assessment Report WG3.

       CO2 MMT Reduced = (Grid Emissions Reduced + Grid Emissions Replaced - Grid Emissions by Solution)
         + Fuel Emissions Avoided + Direct Emissions Reduced - Net Indirect Emissions
       'CO2 Calcs'!A9:K55
    """
    m = pd.DataFrame(0.0, columns=co2_reduced_grid_emissions.columns.copy(),
        index=co2_reduced_grid_emissions.index.copy(), dtype=np.float64)
    m.index = m.index.astype(int)
    s = self.ac.report_start_year
    e = self.ac.report_end_year
    m = m.add(co2_reduced_grid_emissions.loc[s:e], fill_value=0)
    m = m.add(co2_replaced_grid_emissions.loc[s:e], fill_value=0)
    m = m.sub(co2_increased_grid_usage_emissions.loc[s:e], fill_value=0)
    m = m.add(co2eq_direct_reduced_emissions.loc[s:e], fill_value=0)
    m = m.add(co2eq_reduced_fuel_emissions.loc[s:e], fill_value=0)
    m = m.sub(co2eq_net_indirect_emissions.loc[s:e], fill_value=0)
    m.name = "co2_mmt_reduced"
    return m

  def co2eq_mmt_reduced(self, co2eq_reduced_grid_emissions, co2eq_replaced_grid_emissions,
      co2eq_increased_grid_usage_emissions,
      co2eq_direct_reduced_emissions, co2eq_reduced_fuel_emissions, co2eq_net_indirect_emissions):
    """CO2-eq MMT Reduced
       Annual CO2-eq reductions by region are calculated by multiplying the estimated energy
       unit savings by region by the emission factor of the energy unit in question by region
       and year. In this sample the values used are the regional future grid BAU CO2-eq emission
       intensity values (by year) from the AMPERE 3 MESSAGE Base model used in the IPCC 5th
       Assessment Report WG3.

       Reduced Grid MMT CO2-eq Emissions = NEU(t) * EF(e,t)

       where
          NEU(t) = Net Energy Units at time, t
          EF(e,t) = CO2-eq Emissions Factor of REF energy grid at time, t
       'CO2 Calcs'!A64:K110
    """
    m = pd.DataFrame(0.0, columns=co2eq_reduced_grid_emissions.columns.copy(),
        index=co2eq_reduced_grid_emissions.index.copy(), dtype=np.float64)
    m.index = m.index.astype(int)
    s = self.ac.report_start_year
    e = self.ac.report_end_year
    m = m.add(co2eq_reduced_grid_emissions.loc[s:e], fill_value=0)
    m = m.add(co2eq_replaced_grid_emissions.loc[s:e], fill_value=0)
    m = m.sub(co2eq_increased_grid_usage_emissions.loc[s:e], fill_value=0)
    m = m.add(co2eq_direct_reduced_emissions.loc[s:e], fill_value=0)
    m = m.add(co2eq_reduced_fuel_emissions.loc[s:e], fill_value=0)
    m = m.sub(co2eq_net_indirect_emissions.loc[s:e], fill_value=0)
    m.name = "co2eq_mmt_reduced"
    return m

  def co2_ppm_calculator(self, co2_mmt_reduced, co2eq_mmt_reduced):
    """CO2 parts per million reduction over time calculator.

       Each yearly reduction in CO2 (in million metric ton - MMT) is modeled as a
       discrete avoided pulse. A Simplified atmospheric lifetime function for CO2 is
       taken from Myhrvald and Caldeira (2012) based on the Bern Carbon Cycle model.
       Atmospheric tons of CO2 are converted to parts per million CO2 based on the
       molar mass of CO2 and the moles of atmosphere. CO2-eq emissions are treated
       as CO2 for simplicity and due to the lack of detailed information on emissions
       of other GHGs. If these other GHGs are a significant part of overall reductions,
       this model may not be appropriate.

       'CO2 Calcs'!A119:AW165
    """
    columns = ["PPM", "Total"] + list(range(2015, 2061))
    ppm_calculator = pd.DataFrame(0, columns=columns,
        index=co2_mmt_reduced.index.copy(), dtype=np.float64)
    ppm_calculator.index = ppm_calculator.index.astype(int)
    first_year = ppm_calculator.first_valid_index()
    last_year = ppm_calculator.last_valid_index()
    for year in ppm_calculator.index:
      if year < self.ac.report_start_year:
        continue
      b = co2eq_mmt_reduced.loc[year, "World"] if self.ac.emissions_use_co2eq else co2_mmt_reduced.loc[year, "World"]
      for delta in range(1, last_year - first_year + 1):
        if (year + delta - 1) > last_year:
          break
        val = 0.217
        val += 0.259 * math.exp(-delta / 172.9)
        val += 0.338 * math.exp(-delta / 18.51)
        val += 0.186 * math.exp(-delta / 1.186)
        ppm_calculator.loc[year + delta - 1, year] = b * val
    ppm_calculator.loc[:, "Total"] = ppm_calculator.sum(axis=1)
    for year in ppm_calculator.index:
      ppm_calculator.loc[year, "PPM"] = ppm_calculator.loc[year, "Total"] / (44.01 * 1.8 * 100)
    ppm_calculator.name = "co2_ppm_calculator"
    return ppm_calculator

  def co2eq_ppm_calculator(self, co2_ppm_calculator, ch4_ppm_calculator):
    """PPM calculations for CO2, CH4, and CO2-eq from other sources.
       'CO2 Calcs'!A171:F217
    """
    ppm_calculator = pd.DataFrame(0,
        columns=["CO2-eq PPM", "CO2 PPM", "CH4 PPB", "CO2 RF", "CH4 RF"],
        index=co2_ppm_calculator.index.copy(), dtype=np.float64)
    ppm_calculator.index = ppm_calculator.index.astype(int)
    ppm_calculator["CO2 PPM"] = co2_ppm_calculator["PPM"]
    ppm_calculator["CO2 RF"] = ppm_calculator["CO2 PPM"].apply(co2_rf)
    ppm_calculator["CH4 PPB"] = ch4_ppm_calculator["PPB"]
    ppm_calculator["CH4 RF"] = ppm_calculator["CH4 PPB"].apply(ch4_rf)
    s = ppm_calculator["CO2 RF"] + ppm_calculator["CH4 RF"]
    ppm_calculator["CO2-eq PPM"] = s.apply(co2eq_ppm)
    return ppm_calculator

  def co2_reduced_grid_emissions(self, soln_pds_net_grid_electricity_units_saved,
      conv_ref_grid_CO2_per_KWh):
    """Reduced Grid Emissions = NE(t) * EF(e,t)

       where
          NE(t) = Net Energy Units at time, t
          EF(e,t) = CO2 Emissions Factor of REF energy grid at time, t
       'CO2 Calcs'!A234:K280
    """
    return soln_pds_net_grid_electricity_units_saved * conv_ref_grid_CO2_per_KWh

  def co2_replaced_grid_emissions(self, soln_net_annual_funits_adopted,
      conv_ref_grid_CO2_per_KWh):
    """CO2 Replaced Grid Emissions = NAFU(Sol,t) * EF(e,t)  (i.e. only direct emissions)
       where
          NAFU(Sol,t) = Net annual functional units captured by solution at time, t
          EF(e,t) = CO2 Emissions Factor of REF energy grid at time, t
       'CO2 Calcs'!R234:AB280
    """
    if self.ac.solution_category == advanced_controls.SOLUTION_CATEGORY.REPLACEMENT:
      return soln_net_annual_funits_adopted * conv_ref_grid_CO2_per_KWh
    else:
      return soln_net_annual_funits_adopted * 0

  def co2_increased_grid_usage_emissions(self,
      soln_pds_net_grid_electricity_units_used, conv_ref_grid_CO2_per_KWh):
    """Increased Grid Emissions (MMT CO2e) = NEU(t) * EF(e,t)

       where
          NEU(t) = Net Energy Units Used at time, t
          EF(e,t) = CO2 Emissions Factor of REF energy grid at time, t
       'CO2 Calcs'!AI234:AS280
    """
    return soln_pds_net_grid_electricity_units_used * conv_ref_grid_CO2_per_KWh

  def co2eq_reduced_grid_emissions(self, soln_pds_net_grid_electricity_units_saved,
      conv_ref_grid_CO2eq_per_KWh):
    """Reduced Grid MMT CO2-eq Emissions = NEU(t) * EF(e,t)

       where
          NEU(t) = Net Energy Units at time, t
          EF(e,t) = CO2-eq Emissions Factor of REF energy grid at time, t
       'CO2 Calcs'!A288:K334
    """
    return soln_pds_net_grid_electricity_units_saved * conv_ref_grid_CO2eq_per_KWh

  def co2eq_replaced_grid_emissions(self, soln_net_annual_funits_adopted,
      conv_ref_grid_CO2eq_per_KWh):
    """CO2-equivalent replaced Grid MMT CO2-eq Emissions = NAFU(Sol,t) * EF(e,t)

       where
          NAFU(Sol,t) = Net annual functional units captured by solution at time, t
          EF(e,t) = CO2-eq Emissions Factor of REF energy grid at time, t
       'CO2 Calcs'!R288:AB334
    """
    if self.ac.solution_category == advanced_controls.SOLUTION_CATEGORY.REPLACEMENT:
      return soln_net_annual_funits_adopted * conv_ref_grid_CO2eq_per_KWh
    else:
      return soln_net_annual_funits_adopted * 0

  def co2eq_increased_grid_usage_emissions(self,
      soln_pds_net_grid_electricity_units_used, conv_ref_grid_CO2eq_per_KWh):
    """Increased Grid Emissions (MMT CO2e) = NEU(t) * EF(e,t)

       where
          NEU(t) = Net Energy Units Used at time, t
          EF(e,t) = CO2-eq Emissions Factor of REF energy grid at time, t
       'CO2 Calcs'!AI288:AS334
    """
    return soln_pds_net_grid_electricity_units_used * conv_ref_grid_CO2eq_per_KWh

  def co2eq_direct_reduced_emissions(self, soln_pds_direct_co2_emissions_saved,
      soln_pds_direct_ch4_co2_emissions_saved, soln_pds_direct_n2o_co2_emissions_saved):
    """Direct MMT CO2-eq Emissions Reduced = [DEm(Con,t) - DEm(Sol,t)]  / 1000000

       where
          DEm(Con,t) = Direct Emissions of Conventional at time, t
          DEm(Sol,t) = Direct Emissions of Solution at time, t

          NOTE: Includes CH4-CO2-eq and N2O-CO2-eq
       'CO2 Calcs'!A344:K390
    """
    return (soln_pds_direct_co2_emissions_saved/1000000 +
        soln_pds_direct_ch4_co2_emissions_saved/1000000 +
        soln_pds_direct_n2o_co2_emissions_saved/1000000)

  def co2eq_reduced_fuel_emissions(self, soln_net_annual_funits_adopted, fuel_in_liters=False):
    """Reduced Fuel Emissions MMT CO2-eq =
        NAFU(Con,t) * Fuel(Con,t) * [Em(cf) -  (1 - FRF) * Em(sf) * if(Fuel Units are Same,
            then: 1, else:UCF)]/10^6

        where:
          NAFU(Con,t) = Net annual functional units captured by conventional mix at time, t
          Fuel(Con,t) = Conventional Fuel Consumption at time, t
          FRF = Fuel Efficiency Factor
          Em(cf) = Emissions Factor of conventional fuel type
          Em(sf) = Emissions Factor of solution fuel type
          UCF = Unit Conversion Factor (TJ per Liter or L per TJ depending on
            Conventional and Solution Fuel units.
       'CO2 Calcs'!U344:AE390
    """
    factor = self.ac.fuel_emissions_factor - self.ac.fuel_emissions_factor_2 * self.ac.soln_fuel_learning_rate
    factor *= self.ac.conv_fuel_consumed_per_funit
    result = soln_net_annual_funits_adopted * factor / 1000000
    result.name = "co2eq_reduced_fuel_emissions"
    if fuel_in_liters:
      raise NotImplementedError("fuel_in_liters=True not handled")
    return result

  def co2eq_net_indirect_emissions(self, soln_pds_new_iunits_reqd, soln_ref_new_iunits_reqd,
      conv_ref_new_iunits_reqd, soln_net_annual_funits_adopted):
    """Net Indirect Emissions MMT CO2-eq by implementation unit (t) =
          [NIU (Sol,t) * IEm (Sol,t)] - [NIU (Cont.) * IEm (Con,t)]  /  1000000
       where:
          NIU(Sol,t) = New Implementation Units by solution at time, t
          IEm(Sol,t) = Indirect CO2-eq Emission of solution at time, t
          NIU(Con,t) = New Implementation Units by conventional mix at time, t
          IEm(Con,t) = Indirect CO2-eq Emission of conventional mix at time, t
       'CO2 Calcs'!AP344:AZ390
    """
    if self.ac.conv_indirect_co2_is_iunits:
      delta = soln_pds_new_iunits_reqd - soln_ref_new_iunits_reqd
      result = (delta * self.ac.soln_indirect_co2_per_iunit)
      result += conv_ref_new_iunits_reqd * self.ac.conv_indirect_co2_per_unit
    else:
      result = soln_net_annual_funits_adopted * self.ac.soln_indirect_co2_per_iunit
      result -= soln_net_annual_funits_adopted * self.ac.conv_indirect_co2_per_unit
    result /= 1000000
    return result


# The following formulae come from the SolarPVUtil Excel implementation of 27Aug18.
# There was no explanation of where they came from or what they really mean.

def co2_rf(x):
  original_co2 = 400
  return 5.35 * math.log((original_co2 + x) / original_co2)

def f(M, N):
  return 0.47 * math.log(1 + 2.01 * 10**-5 * (M * N)**0.75 + 5.31 * 10**-15 * M * (M * N)**1.52)

def ch4_rf(x):
  original_ch4 = 1800
  original_n2o = 320
  indirect_ch4_forcing_scalar = 0.97 / 0.641
  old_M = original_ch4
  new_M = original_ch4 + x
  N = original_n2o
  return indirect_ch4_forcing_scalar * 0.036 * (new_M**0.5 - old_M**0.5) - f(new_M, N) + f(old_M, N)

def co2eq_ppm(x):
  original_co2 = 400
  return (original_co2 * math.exp(x / 5.35)) - original_co2