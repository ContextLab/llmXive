import matplotlib.pyplot as plt
import pandas as pd
import os

def create_scatter_plot(df, x_col, y_col, title, filename):
    """
    Creates a scatter plot and saves it to a file.
    """
    plt.figure(figsize=(8, 6))
    plt.scatter(df[x_col], df[y_col])
    plt.title(title)
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.savefig(filename)
    plt.close()

def create_residual_plot(df, predicted_col, actual_col, title, filename):
    """
    Creates a residual plot and saves it to a file.
    """
    df['residuals'] = df[actual_col] - df[predicted_col]
    plt.figure(figsize=(8, 6))
    plt.scatter(df[predicted_col], df['residuals'])
    plt.title(title)
    plt.xlabel("Predicted Values")
    plt.ylabel("Residuals")
    plt.savefig(filename)
    plt.close()