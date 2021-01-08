# model.py
from mesa import Agent, Model
from mesa.time import RandomActivation
import random
import matplotlib.pyplot as plt
from mesa.space import MultiGrid
import numpy
from mesa.datacollection import DataCollector
from mesa.batchrunner import BatchRunner
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule
from mesa.visualization.UserParam import UserSettableParameter
import time
import csv

import os

os.system('kill $(lsof -t -i:8521)')


def agent_portrayal(agent):
    portrayal = {
        "Shape": "circle",
        "Color": "red",
        "Filled": "true",
        "Layer": 0,
        "r": 0.5
    }
    if agent.type == "human":
        portrayal["Color"] = 'rgb('+str(agent.age*2) + \
            ','+str(agent.age*2)+','+str(agent.age*2)+')'
        portrayal["Layer"] = 0
        portrayal["r"] = agent.age/100
    if agent.type == "human" and agent.infected == True:
        portrayal["Color"] = 'rgb(255,0,0)'
        portrayal["Layer"] = 0
        portrayal["r"] = agent.age/100
    if agent.type == "human" and agent.immune == True:
        portrayal["Color"] = 'rgb(0,255,0)'
        portrayal["Layer"] = 0
        portrayal["r"] = agent.age/100
    if agent.type == "human" and agent.alive == False:
        portrayal["Color"] = 'rgb(0,0,255)'
        portrayal["Layer"] = 0
        portrayal["r"] = 0.8
    if agent.type == "virion":
        portrayal["Color"] = "red"
        portrayal["Layer"] = 1
        portrayal["r"] = 0.2
    return portrayal


class Human(Agent):

    # an agent with fixed initial wealth
    def __init__(self, unique_id, model, person, viral_decay_factor, viral_in_vivo_replication_and_age_factor, since_infection_recovery_factor):
        super().__init__(unique_id, model)
        self.viral_in_vivo_replication_and_age_factor = viral_in_vivo_replication_and_age_factor
        self.viral_decay_factor = viral_decay_factor
        self.type = "human"
        self.age = person['age']
        self.time_since_infection = 0
        self.immune = False
        self.susceptibility = 70
        self.alive = True
        self.viral_loads = []
        self.since_infection_recovery_factor = since_infection_recovery_factor
        self.chance_of_death = person['death_chance_percentage']
        # self.health = 100 - self.age
        self.infected = False

    def getViralLoadSum(self):
        sum = 0
        for load in self.viral_loads:
            sum = sum + load
        # print("viral load:",sum)
        return sum 

    def viralLoadIncrease(self):
        for index, load in enumerate(self.viral_loads, start=0):
            self.viral_loads[index] = load * (
                self.age*self.viral_in_vivo_replication_and_age_factor/2*(self.time_since_infection+1))

    def step(self):
        if self.immune == True:
            self.move()
            return
        if self.alive == False:
            return
        viral_load2 = self.getViralLoadSum()
        self.viralLoadIncrease()
        viral_load = self.getViralLoadSum()

        if viral_load > 10:
            self.infected = True
        else:
            self.infected = False

        # if self.alive == True and rand1 <=chance1:
        #     self.alive = False
        #     self.infected = False
        #     self.model.grid._remove_agent(self.pos, self)
        #     return

        if viral_load > 0:
            self.time_since_infection = self.time_since_infection + 1

        if self.time_since_infection * 50 >= self.age/self.since_infection_recovery_factor:
            self.infected = False
            self.immune = False
            self.viral_loads = []
            self.alive = True
            self.time_since_infection = 0
        # agent step  method
        # if self.age == 65:

        self.move()

        # self.model.schedule.remove(self)

    def move(self):
        viral_load = self.getViralLoadSum()
        rand1 = random.randrange(10000*365)
        chance1 = self.chance_of_death*10000
        # if self.infected == True and rand1 <= chance1*100 and self.alive == True:
        #     self.alive = False
        #     self.infected = False
        #     self.viral_loads = []
            # self.model.grid._remove_agent(self.pos, self)
            # return
        agefactor = (35000000000 / (self.age + 1))
        if viral_load / 100000  >= agefactor and self.alive and self.time_since_infection > 10 == True:
            print("viral load:",viral_load,"age:",self.age , "agefactor:",agefactor)
            self.alive = False
            self.infected = False
            self.viral_loads = []
            # self.model.grid._remove_agent(self.pos, self)

        else:
            if self.alive == True:
                possible_steps = self.model.grid.get_neighborhood(
                    self.pos, moore=True, include_center=False)
                new_position = random.choice(possible_steps)
                if len(possible_steps) > 0:
                    self.model.grid.move_agent(self, new_position)

        if self.alive:
            self.checkForSignalHere()
        if viral_load > 0 and self.alive:
            self.sendSignals(viral_load)

    def checkForSignalHere(self):
        cellMates = self.model.grid.get_cell_list_contents(self.pos)
        for cell in cellMates:
            if cell.type == "virion" and self.immune == False and random.randrange(100) < self.age:
                self.viral_loads.append(1)

    def sendSignals(self, viral_load):
        a = virion(self.model.num_agents+1, self.model,
                   self.age/5, self.viral_decay_factor)
        self.model.num_agents += 1
        a.type = "virion"
        x, y = self.pos
        self.model.grid.place_agent(a, (x, y))
        self.model.schedule.add(a)


