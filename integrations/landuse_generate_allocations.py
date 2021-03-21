import solution.factory
import pandas as pd
import pickle

try:
    with open('solutions_cache.pickle', 'rb') as f:
        solutions = pickle.load(f)
except FileNotFoundError:
    scenarios = solution.factory.all_solutions_scenarios()

    # Copied from the PD Solutions columns of the 'Discrete Solution' 
    # tab in excel
    desired_solutions = [
        'peatlands', # peatland protection &/| peatland restoration
        'afforestation',
        'bamboo',
        'forestprotection', #forest protection',
        # 'mangroverestoration', # <- generates KeyError when trying to run solution
        'tropicalforests', # tropical forest restoration',
        'temperateforests', # temperate forest restoration',
        # 'grasslandprotection', # <- generates KeyError when trying to run solution
        'multistrataagroforestry',
        'silvopasture',
        'managedgrazing',
        'tropicaltreestaples',
        'farmlandrestoration',
        'perennialbioenergy',
        'improvedrice',
        'conservationagriculture',
        'regenerativeagriculture',
        'treeintercropping',
        # 'biochar', # <- doesn't have an ae object associated with it
        'irrigationefficiency',
        'nutrientmanagement'
        ## The following models do not appear to be implemented
        # mangrove protection
        # ip forest management
        # sustainable forest management
        # Livestock Feed
        # SRI
        # Boreal Forest Restoration
        # Sustainable Intensification
    ]



    solutions = [(name, scenarios[name][0]()) for name in desired_solutions]

    # Caching the solutions models so we can more quickly iterate
    # with everything that follows
    with open('solutions_cache.pickle', 'wb') as f:
        solutions = pickle.dump(solutions, f)

all_land_allocs = []
for name, soln in solutions:
    df = soln.ae.soln_land_alloc_df.copy()
    df.index.name = 'tmr'
    df.reset_index(inplace=True)
    df['solution'] = name
    all_land_allocs.append(df)

## df here is a partial representation of the 'Discrete Solution',
## specifically, the 'Total %' columns (e.g., G18:G46)
df = pd.concat(all_land_allocs).set_index(['tmr', 'solution'])

