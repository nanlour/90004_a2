import pandas as pd
import matplotlib.pyplot as plt

def draw_plot():
    # Read the CSV file
    df = pd.read_csv('model_data.csv')

    # Plot the muscle
    plt.figure(figsize=(15, 6))
    plt.plot(df['Muscle Mass'], label='Muscle Mass')
    plt.xlabel('Time')
    plt.ylabel('Muscle Mass')
    plt.title('Muscle Mass over Time')
    plt.legend()

    plt.savefig('muscle_mass_over_time.png')

    # Plot the hormone
    plt.figure(figsize=(15, 6))
    plt.plot(df['Anabolic Hormone'], label='Anabolic Hormone')
    plt.plot(df['Catabolic Hormone'], label='Catabolic Hormone')
    plt.xlabel('Time')
    plt.ylabel('Hormone Level')
    plt.title('Anabolic and Catabolic Hormone Levels over Time')
    plt.legend()

    plt.savefig('hormone_levels_over_time.png')

draw_plot()