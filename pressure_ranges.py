# -*- coding: utf-8 -*-
"""
Obtener rangos de presiones

@author: zaula
"""

#%% Importar librerias
import os
import numpy as np
import pandas as pd
from calendar import monthrange
from scipy.interpolate import interp1d


#%% Funciones


def constant_operation(stations, ranges_table):
    
    new_stations = stations.copy()
    new_stations.set_index("ID", inplace=True, drop=False)
    new_stations["Semaforo"] = ""
    ranges_table = ranges_table.set_index("ID").loc[new_stations.index, :]

    mask = ((stations["Presion (km/cm2)"] >= ranges_table["Min"])
            & (stations["Presion (km/cm2)"] <= ranges_table["Max"]))
    new_stations.loc[mask, "Semaforo"] = "Buen funcionamiento"
    mask = stations["Presion (km/cm2)"] > ranges_table["Max"]
    new_stations.loc[mask, "Semaforo"] = "Sobrepresión"
    mask = stations["Presion (km/cm2)"] < ranges_table["Min"]
    new_stations.loc[mask, "Semaforo"] = "Presión baja"

    operation = {
        "Buen funcionamiento": (new_stations["Semaforo"] == "Buen funcionamiento").sum(),
        "Sobrepresión": (new_stations["Semaforo"] == "Sobrepresión").sum(),
        "Presión baja": (new_stations["Semaforo"] == "Presión baja").sum(),
        "Fuera de funcionamiento": (new_stations["Semaforo"] == "Fuera de funcionamiento").sum(),
    }
    
    color_sequence = {
        "Buen funcionamiento": "#009d5f",
        "Sobrepresión": "#f4d03f",
        "Presión baja": "#e74c3c",
    }

    return new_stations, operation, color_sequence


def stations_operation(stations, date, hour, ranges_table):

    new_stations = stations.copy()
    new_stations.set_index("ID", inplace=True, drop=False)
    new_stations["Semaforo"] = ""

    month = date.month
    mask = ((month >= ranges_table["Mes inicio"]) & (month < ranges_table["Mes final"])
            & (hour >= ranges_table["Hora inicio"]) & (hour < ranges_table["Hora final"]))
    data_ranges = ranges_table.loc[
        mask,
        ["Estacion", "Min1", "Max1", "Min2", "Max2", "Min3", "Max3", "Min4", "Max4"]
    ]
    data_ranges.set_index("Estacion", inplace=True)

    for i in range(len(stations)):
        station = stations.iloc[i, :]
        idx = station["ID"]
        pressure = station["Presion (km/cm2)"]
        ranges = data_ranges.loc[idx, :]
        if pressure >= ranges["Min1"] and pressure < ranges["Max1"]:
            new_stations.loc[idx, "Semaforo"] = "Buen funcionamiento"
        elif pressure >= ranges["Min2"] and pressure < ranges["Max2"]:
            new_stations.loc[idx, "Semaforo"] = "Sobrepresión"
        elif pressure > ranges["Min3"] and pressure < ranges["Max3"]:
            new_stations.loc[idx, "Semaforo"] = "Presión baja"
        elif pressure >= ranges["Min4"] and pressure <= ranges["Max4"]:
            new_stations.loc[idx, "Semaforo"] = "Fuera de funcionamiento"
        
    operation = {
        "Buen funcionamiento": (new_stations["Semaforo"] == "Buen funcionamiento").sum(),
        "Sobrepresión": (new_stations["Semaforo"] == "Sobrepresión").sum(),
        "Presión baja": (new_stations["Semaforo"] == "Presión baja").sum(),
        "Fuera de funcionamiento": (new_stations["Semaforo"] == "Fuera de funcionamiento").sum(),
    }
    
    color_sequence = {
        "Buen funcionamiento": "#009d5f",
        "Sobrepresión": "#f4d03f",
        "Presión baja": "#e74c3c",
        "Fuera de funcionamiento": "#8e44ad",
    }

    return new_stations, operation, color_sequence


