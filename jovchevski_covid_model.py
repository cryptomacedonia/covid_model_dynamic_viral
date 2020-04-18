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
        portrayal["Color"] = "black" if agent.age > 50 else "green"
        portrayal["Layer"] = 0
        portrayal["r"] = 1.0
    if agent.type == "virion":
        portrayal["Color"] = "red"
        portrayal["Layer"] = 1
        portrayal["r"] = 0.2
    return portrayal


class HumanOld(Agent):

    # an agent with fixed initial wealth
    def __init__(self, unique_id, model, age):
        super().__init__(unique_id, model)
        self.type = "human"
        self.age = age
        self.time_since_infection = 0
        self.immune =  False
        # self.health = 100 - self.age
        self.infected = False
        self.susceptibility = 30
    def step(self):

        # agent step  method
        # if self.age == 65:
        self.move()
        if self.infected == False:
            self.checkForSignalHere()
        else:
            self.sendSignals()

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False)

        new_position = random.choice(possible_steps)

        self.model.grid.move_agent(self, new_position)
        if self.infected:
            self.time_since_infection  = self.time_since_infection + 1

        if self.time_since_infection >=300:
            self.infected =  False
            self.immune = True
            self.time_since_infection = 0

    def checkForSignalHere(self):
        cellMates = self.model.grid.get_cell_list_contents(self.pos)
        for cell in cellMates:
            if cell.type == "virion" and self.immune == False and random.randrange(100) < self.susceptibility:
                self.infected = True
                self.time_since_infection = 0

    def sendSignals(self):
        a = virion(self.model.num_agents+1, self.model, self,3)
        self.model.num_agents += 1
        a.type = "virion"
        x, y = self.pos
        self.model.grid.place_agent(a, (x, y))
        self.model.schedule.add(a)


class HumanYoung(Agent):

    # an agent with fixed initial wealth
    def __init__(self, unique_id, model, age):
        super().__init__(unique_id, model)
        self.type = "human"
        self.age = age
        self.time_since_infection = 0
        self.immune = False
        self.susceptibility = 70
        # self.health = 100 - self.age
        self.infected = False

    def step(self):

        # agent step  method
        # if self.age == 65:
        self.move()
        if self.infected == False:
            self.checkForSignalHere()
        else:
            self.sendSignals()

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False)
        new_position = random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)
        if self.infected:
            self.time_since_infection  = self.time_since_infection + 1

        if self.time_since_infection >=30:
            self.infected =  False
            self.immune = True
            self.time_since_infection = 0

    def checkForSignalHere(self):
        cellMates = self.model.grid.get_cell_list_contents(self.pos)
        for cell in cellMates:
            if cell.type == "virion" and self.immune == False and random.randrange(100) < self.susceptibility:
                self.infected = True
                self.time_since_infection = 0

    def sendSignals(self):
        a = virion(self.model.num_agents+1, self.model, self,6)
        self.model.num_agents += 1
        a.type = "virion"
        x, y = self.pos
        self.model.grid.place_agent(a, (x, y))
        self.model.schedule.add(a)


class virion(Agent):

    # an agent with fixed initial wealth
    def __init__(self, unique_id, model, originatingStemCell,strength):
        super().__init__(unique_id, model)
        self.originatingStemCell = originatingStemCell
        self.strength = strength
       
        self.type = "virion"

    def step(self):

        self.move()
        x, y = self.pos

        self.strength -= 4

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
def get_infected_all(model):
    sum = 0
    for agent in model.schedule.agents:

        if agent.type == "human" and agent.infected == True :
            sum = sum + 1

   
    return sum    
def get_infected_young(model):
    sum = 0
    for agent in model.schedule.agents:

        if agent.type == "human" and agent.infected == True and agent.age == 25:
            sum = sum + 1

   
    return sum

class CovidModel(Model):

    # Model with some number of agents
    def __init__(self, younger, older, width, height):
        self.startTime = int(round(time.time() * 1000))
        self.num_agents = younger+older+1
        self.kill_agents = []
        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(width, height, True)
        self.datacollector = DataCollector(
            {"infected_old":  get_infected_old,"infected_young":  get_infected_young,"infected_all":  get_infected_all
             })
        # cr4eate some agents

        for i in range(older):
            a = HumanOld(i, self, 65)
            a.type = "human"
            a.age = 65

            x = random.randrange(self.grid.width)
            y = random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))
            self.schedule.add(a)

        for i2 in range(younger):
            a2 = HumanYoung(i2+older, self, 25)
            a2.type = "human"
            a2.age = 25
            x = random.randrange(self.grid.width)
            y = random.randrange(self.grid.height)
            self.grid.place_agent(a2, (x, y))
            self.schedule.add(a2)
        a = HumanYoung(younger+older+1, self, 25)
        a.type = "human"
        a.age = 25
        a.infected = True
        x = random.randrange(self.grid.width)
        y = random.randrange(self.grid.height)
        self.grid.place_agent(a, (x, y))
        self.schedule.add(a)
        # for a in all:

        self.running = True
        # add the agent to models grid

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)

n_slider_younger = UserSettableParameter(
    'slider', "Number of Younger", 10, 2, 200, 1)
n_slider_older = UserSettableParameter(
    'slider', "Number of Older", 10, 2, 200, 1)

chart_young = ChartModule([{"Label": "infected_young",
                      "Color": "Black"}],
                    data_collector_name='datacollector')
chart_old = ChartModule([{"Label": "infected_old",
                      "Color": "Black"}],
                    data_collector_name='datacollector')      
chart_all = ChartModule([{"Label": "infected_all",
                      "Color": "Black"}],
                    data_collector_name='datacollector')                
grid = CanvasGrid(agent_portrayal, 50, 50, 800, 800)

server = ModularServer(CovidModel,
                       [chart_young,chart_old,chart_all, grid ],
                       "Covid Model",
                       {"younger": n_slider_younger, "older": n_slider_older, "width": 50, "height": 50})
server.launch()
