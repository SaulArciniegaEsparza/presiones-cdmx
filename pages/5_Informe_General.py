# -*- coding: utf-8 -*-
"""
Reporte por estacion

@author: zaula
"""


#%% Libraries
import os
import datetime
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import data_bases as dbs


#%% Datos iniciales
db = dbs.DataBase()
dates = db.get_time_period()
date0 = dates["min"].to_pydatetime().date()
date1 = (dates["max"] - pd.Timedelta(60, "days")).to_pydatetime().date()
date2 = dates["max"].to_pydatetime().date()
db.close()

if "ids" not in st.session_state:
    db = dbs.DataBase()
    ids = db.get_stations_id()
    db.close()
    st.session_state["ids"] = ids


#%% Definir funciones

def daily_pressure(ids, date):
    if len(ids) == 0:
        ids = None
    db = dbs.DataBase()
    stations = db.get_stations()
    pressure = db.get_pressure_by_day(date, ids).round(3)
    db.close()
    if ids is None:
        ids = []  # ids comunes
        for i in stations["ID"]:
            if i in pressure.columns:
                ids.append(i)
        stations = stations.loc[ids, :]
        names = stations[["ID", "Nombre"]]
        pressure = pressure.loc[:, ids]
    else:
        names = stations.loc[ids, ["ID", "Nombre"]]
    press = pd.DataFrame(
        np.full((24, len(names)), np.nan),
        index=np.arange(0, 24),
        columns=names["ID"]
    )
    for col in pressure.columns:
        press[col] = pressure[col]
    stats = press.copy()
    stats.loc["Min", :] = press.min().values
    stats.loc["Promedio", :] = press.mean().values
    stats.loc["Max", :] = press.max().values
    names.set_index("ID", drop=False, inplace=True)
    stats.columns = [f"{d}-{names.loc[d, 'Nombre']}" for d in stats.columns]
    stats = stats.transpose().round(3)
    return press, stats, names


def hourly_pressure_by_month(ids, year, month):
    if len(ids) == 0:
        ids = None
    db = dbs.DataBase()
    pressure = db.get_hourly_pressure_by_month(year, month, ids)
    stations = db.get_stations()
    db.close()
    if ids is None:
        ids = []  # ids comunes
        for i in stations["ID"]:
            if i in pressure.columns:
                ids.append(i)
        stations = stations.loc[ids, :]
        names = stations[["ID", "Nombre"]]
        pressure = pressure.loc[:, ids]
    else:
        names = stations.loc[ids, ["ID", "Nombre"]]
    press = pd.DataFrame(
        np.full((24, len(names)), np.nan),
        index=np.arange(0, 24),
        columns=names["ID"]
    )
    for col in pressure.columns:
        press[col] = pressure[col]
    stats = press.copy()
    stats.columns = [f"{d}-{names.loc[d, 'Nombre']}" for d in stats.columns]
    return press, stats, names


def daily_pressure_by_month(ids, year, month):
    if len(ids) == 0:
        ids = None
    db = dbs.DataBase()
    pressure = db.get_daily_pressure_by_month(year, month, ids)
    stations = db.get_stations()
    db.close()
    if ids is None:
        ids = []  # ids comunes
        for i in stations["ID"]:
            if i in pressure.columns:
                ids.append(i)
        stations = stations.loc[ids, :]
        names = stations[["ID", "Nombre"]]
        pressure = pressure.loc[:, ids]
    else:
        names = stations.loc[ids, ["ID", "Nombre"]]
    press = pd.DataFrame(
        np.full((24, len(names)), np.nan),
        index=np.arange(0, 24),
        columns=names["ID"]
    )
    for col in pressure.columns:
        press[col] = pressure[col]
    stats = press.copy()
    stats.columns = [f"{d}-{names.loc[d, 'Nombre']}" for d in stats.columns]
    return press, stats, names


def monthly_pressure_by_year(ids, year):
    if len(ids) == 0:
        ids = None
    db = dbs.DataBase()
    pressure = db.get_monthly_pressure_by_year(year, ids)
    stations = db.get_stations()
    db.close()
    if ids is None:
        ids = []  # ids comunes
        for i in stations["ID"]:
            if i in pressure.columns:
                ids.append(i)
        stations = stations.loc[ids, :]
        names = stations[["ID", "Nombre"]]
        pressure = pressure.loc[:, ids]
    else:
        names = stations.loc[ids, ["ID", "Nombre"]]
    press = pd.DataFrame(
        np.full((12, len(names)), np.nan),
        index=np.arange(1, 13),
        columns=names["ID"]
    )
    for col in pressure.columns:
        press[col] = pressure[col]
    stats = press.copy()
    stats.columns = [f"{d}-{names.loc[d, 'Nombre']}" for d in stats.columns]
    return press, stats, names


@st.cache
def download_data(data):
    return data.to_csv().encode('utf-8')


#%% App

st.sidebar.title("Sistema de Presiones CDMX")
selection = st.sidebar.multiselect("Buscar estaciones", st.session_state["ids"])
plot_type = st.sidebar.selectbox(
    "Tipo de grafico",
    ["Serie horaria en un dia",
     "Estadisticos horarios por mes",
     "Estadisticos diarios por mes",
     "Estadisticos mensuales por año"
    ]
)

st.title("Reporte General de Presiones")


