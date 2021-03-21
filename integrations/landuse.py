import solution.factory
peatlands_scenario = solution.factory.one_solution_scenarios("peatlands")

solution = peatlands_scenario[0]()

print(solution.ae.soln_land_alloc_df)
