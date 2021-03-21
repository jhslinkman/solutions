""" Shared features in LAND solutions """
import solution.factory
import pandas as pd


MHA_TO_HA = 1000000

# Gets the total land allocation per moisture regime.
# Set per_aez to True to get land totals per each AEZ
# Returns pd.Series
def get_land_totals(per_aez=False):
    # It doesn't matter which solution or scenario is used here.
    # Under the hood, each solution looks at the same set of files in data/land/world/2020/
    scenario = solution.factory.one_solution_scenarios("peatlands")[0]()
    d = scenario.ae.our_land_alloc_dict

    tuples = []
    values = []
    for mr in d.keys():
        for aez in d[mr].keys():
            tuples.append((mr, aez))
            values.append(d[mr][aez]['TOTAL'] / 10000)
    index = pd.MultiIndex.from_tuples(tuples, names=['Moisture Regime', 'AEZ'])
    series = pd.Series(values, index=index)

    scope = [0] if not per_aez else [0,1]
    return series.sum(level=scope)