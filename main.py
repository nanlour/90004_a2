import math
import random

import numpy as np
import pandas as pd
from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation
import time
import multiprocessing
from scipy.optimize import curve_fit


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
    def get_muscle_mass(model):
        return model.muscle_mass

    def get_anabolic_hormone_mean(agent):
        return agent.anabolic_hormone_mean

    def get_catabolic_hormone_mean(agent):
        return agent.catabolic_hormone_mean

    def __init__(self, width, height, intensity, hours_of_sleep, days_between_workouts, slow_twitch_fibers):
        super().__init__()
        self.schedule = RandomActivation(self)

        # Arguments that can be changed
        self.lift_weights = True
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
            model_reporters={"Muscle Mass": self.get_muscle_mass,
                             "Anabolic Hormone": self.get_anabolic_hormone_mean,
                             "Catabolic Hormone": self.get_catabolic_hormone_mean}
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
        self.catabolic_hormone_mean = sum(a.catabolic_hormone for a in self.schedule.agents) / len(self.schedule.agents)
        self.anabolic_hormone_mean = sum(a.anabolic_hormone for a in self.schedule.agents) / len(self.schedule.agents)
        self.datacollector.collect(self)

        for a in self.schedule.agents:
            a.perform_daily_activity()

        if (self.lift_weights and self.schedule.time % self.days_between_workouts == 0):
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

    def run_simulation(self, steps):
        for _ in range(steps):
            self.step()
        return self.datacollector.get_model_vars_dataframe()


# 模型参数
width = 17
height = 17
intensity = 95
hours_of_sleep = 8
days_between_workouts = 2
slow_twitch_fibers = 0.5
steps = 1000  # 模拟步数

# 模拟时间戳
timestamp = time.strftime("%Y%m%d%H%M%S")

# 创建模型
model = MuscleModel(width, height, intensity, hours_of_sleep, days_between_workouts, slow_twitch_fibers)

# 并行执行模拟
def run_simulation_parallel(model_instance_steps):
    model_instance, steps = model_instance_steps
    return model_instance.run_simulation(steps)

if __name__ == "__main__":
    start_time = time.time()

    # 创建模型实例列表
    model_instances = [(MuscleModel(width, height, intensity, hours_of_sleep, days_between_workouts, slow_twitch_fibers), steps) for _ in range(32)]

    # 使用32进程并行执行模拟
    with multiprocessing.Pool() as pool:
        results = pool.map(run_simulation_parallel, model_instances)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Simulation completed in {elapsed_time} seconds")

    # 生成输出文件
    for i, result in enumerate(results):
        file_name = f"model_data_intensity_{intensity}_sleep_{hours_of_sleep}_workout_{days_between_workouts}_fibers_{slow_twitch_fibers}_steps_{steps}_{timestamp}_{i}.csv"
        result.to_csv(file_name)

    # 合并多个模拟的结果
    merged_result = pd.concat(results)

    # 去除极端值
    # 此处您可以根据需要进行调整，比如使用标准差或其他方法来检测和移除极端值
    merged_result = merged_result[(
                np.abs(merged_result['Muscle Mass'] - merged_result['Muscle Mass'].mean()) < 3 * merged_result[
            'Muscle Mass'].std())]


    # 曲线拟合
    def func(x, a, b, c):
        return a * np.exp(-b * x) + c


    popt, _ = curve_fit(func, merged_result.index, merged_result['Muscle Mass'])

    # 生成拟合曲线的数据
    fit_x = np.linspace(merged_result.index.min(), merged_result.index.max(), 1000)
    fit_y = func(fit_x, *popt)

    # 绘制拟合曲线
    import matplotlib.pyplot as plt

    plt.plot(merged_result.index, merged_result['Muscle Mass'], 'b.', label='Data')
    plt.plot(fit_x, fit_y, 'r-', label='Fit')
    plt.xlabel('Time')
    plt.ylabel('Muscle Mass')
    plt.legend()
    plt.show()
