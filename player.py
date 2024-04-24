import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib
matplotlib.use('TkAgg')  # 修改后端为TkAgg

# 检查目录中最新的模型数据文件
def find_latest_model_data():
    files = os.listdir('.')
    model_data_files = [f for f in files if f.startswith('model_data') and f.endswith('.csv')]
    if model_data_files:
        latest_model_data_file = max(model_data_files)
        return latest_model_data_file
    else:
        return None

# 从最新的模型数据文件中加载数据
latest_model_data_file = find_latest_model_data()
if latest_model_data_file:
    model_data = pd.read_csv(latest_model_data_file)

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

    # 设置播放窗口标题为当前播放文件名
    plt.get_current_fig_manager().set_window_title(latest_model_data_file)

    # 播放动画
    plt.show()
else:
    print("No model data file found.")