class virion(Agent):

    # an agent with fixed initial wealth
    def __init__(self, unique_id, model, strength, viral_decay_factor):
        super().__init__(unique_id, model)
        self.viral_decay_factor = viral_decay_factor
        self.strength = strength

        self.type = "virion"

    def step(self):

        self.move()
        x, y = self.pos

        self.strength = self.strength - self.viral_decay_factor

        if self.strength <= 0:

            self.model.grid._remove_agent(self.pos, self)
            self.model.schedule.remove(self)

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False)
        new_position = random.choice(possible_steps)

        self.model.grid.move_agent(self, new_position)


def get_infected_old(model):
    sum = 0
    for agent in model.schedule.agents:

        if agent.type == "human" and agent.infected == True and agent.age == 65:
            sum = sum + 1

    return sum


def get_infected_current(model):
    sum = 0
    for agent in model.schedule.agents:

        if agent.type == "human" and agent.infected == True:
            sum = sum + 1

    return sum


def get_infected_all(model):
    sum = 0
    for agent in model.schedule.agents:

        if agent.type == "human" and agent.time_since_infection > 0:
            sum = sum + 1

    return sum


def get_deseased_all(model):
    sum = 0
    for agent in model.schedule.agents:

        if agent.type == "human" and agent.alive == False:
            sum = sum + 1

    return sum


def get_infected_young(model):
    sum = 0
    for agent in model.schedule.agents:

        if agent.type == "human" and agent.infected == True and agent.age == 25:
            sum = sum + 1

    return sum


