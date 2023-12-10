#!/usr/bin/env python
# coding: utf-8

# In[1]:


import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import networkx as nx

# Function to read DIMACS file and create a graph
def read_dimacs_file(file_path):
    G = nx.Graph()
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith('e'):
                _, node1, node2 = line.split()
                G.add_edge(int(node1), int(node2))
    return G

# File paths
zip_code_file = 'Zip Code of each County.csv'
population_file = 'Population of each County.csv'

# Read data
zip_code_data = pd.read_csv(zip_code_file)
population_data = pd.read_csv(population_file)

# Merge the zip code and population data
combined_data = pd.merge(zip_code_data, population_data, on='County Number')

# Read DIMACS file 
dimacs_file_path = 'MS.dimacs'
graph = read_dimacs_file(dimacs_file_path)

# Convert format
county_zip_code = combined_data.set_index('County Number')['Zip Code'].to_dict()
county_population = combined_data.set_index('County Number')['Population'].to_dict()

# Total number of counties and districts
N = 82  # Number of counties
D = 4   # Total number of districts

# Create a new model
model = gp.Model("Redistricting")

# Decision variables
x = model.addVars(graph.nodes, D, vtype=GRB.BINARY, name="x")

# Constraint: Each county in one district
model.addConstrs((gp.quicksum(x[i, j] for j in range(D)) == 1 for i in graph.nodes), "OneDistrict")

# Population balance constraints
total_population = sum(county_population.values())
average_population = total_population / D
tolerance = 0.005
model.addConstrs((gp.quicksum(county_population.get(i, 0) * x[i, j] for i in graph.nodes) <= average_population * (1 + tolerance) for j in range(D)), "PopulationUpperBound")
model.addConstrs((gp.quicksum(county_population.get(i, 0) * x[i, j] for i in graph.nodes) >= average_population * (1 - tolerance) for j in range(D)), "PopulationLowerBound")

# Contiguity constraints
for i in graph.nodes:
    for j in range(D):
        model.addConstr(gp.quicksum(x[n, j] for n in graph.neighbors(i)) >= x[i, j], f"Contiguity_{i}_{j}")

#Objective
objective = gp.quicksum(x[u, j] * x[v, j] for u, v in graph.edges for j in range(D))
model.setObjective(objective, GRB.MAXIMIZE)

# Optimize the model
model.optimize()

# Extracting and printing the results
if model.status == GRB.OPTIMAL:
    assignment = model.getAttr('x', x)
    for j in range(D):
        district_counties = [i for i in graph.nodes if assignment[i, j] > 0.5]
        print(f"District {j}: {district_counties}")


# In[ ]:




