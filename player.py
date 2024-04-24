# A simulator player for muscle growth based on the output of the model:main.py
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from IPython.display import clear_output
import time
import matplotlib
matplotlib.use('TkAgg')  # 修改后端为TkAgg

# 从CSV文件中加载模拟数据
model_data = pd.read_csv('model_data.csv')

# 创建一个图形对象
fig, ax = plt.subplots()
line, = ax.plot([], [], lw=2)
ax.set_xlim(0, len(model_data))
ax.set_ylim(model_data.min().min(), model_data.max().max())
ax.set_xlabel('Time Step')
ax.set_ylabel('Muscle Mass')


# 初始化函数，用于绘制空图形
def init():
    line.set_data([], [])
    return line,


# 更新函数，用于更新图形内容
def update(i):
    # 构建 x 数据，范围为 [0, 1, 2, ..., i]
    x_data = range(i + 1)
    # 获取对应的 y 数据
    y_data = model_data.iloc[:i + 1]['Muscle Mass']
    # 更新图形内容
    line.set_data(x_data, y_data)
    return line,



# 创建动画对象
ani = FuncAnimation(fig, update, frames=len(model_data), init_func=init, blit=True)

# 播放动画
plt.show()
