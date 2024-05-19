import math
import random
import pandas as pd
from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation
from draw import draw_plot


class MuscleFiber(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.max_size = 4
        self.anabolic_hormone = 50
        self.catabolic_hormone = 52

        for _ in range(20):
            if random.random() > self.model.slow_twitch_fibers:
                self.max_size += 1

        self.fiber_size = (0.2 + random.random() * 0.4) * self.max_size

    def perform_daily_activity(self):
        self.catabolic_hormone += 2.0 * math.log10(self.fiber_size)
        self.anabolic_hormone += 2.5 * math.log10(self.fiber_size)

    def lift_weights(self):
        if random.random() < (self.model.intensity / 100) ** 2:
            self.catabolic_hormone += math.log10(self.fiber_size) * 44
            self.anabolic_hormone += math.log10(self.fiber_size) * 55

    def sleep(self):
        self.catabolic_hormone -= math.log10(self.catabolic_hormone) * 0.5 * self.model.hours_of_sleep
        self.anabolic_hormone -= math.log10(self.anabolic_hormone) * 0.48 * self.model.hours_of_sleep

    def regulate_hormones(self):
        self.anabolic_hormone = min(self.model.anabolic_hormone_max, self.anabolic_hormone)
        self.anabolic_hormone = max(self.model.anabolic_hormone_min, self.anabolic_hormone)
        self.catabolic_hormone = min(self.model.catabolic_hormone_max, self.catabolic_hormone)
        self.catabolic_hormone = max(self.model.catabolic_hormone_min, self.catabolic_hormone)

    def develop_muscle(self):
        self.__grow()
        self.__regulate_muscle_fibers()

    def __grow(self):
        self.fiber_size -= 0.20 * math.log10(self.catabolic_hormone)
        self.fiber_size += 0.20 * min(math.log10(self.anabolic_hormone), 1.05 * math.log10(self.catabolic_hormone))

    def __regulate_muscle_fibers(self):
        self.fiber_size = max(1, self.fiber_size)
        self.fiber_size = min(self.max_size, self.fiber_size)


class MuscleModel(Model):
    def __init__(self, width, height, lift_weights, hours_of_sleep, intensity, days_between_workouts,
                 slow_twitch_fibers):
        super().__init__()
        self.schedule = RandomActivation(self)

        # Arguments that can be changed
        self.lift_weights = lift_weights
        self.hours_of_sleep = hours_of_sleep
        self.intensity = intensity
        self.days_between_workouts = days_between_workouts
        self.slow_twitch_fibers = slow_twitch_fibers

        # Constants
        self.grid = MultiGrid(width, height, True)
        self.anabolic_hormone_max = 200
        self.catabolic_hormone_max = 250
        self.anabolic_hormone_min = 50
        self.catabolic_hormone_min = 52
        self.hormone_diffuse_rate = 0.75

        # Imporant data
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
            a.develop_muscle()

        self.schedule.step()


simluate_time = 100

width = 17
height = 17

lift_weights = True
hours_of_sleep = 8
intensity = 95
days_between_workouts = 2
slow_twitch_fibers = 0.5

model = MuscleModel(width, height, lift_weights, hours_of_sleep, intensity, days_between_workouts, slow_twitch_fibers)
for i in range(simluate_time):
    model.step()

model_data = model.datacollector.get_model_vars_dataframe()
model_data.to_csv('model_data.csv')

draw_plot()