def pressure_hourly(ide, date, ranges_table):

    month = date.month
    mask = ((month >= ranges_table["Mes inicio"]) & (month <= ranges_table["Mes final"])
            & (ide == ranges_table["Estacion"]))
    ranges = ranges_table.loc[mask, :]

    hours = np.arange(0, 23+0.2, 0.2)
    data = pd.DataFrame(
        np.full((len(hours), 8), np.nan),
        index=hours,
        columns=["Min1", "Max1", "Min2", "Max2", "Min3", "Max3", "Min4", "Max4"]
    )
    
    x = ranges.iloc[:, 3].values
    for col in data.columns:
        interp = interp1d(x, ranges.loc[:, col].values, kind="previous", fill_value="extrapolate")
        data.loc[:, col].values[:] = interp(hours)
    
    return data


def pressure_ranges_timeserie(ide, year, month, ranges_table):
    
    days = monthrange(year, month)[1]
    start = f"{year}-{month:02d}-01 00:00"
    end = f"{year}-{month:02d}-{days:02d} 23:00"
    dates = pd.date_range(start, end, freq="1H")
    data = pd.DataFrame(
        np.full((len(dates), 8), np.nan),
        index=dates,
        columns=["Min1", "Max1", "Min2", "Max2", "Min3", "Max3", "Min4", "Max4"],
        dtype=np.float32
    )

    mask = ((month >= ranges_table["Mes inicio"]) & (month <= ranges_table["Mes final"])
        & (ide == ranges_table["Estacion"]))
    ranges = ranges_table.loc[mask, :]
    x = ranges.iloc[:, 3].values
    for col in data.columns:
        interp = interp1d(x, ranges.loc[:, col].values, kind="previous", fill_value="extrapolate")
        for hour in np.arange(0, 24):
            data.loc[dates.hour == hour, col] = interp(hour)
    
    return data


def pressure_ranges_operation(year, month, pressure, ranges_table):

    days = monthrange(year, month)[1]
    start = f"{year}-{month:02d}-01 00:00"
    end = f"{year}-{month:02d}-{days:02d} 23:00"
    dates = pd.date_range(start, end, freq="1H")
    operation = pd.DataFrame(
        np.zeros((len(dates), 2), dtype=int),
        columns=["Sobrepresión", "Presión baja"],
        index=dates
    )
    operation_stats_dict = {
        "Sobrepresión": 0,
        "Presión baja": 0,
    }
    operation_daily = {
        "Sobrepresión": pd.DataFrame(np.zeros((days, pressure.shape[1]), dtype=int), columns=pressure.columns, index=np.arange(1, days+1)),
        "Presión baja": pd.DataFrame(np.zeros((days, pressure.shape[1]), dtype=int), columns=pressure.columns, index=np.arange(1, days+1)),
    }

    for ide in pressure.columns:
        station_ranges = pressure_ranges_timeserie(ide, year, month, ranges_table)
        station_ranges["Presion"] = pressure.loc[:, ide]
        station_ranges = station_ranges.dropna(how="any")
        d1 = (station_ranges["Presion"] >= station_ranges["Min2"]).fillna(0).astype(int)
        d2 = (station_ranges["Presion"] < station_ranges["Max3"]).fillna(0).astype(int)
        
        operation_stats_dict["Sobrepresión"] += min(1, d1.sum())
        operation_stats_dict["Presión baja"] += min(1, d2.sum())
        
        operation.loc[station_ranges.index, "Sobrepresión"] += d1
        operation.loc[station_ranges.index, "Presión baja"] += d2

        operation_daily["Sobrepresión"].loc[:, ide] = d1.groupby(d1.index.day).sum()
        operation_daily["Presión baja"].loc[:, ide] = d2.groupby(d2.index.day).sum()

    operation_dict = {
        "Sobrepresión": pd.pivot_table(
            operation,
            values="Sobrepresión",
            index=operation.index.hour,
            columns=operation.index.day,
            aggfunc="sum"
            ),
        "Presión baja": pd.pivot_table(
            operation,
            values="Presión baja",
            index=operation.index.hour,
            columns=operation.index.day,
            aggfunc="sum"
            ),
    }
    return operation_dict, operation_stats_dict, operation_daily



