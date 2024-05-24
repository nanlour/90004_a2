import math
import random

from args import args

class MuscleFiber():
    def __init__(self):
        self.max_size = 4
        self.anabolic_hormone = 50
        self.catabolic_hormone = 52
        self.nutrient = 0

        for _ in range(20):
            if random.random() > MuscleModel.slow_twitch_fibers:
                self.max_size += 1

        self.fiber_size = (0.2 + random.random() * 0.4) * self.max_size

    def __regulate_nutrient(self):
        self.nutrient = min(MuscleModel.nutrient_max, self.nutrient)

    def get_nutrient(self):
        self.nutrient += MuscleModel.nutrient
        self.__regulate_nutrient()

    def perform_daily_activity(self):
        self.catabolic_hormone += 2.0 * math.log10(self.fiber_size)
        self.anabolic_hormone += 2.5 * math.log10(self.fiber_size)

    def lift_weights(self):
        if random.random() < (MuscleModel.intensity / 100) ** 2:
            self.catabolic_hormone += math.log10(self.fiber_size) * 44
            self.anabolic_hormone += math.log10(self.fiber_size) * 55

    def sleep(self):
        sleep_hours = MuscleModel.getSleepHours()
        self.catabolic_hormone -= math.log10(self.catabolic_hormone) * 0.5 * sleep_hours
        self.anabolic_hormone -= math.log10(self.anabolic_hormone) * 0.48 * sleep_hours

    def regulate_hormones(self):
        self.anabolic_hormone = min(MuscleModel.anabolic_hormone_max, self.anabolic_hormone)
        self.anabolic_hormone = max(MuscleModel.anabolic_hormone_min, self.anabolic_hormone)
        self.catabolic_hormone = min(MuscleModel.catabolic_hormone_max, self.catabolic_hormone)
        self.catabolic_hormone = max(MuscleModel.catabolic_hormone_min, self.catabolic_hormone)

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


class MuscleModel():
    # Constants
    anabolic_hormone_max = 200
    catabolic_hormone_max = 250
    anabolic_hormone_min = 50
    catabolic_hormone_min = 52
    hormone_diffuse_rate = 0.75
    nutrient_max = 100

    # Arguments
    width = args["width"]
    height = args["height"]
    lift_weights = args["lift_weights"]
    hours_of_sleep = args["hours_of_sleep"]
    sleep_variance_range = args['sleep_variance_range']
    intensity = args["intensity"]
    days_between_workouts = args["days_between_workouts"]
    slow_twitch_fibers = args["slow_twitch_fibers"]
    nutrient = args['nutrient']

    def __init__(self):
        # Output data
        self.time = 0
        self.muscle_mass = 0
        self.anabolic_hormone_mean = 50
        self.catabolic_hormone_mean = 52
        self.data = [["Time","muscle", "anabolic","catabolic"]]

        self.muscle_fiber_grid = [[MuscleFiber() for _ in range(self.width)] for _ in range(self.height)]
    
    def __get_neighbors(self, x, y):
        return [((y - 1) % self.height, (x - 1) % self.width), ((y - 1) % self.height, x), ((y - 1) % self.height, (x + 1) % self.width), ((y + 1) % self.height, (x - 1) % self.width), ((y + 1) % self.height, x), ((y + 1) % self.height, (x + 1) % self.width), (y, (x - 1) % self.width), (y, (x + 1) % self.width)]

    def __diffuse(self):
        new_values_anabolic = [[0 for _ in range(self.width)] for _ in range(self.height)]
        new_values_catabolic = [[0 for _ in range(self.width)] for _ in range(self.height)]

        for y in range(self.height):
            for x in range(self.width):
                new_values_anabolic[y][x] += self.muscle_fiber_grid[y][x].anabolic_hormone * (1 - self.hormone_diffuse_rate)
                new_values_catabolic[y][x] += self.muscle_fiber_grid[y][x].catabolic_hormone * (1 - self.hormone_diffuse_rate)

                for y_, x_ in self.__get_neighbors(x, y):
                    new_values_anabolic[y_][x_] += self.muscle_fiber_grid[y][x].anabolic_hormone * self.hormone_diffuse_rate / 8
                    new_values_catabolic[y_][x_] += self.muscle_fiber_grid[y][x].catabolic_hormone * self.hormone_diffuse_rate / 8

        for y in range(self.height):
            for x in range(self.width):
                self.muscle_fiber_grid[y][x].anabolic_hormone = new_values_anabolic[y][x]
                self.muscle_fiber_grid[y][x].catabolic_hormone = new_values_catabolic[y][x]

    def getSleepHours():
        sleep_hours = random.uniform(MuscleModel.hours_of_sleep - MuscleModel.sleep_variance_range, MuscleModel.hours_of_sleep + MuscleModel.sleep_variance_range)
        return sleep_hours

    def step(self):
        self.muscle_mass = sum(muscle_fiber.fiber_size for row in self.muscle_fiber_grid for muscle_fiber in row) / 100
        self.catabolic_hormone_mean = sum(muscle_fiber.catabolic_hormone for row in self.muscle_fiber_grid for muscle_fiber in row) / (self.height * self.width)
        self.anabolic_hormone_mean = sum(muscle_fiber.anabolic_hormone for row in self.muscle_fiber_grid for muscle_fiber in row) / (self.height * self.width)
        self.data.append([self.time, self.muscle_mass, self.anabolic_hormone_mean, self.catabolic_hormone_mean])

        for y in range(self.height):
            for x in range(self.width):
                self.muscle_fiber_grid[y][x].perform_daily_activity()

        if (self.lift_weights and self.time % self.days_between_workouts == 0):
            for y in range(self.height):
                for x in range(self.width):
                    self.muscle_fiber_grid[y][x].lift_weights()

        for y in range(self.height):
            for x in range(self.width):
                self.muscle_fiber_grid[y][x].sleep()

        self.__diffuse()

        for y in range(self.height):
            for x in range(self.width):
                self.muscle_fiber_grid[y][x].regulate_hormones()

        for y in range(self.height):
            for x in range(self.width):
                self.muscle_fiber_grid[y][x].get_nutrient()
                self.muscle_fiber_grid[y][x].develop_muscle()

        self.time += 1


model = MuscleModel()
for i in range(args["simluate_time"]):
    model.step()

filename = "model_data.csv"

with open(filename, 'w') as file:
    for row in model.data:
        str_row = [str(item) for item in row]
        file.write(','.join(str_row) + '\n')
