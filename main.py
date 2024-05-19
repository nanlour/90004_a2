import math
import random
import numpy as np
import pandas as pd
from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation
from draw import draw_plot

from args import args

class MuscleFiber(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.max_size = 4
        self.anabolic_hormone = 50
        self.catabolic_hormone = 52
        self.nutrient = 0

        for _ in range(20):
            if random.random() > self.model.slow_twitch_fibers:
                self.max_size += 1

        self.fiber_size = (0.2 + random.random() * 0.4) * self.max_size

    def __regulate_nutrient(self):
        self.nutrient = min(self.model.nutrient_max, self.nutrient)

    def get_nutrient(self):
        self.nutrient += self.model.nutrient
        self.__regulate_nutrient()

    def perform_daily_activity(self):
        self.catabolic_hormone += 2.0 * math.log10(self.fiber_size)
        self.anabolic_hormone += 2.5 * math.log10(self.fiber_size)

    def lift_weights(self):
        if random.random() < (self.model.intensity / 100) ** 2:
            self.catabolic_hormone += math.log10(self.fiber_size) * 44
            self.anabolic_hormone += math.log10(self.fiber_size) * 55

    def sleep(self):
        sleep_hours = self.model.getSleepHours()
        self.catabolic_hormone -= math.log10(self.catabolic_hormone) * 0.5 * sleep_hours
        self.anabolic_hormone -= math.log10(self.anabolic_hormone) * 0.48 * sleep_hours

    def regulate_hormones(self):
        self.anabolic_hormone = min(self.model.anabolic_hormone_max, self.anabolic_hormone)
        self.anabolic_hormone = max(self.model.anabolic_hormone_min, self.anabolic_hormone)
        self.catabolic_hormone = min(self.model.catabolic_hormone_max, self.catabolic_hormone)
        self.catabolic_hormone = max(self.model.catabolic_hormone_min, self.catabolic_hormone)

    def develop_muscle(self):
        self.__grow()
        self.__regulate_muscle_fibers()

    def __grow(self):
        fiber_size_change = 0.20 * min(math.log10(self.anabolic_hormone), 1.05 * math.log10(self.catabolic_hormone)) - 0.20 * math.log10(self.catabolic_hormone)
        fiber_size_change = min(fiber_size_change, self.nutrient / 5000)
        if (fiber_size_change > 0):
            self.nutrient -= fiber_size_change * 5000
        self.fiber_size += fiber_size_change

    def __regulate_muscle_fibers(self):
        self.fiber_size = max(1, self.fiber_size)
        self.fiber_size = min(self.max_size, self.fiber_size)


class MuscleModel(Model):
    def __init__(self):
        super().__init__()
        self.schedule = RandomActivation(self)

        # Arguments that can be changed
        self.width = args["width"]
        self.height = args["height"]
        self.lift_weights = args["lift_weights"]
        self.hours_of_sleep = args["hours_of_sleep"]
        self.sleep_variance_range = args['sleep_variance_range']
        self.intensity = args["intensity"]
        self.days_between_workouts = args["days_between_workouts"]
        self.slow_twitch_fibers = args["slow_twitch_fibers"]
        self.nutrient = args['nutrient']

        # Constants
        self.grid = MultiGrid(self.width, self.height, True)
        self.anabolic_hormone_max = 200
        self.catabolic_hormone_max = 250
        self.anabolic_hormone_min = 50
        self.catabolic_hormone_min = 52
        self.hormone_diffuse_rate = 0.75
        self.nutrient_max = 100

        # Output data
        self.muscle_mass = 0
        self.anabolic_hormone_mean = 50
        self.catabolic_hormone_mean = 52

        for contents, (x, y) in self.grid.coord_iter():
            muscle_fiber = MuscleFiber((x, y), self)
            self.grid.place_agent(muscle_fiber, (x, y))
            self.schedule.add(muscle_fiber)

        self.datacollector = DataCollector(
            model_reporters={"Muscle Mass": lambda m: m.muscle_mass,
                             "Anabolic Hormone": lambda a: a.anabolic_hormone_mean,
                             "Catabolic Hormone": lambda c: c.catabolic_hormone_mean}
        )

    def __diffuse(self):
        new_values_anabolic = {agent: 0 for agent in self.schedule.agents}
        new_values_catabolic = {agent: 0 for agent in self.schedule.agents}

        for agent in self.schedule.agents:
            count = len(list(self.grid.get_neighbors(agent.pos, moore=True)))
            new_values_anabolic[agent] += agent.anabolic_hormone * (1 - self.hormone_diffuse_rate)
            new_values_catabolic[agent] += agent.catabolic_hormone * (1 - self.hormone_diffuse_rate)

            for neighbor in self.grid.get_neighbors(agent.pos, moore=True):
                new_values_anabolic[neighbor] += agent.anabolic_hormone * self.hormone_diffuse_rate / count
            for neighbor in self.grid.get_neighbors(agent.pos, moore=True):
                new_values_catabolic[neighbor] += agent.catabolic_hormone * self.hormone_diffuse_rate / count

        for agent, new_value in new_values_anabolic.items():
            agent.anabolic_hormone = new_value
        for agent, new_value in new_values_catabolic.items():
            agent.catabolic_hormone = new_value

    def getSleepHours(self):
        sleep_hours = -1
        while (sleep_hours < 0 or sleep_hours > self.hours_of_sleep * 2):
            sleep_hours = np.random.normal(self.hours_of_sleep, self.sleep_variance_range / 3)
        return sleep_hours

    def step(self):
        self.muscle_mass = sum(a.fiber_size for a in self.schedule.agents)
        self.catabolic_hormone_mean = sum(a.catabolic_hormone for a in self.schedule.agents) / len(self.agents)
        self.anabolic_hormone_mean = sum(a.anabolic_hormone for a in self.schedule.agents) / len(self.agents)
        self.datacollector.collect(self)

        for a in self.schedule.agents:
            a.perform_daily_activity()

        if (self.lift_weights and self._steps % self.days_between_workouts == 0):
            for a in self.schedule.agents:
                a.lift_weights()

        for a in self.schedule.agents:
            a.sleep()

        self.__diffuse()

        for a in self.schedule.agents:
            a.regulate_hormones()

        for a in self.schedule.agents:
            a.get_nutrient()
            a.develop_muscle()

        self.schedule.step()


model = MuscleModel()
for i in range(args["simluate_time"]):
    model.step()

model_data = model.datacollector.get_model_vars_dataframe()
model_data.to_csv('model_data.csv')

draw_plot()
