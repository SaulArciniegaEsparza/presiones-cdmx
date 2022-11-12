# -*- coding: utf-8 -*-
"""
Interpolacion de presiones

@author: zaula
"""

#%% Importar librerias
import os
import numpy as np
import pandas as pd


#%% Funciones

def _idw(x, y, z, xi, yi, p=1.5):
    """
    Interpolacion de puntos
    """
    dist = distance_matrix(x, y, xi, yi)
    # In IDW, weights are 1 / distance
    weights = (1.0 / dist) ** p
    # Make weights sum to one
    weights /= weights.sum(axis=0)
    # Multiply the weights for each interpolated
    # point by all observed Z-values
    zi = np.dot(weights.T, z)
    return zi


def distance_matrix(x0, y0, x1, y1):
    """
    Matriz de distancia entre puntos
    """
    obs = np.vstack((x0, y0)).T
    interp = np.vstack((x1, y1)).T
    d0 = np.subtract.outer(obs[:,0], interp[:,0])
    d1 = np.subtract.outer(obs[:,1], interp[:,1])
    return np.hypot(d0, d1)


def idw_interpolation(stations, grid):
    
    # Oberved points
    stations = stations.dropna(subset="Presion (km/cm2)")
    x = stations["X"].values
    y = stations["Y"].values
    z = stations["Presion (km/cm2)"]
    # Coordinates to interpolate
    xi = grid["X"].values
    yi = grid["Y"].values
    # Interpolation
    zi = _idw(x, y, z, xi, yi, p=2.0)
    grid["Presion (km/cm2)"] = zi
    return grid
    
    