###############################################################################
if plot_type == "Serie horaria en un dia":
    sdate = st.sidebar.date_input(
        "Seleccionar fecha",
        value=date2,
        min_value=date0,
        max_value=date2
    )
    
    pressure, stats, names = daily_pressure(selection, sdate)
    
    if len(pressure) == 0:
        st.error(f"No se encontraron registros de las estaciones para la fecha **{sdate}**")
    else:
        # plot
        data_plot = []
        for i in range(len(names)):
            ide = names.iloc[i, 0]
            data_plot.append(
                go.Scatter(
                    x=pressure.index,
                    y=pressure[ide],
                    mode="lines",
                    name=f"{ide} - {names.iloc[i, 1]}"
                    )
                )
        layout = go.Layout(yaxis={"title": "Presión horaria (kg/cm2)"})
        fig = go.Figure(data=data_plot, layout=layout)
        fig.update_xaxes(range=[0, 23])
        
        st.markdown(f"Presiones horarias: **{sdate}**")
        st.plotly_chart(fig, use_container_width=True)
        
        # downloads    
        col1, col2 = st.columns(2)
        with col1:
            output1 = download_data(pressure)
            st.download_button(
                label="Descargar series",
                data=output1,
                file_name=f"Presiones_{sdate}.csv",
                mime="text/csv",
            )
        with col2:
            output2 = download_data(stats)
            st.download_button(
                label="Descargar estadísticos",
                data=output2,
                file_name=f"EstadisticosPresiones_{sdate}.csv",
                mime="text/csv",
            )
        
        with st.expander(f"Estadísticos horarios de presión para el día: {sdate}"):
            st.dataframe(stats, use_container_width=True)

###############################################################################
if plot_type == "Estadisticos horarios por mes":
    year = st.sidebar.selectbox("Seleccionar año", list(range(date2.year, date0.year-1, -1)), 0)
    month = st.sidebar.selectbox("Seleccionar mes", list(range(1, 13)), date2.month-1)
    
    pressure, stats, names = hourly_pressure_by_month(selection, year, month)
    
    if len(pressure) == 0:
        st.error(f"No se encontraron registros de las estaciones para el mes **{year}-{month}**")
    else:
        # plot
        data_plot = []
        for i in range(len(names)):
            ide = names.iloc[i, 0]
            data_plot.append(
                go.Scatter(
                    x=pressure.index,
                    y=pressure[ide],
                    mode="lines",
                    name=f"{ide} - {names.iloc[i, 1]}"
                    )
                )
        layout = go.Layout(yaxis={"title": "Presión horaria (kg/cm2)"})
        fig = go.Figure(data=data_plot, layout=layout)
        fig.update_xaxes(range=[0, 23])
                
        st.markdown(f"Presiones promedio horarias: **{year}-{month}**")
        st.plotly_chart(fig, use_container_width=True)
        
        # downloads
        output = download_data(pressure)
        st.download_button(
            label="Descargar estadísticos",
            data=output,
            file_name=f"PresionesPromedio_{year}-{month}.csv",
            mime="text/csv",
        )
        
        with st.expander(f"Presiones promedio horarias para el mes: {year}-{month}"):
            st.dataframe(stats, use_container_width=True)

###############################################################################
if plot_type == "Estadisticos diarios por mes":
    year = st.sidebar.selectbox("Seleccionar año", list(range(date2.year, date0.year-1, -1)), 0)
    month = st.sidebar.selectbox("Seleccionar mes", list(range(1, 13)), date2.month-1)
    
    pressure, stats, names = daily_pressure_by_month(selection, year, month)
    
    if len(pressure) == 0:
        st.error(f"No se encontraron registros de las estaciones para el mes **{year}-{month}**")
    else:
        # plot
        data_plot = []
        for i in range(len(names)):
            ide = names.iloc[i, 0]
            data_plot.append(
                go.Scatter(
                    x=pressure.index,
                    y=pressure[ide],
                    mode="lines",
                    name=f"{ide} - {names.iloc[i, 1]}"
                    )
                )
        layout = go.Layout(yaxis={"title": "Presión diaria (kg/cm2)"})
        fig = go.Figure(data=data_plot, layout=layout)
        
        st.markdown(f"Presiones promedio diarias: **{year}-{month}**")
        st.plotly_chart(fig, use_container_width=True)
        
        # downloads
        output = download_data(pressure)
        st.download_button(
            label="Descargar estadísticos",
            data=output,
            file_name=f"Presiones_{selection}_{year}-{month}.csv",
            mime="text/csv",
        )
        
        with st.expander(f"Presiones promedio diarias: {year}-{month}"):
            st.dataframe(stats, use_container_width=True)

###############################################################################
if plot_type == "Estadisticos mensuales por año":
    year = st.sidebar.selectbox("Seleccionar año", list(range(date2.year, date0.year-1, -1)), 0)
    
    pressure, stats, names = monthly_pressure_by_year(selection, year)
    
    if len(pressure) == 0:
        st.error(f"No se encontraron registros de las estaciones para el año **{year}**")
    else:
        # plot
        data_plot = []
        for i in range(len(names)):
            ide = names.iloc[i, 0]
            data_plot.append(
                go.Scatter(
                    x=pressure.index,
                    y=pressure[ide],
                    mode="lines",
                    name=f"{ide} - {names.iloc[i, 1]}"
                    )
                )
        layout = go.Layout(yaxis={"title": "Presión mensual (kg/cm2)"})
        fig = go.Figure(data=data_plot, layout=layout)
        fig.update_xaxes(range=[1, 12])
        
        st.markdown(f"Presiones mensuales promedio para el año: **{year}**")
        st.plotly_chart(fig, use_container_width=True)
        
        # downloads
        output = download_data(pressure)
        st.download_button(
            label="Descargar estadísticos",
            data=output,
            file_name=f"Presiones_{selection}_{year}.csv",
            mime="text/csv",
        )
        
        with st.expander(f"Presiones mensuales promedio para el año: {year}"):
            st.dataframe(stats, use_container_width=True)