class CovidModel(Model):
    def normalize(self, values, actual_bounds, desired_bounds):
        return [desired_bounds[0] + (int(x) - int(actual_bounds[0])) * (desired_bounds[1] - desired_bounds[0]) / (int(actual_bounds[1]) - int(actual_bounds[0])) for x in values]

    def get_list_bounds(self, val_list):
        min_val = min(val_list)
        max_val = max(val_list)
        return (min_val, max_val)

    def generatePeople(self, selectedCount):
        total = 0
        people = []
        prob_of_death_list = {}
        file = open("./prob_death.csv", "r")
        for line in file:
            lineSplittedList = line.split(',')
            dt = {}
            dt[str(lineSplittedList[0])] = {"male": float(
                lineSplittedList[1]), "female": float(lineSplittedList[2])}
            prob_of_death_list[str(lineSplittedList[0])] = {"male": float(
                lineSplittedList[1]), "female": float(lineSplittedList[2])}
        for age_group in self.population_pyramid:
            total = total + \
                int(age_group["male_population"]) + \
                int(age_group["female_population"])

        for age_group in self.population_pyramid:
            age_group["male_population"] = int(
                age_group["male_population"])/total
            age_group["female_population"] = int(
                age_group["female_population"])/total
        while len(people) <= selectedCount:
            for age_group in self.population_pyramid:
                if random.randrange(100) < age_group["female_population"]*100:
                    age_random_in_range = random.randrange(
                        int(age_group["age_from"]), int(age_group["age_to"]), 1)
                    people.append({"sex": "female", "age": age_random_in_range, "death_chance_percentage": float(
                        prob_of_death_list[str(age_random_in_range)]["female"])})
                if random.randrange(100) < age_group["male_population"]*100:
                    age_random_in_range = random.randrange(
                        int(age_group["age_from"]), int(age_group["age_to"]), 1)
                    people.append({"death_chance_percentage": float(prob_of_death_list[str(
                        age_random_in_range)]["male"]), "sex": "male", "age": age_random_in_range})
        return people

    # Model with some number of agents
    def __init__(self, since_infection_recovery_factor, viral_in_vivo_replication_and_age_factor, viral_decay_factor, choice_location, number_of_infected_people, number_of_people, width, height):
        list_data = []
        with open('./population_pyramid/'+choice_location+'.csv', newline='') as f:
            reader = csv.reader(f)
            lista = list(reader)
            lista = lista[1:]
            data = []
            for entry in lista:
                prep_entry = {}
                ages = entry[0].split('-')

                if len(ages) == 2:
                    prep_entry["age_from"] = ages[0]
                    prep_entry["age_to"] = ages[1]
                else:
                    prep_entry["age_from"] = ages[0][:-1]
                    prep_entry["age_to"] = str(int(ages[0][:-1]) + 20)

                prep_entry["male_population"] = entry[1]
                prep_entry["female_population"] = entry[2]
                data.append(prep_entry)

        self.population_pyramid = data
        people = self.generatePeople(number_of_people)
        self.startTime = int(round(time.time() * 1000))
        self.num_agents = len(people)
        self.kill_agents = []
        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(width, height, True)
        self.datacollector = DataCollector(
            {"deseased_all": get_deseased_all, "infections_current":  get_infected_current, "all_infections_including_transient": get_infected_all
             })
        # cr4eate some agents
        for i in range(len(people)):
            a = Human(i, self, people[i], viral_decay_factor,
                      viral_in_vivo_replication_and_age_factor, since_infection_recovery_factor)
            a.type = "human"
            x = random.randrange(self.grid.width)
            y = random.randrange(self.grid.height)
            if random.randrange(number_of_people) < number_of_infected_people:
                a.infected = True
                a.viral_loads = [10]
            self.grid.place_agent(a, (x, y))
            self.schedule.add(a)

        self.running = True
        # add the agent to models grid

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)


choices = []
file = open("./locations_ppopulation_pyramid.txt", "r")
for line in file:
    for one in line.split(','):
        choices.append(one)

choice_location = UserSettableParameter('choice', 'selected location', value='Italy-2019',
                                        choices=choices)
n_slider_number_of_people = UserSettableParameter(
    'slider', "Number of People", 300, 2, 500, 1)

n_slider_number_of_infected_people = UserSettableParameter(
    'slider', "Number of Infected People", 30, 0, 200, 1)
n_slider_since_infection_recovery_factor = UserSettableParameter(
    'slider', "since_infection_recovery_factor", 1, 1, 5, 1)
n_slider_viral_decay_factor = UserSettableParameter(
    'slider', "viral decay", 1, 1, 5, 1)


n_slider_viral_in_vivo_replication_and_age_factor = UserSettableParameter(
    'slider', "in_vivo_replication_and_age_factor", 1, 1, 5, 1)


chart_deseased = ChartModule([{"Label": "deseased_all",
                               "Color": "Black"}],
                             data_collector_name='datacollector')
chart_current_infection = ChartModule([{"Label": "infections_current",
                                        "Color": "Black"}],
                                      data_collector_name='datacollector')
chart_all_infections = ChartModule([{"Label": "all_infections_including_transient",
                                     "Color": "Black"}],
                                   data_collector_name='datacollector')
grid = CanvasGrid(agent_portrayal, 50, 50, 800, 800)

server = ModularServer(CovidModel,
                       [chart_all_infections, chart_deseased,
                           chart_current_infection, grid],
                       "Covid Model",
                       {"since_infection_recovery_factor": n_slider_since_infection_recovery_factor, "viral_decay_factor": n_slider_viral_decay_factor,
                        "viral_in_vivo_replication_and_age_factor": n_slider_viral_in_vivo_replication_and_age_factor, "choice_location": choice_location, "number_of_infected_people": n_slider_number_of_infected_people, "number_of_people": n_slider_number_of_people, "width": 50, "height": 50})
server.launch()


# server = ModularServer(CovidModel,
#                        [chart_young,chart_old,chart_all, grid ],
#                        "Covid Model",
#                        { "choice_location":choice_location, "number_of_people":n_slider_number_of_people, "younger": n_slider_younger, "older": n_slider_older, "width": 50, "height": 50})
# server.launch()
