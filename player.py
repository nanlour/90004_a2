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
        the_latest_model_data_file = max(model_data_files)
        return the_latest_model_data_file
    else:
        return None


# 计算切线斜率
def calculate_slope(x_data, y_data, i):
    if i == 0:
        return 0  # 初始点，斜率为0
    else:
        delta_x = x_data[i] - x_data[i - 1]
        delta_y = y_data[i] - y_data[i - 1]
        return delta_y / delta_x


# 计算切线端点
def calculate_tangent_endpoints(x_data, y_data, i, slope, x_step_ratio):
    x = x_data[i]
    y = y_data[i]
    delta_x = (x_data[-1] - x_data[0]) * x_step_ratio
    delta_y = slope * delta_x
    return (x - delta_x, y - delta_y), (x + delta_x, y + delta_y)


# 从最新的模型数据文件中加载数据
latest_model_data_file = find_latest_model_data()
if latest_model_data_file:
    model_data = pd.read_csv(latest_model_data_file)

    # 创建一个图形对象
    fig, ax = plt.subplots()
    line, = ax.plot([], [], lw=2)
    tangent_line, = ax.plot([], [], lw=1, color='red')  # 切线段
    slope_text = ax.text(0.02, 0.95, '', transform=ax.transAxes)  # 显示斜率的文本框
    ax.set_xlim(0, len(model_data))
    ax.set_ylim(model_data.min().min(), model_data.max().max())
    ax.set_xlabel('Time Step')
    ax.set_ylabel('Muscle Mass')

    # 初始化函数，用于绘制空图形
    def init():
        line.set_data([], [])
        tangent_line.set_data([], [])
        slope_text.set_text('')
        return line, tangent_line, slope_text

    # 更新函数，用于更新图形内容
    def update(i):
        # 构建 x 数据，范围为 [0, 1, 2, ..., i]
        x_data = range(i + 1)
        # 获取对应的 y 数据
        y_data = model_data.iloc[:i + 1]['Muscle Mass']
        # 计算切线斜率
        slope = calculate_slope(x_data, y_data, i)
        # 计算切线端点，确保切线跨越横坐标的十分之一
        x_step_ratio = 0.4
        start_point, end_point = calculate_tangent_endpoints(x_data, y_data, i, slope, x_step_ratio)
        # 更新图形内容
        line.set_data(x_data, y_data)
        tangent_line.set_data([start_point[0], end_point[0]], [start_point[1], end_point[1]])
        slope_text.set_text(f'Slope: {slope:.2f}')  # 显示斜率
        return line, tangent_line, slope_text


    # 创建动画对象
    interval_ms = 5  # 设置播放速度为100毫秒
    ani = FuncAnimation(fig, update, frames=len(model_data), init_func=init, blit=True, interval=interval_ms)

    # 设置播放窗口标题为当前播放文件名
    plt.get_current_fig_manager().set_window_title(latest_model_data_file)

    # 播放动画
    plt.show()
else:
    print("No model data file found.")
