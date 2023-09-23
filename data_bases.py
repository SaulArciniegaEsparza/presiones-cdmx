# -*- coding: utf-8 -*-
"""
Gestionar base de datos

@author: zaula
"""

#%% Importar librerias
import os
import numpy as np
import pandas as pd
import sqlite3

path = os.path.abspath(os.path.dirname(__file__))


#%% Clases

class DataBase:

    def __init__(self):
        self.folder = os.path.join(path, "Datos")
        self.fname = os.path.join(self.folder, "DataBase.sqlite")
        self.etable = "estaciones"
        self.ptable = "presiones"
        self.efields = {
            "ID": "INTEGER PRIMARY KEY",
            "Nombre": "text NOT NULL",
            "X": "REAL NOT NULL",
            "Y": "REAL NOT NULL",
            "Carga": "REAL NOT NULL",
            "Diametro": "INTEGER NOT NULL",
            "Instalacion": "INTEGER NOT NULL",
            "Ubicacion": "text",
            "SensorMaterial": "text",
            "SensorUbicacion": "text",
            "FuenteTipo1": "text",
            "FuenteNombre1": "text",
            "FuenteUbicacion1": "text",
            "FuenteTipo2": "text",
            "FuenteNombre2": "text",
            "FuenteUbicacion2": "text",
        }
        self.pfields = {
            "ID": "INTEGER NOT NULL",
            "Fecha": "text NOT NULL",
            "Ano": "INTEGER NOT NULL",
            "Mes": "INTEGER NOT NULL",
            "Dia": "INTEGER NOT NULL",
            "Hora": "INTEGER NOT NULL",
            "Valor": "REAL"
        }
        self.init_db()
    
    def init_db(self):
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
        if not os.path.exists(self.fname):
            self.conn = sqlite3.connect(self.fname)
            cursor = self.conn.cursor()
            fieldstr = ", ".join([f"{key} {value}" for key, value in self.efields.items()])
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.etable} ({fieldstr})")
            fieldstr = ", ".join([f"{key} {value}" for key, value in self.pfields.items()])
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.ptable} ({fieldstr})")
            self.conn.commit()
            
            df = pd.read_csv(os.path.join(path, "DatosIniciales", "Estaciones.csv"))
            df.to_sql(self.etable, self.conn, if_exists="replace", index=False)
            
            df = pd.read_csv(os.path.join(path, "DatosIniciales", "Presiones.csv"),
                             index_col=[0], parse_dates=[0])
            d = df.melt(ignore_index=False).reset_index(False)
            d["Ano"] = d.iloc[:, 0].dt.year
            d["Mes"] = d.iloc[:, 0].dt.month
            d["Dia"] = d.iloc[:, 0].dt.day
            d["Hora"] = d.iloc[:, 0].dt.hour
            d.iloc[:, 1] = d.iloc[:, 1].astype(int)
            d.columns = ["Fecha", "ID", "Valor", "Ano", "Mes", "Dia", "Hora"]
            d = d.loc[:, ["ID", "Fecha", "Ano", "Mes", "Dia", "Hora", "Valor"]]
            d = d.dropna()
            d.to_sql(self.ptable, self.conn, if_exists="replace", index=False)
                        
        else:
            self.conn = sqlite3.connect(self.fname)

    def get_stations_id(self):
        query = f"SELECT ID FROM {self.etable}"
        df = pd.read_sql(query, self.conn)["ID"]
        return [int(x) for x in df]

    def get_stations(self):
        query = f"SELECT * FROM {self.etable}"
        df = pd.read_sql(query, self.conn)
        return df.set_index("ID", drop=False)

    def get_station(self, ide=1):
        query = f"SELECT * FROM {self.etable} WHERE ID = {ide}"
        df = pd.read_sql(query, self.conn)
        if len(df) == 1:
            return df.squeeze()
        else:
            return pd.Series([], dtype=np.float32)
        
    def update_stations(self, table):
        if not isinstance(table, pd.DataFrame):
            return False, "No se ha podido cargar la tabla"
        if len(table) == 0:
            return False, "La tabla ingresada no tiene información"
        for key in self.efields.keys():
            if key not in table.columns:
                return False, f"La tabla ingresada no tiene la columna '{key}'."
        if len(table["ID"].unique()) != len(table.index):
            return False, "La tabla ingresada tiene índices repetidos para las estaciones."
        table.to_sql(self.etable, self.conn, if_exists="replace", index=False)
        return True, "Se ha actualizado la tabla de estaciones."    
        
    def get_time_period(self):
        query = f"SELECT MIN(Fecha) AS min, MAX(Fecha) AS max FROM {self.ptable}"
        df = pd.read_sql(query, self.conn)
        if len(df) > 0:
            return pd.to_datetime(df.iloc[0, :])
        else:
            return pd.Series([], dtype=np.float32)

    def get_dates_record(self, ide=None, which="both"):
        if which.lower() == "both":
            if ide is not None:
                ide = int(ide)
                query = f"SELECT MIN(Fecha) AS min, MAX(Fecha) AS max FROM {self.ptable} WHERE ID = {ide}"
                df = pd.read_sql(query, self.conn)
                if len(df) == 1:
                    return pd.to_datetime(df.iloc[0, :])
            else:
                query = f"SELECT ID, MIN(Fecha) AS min, MAX(Fecha) AS max FROM {self.ptable} GROUP BY ID"
                df = pd.read_sql(query, self.conn)
                if len(df) > 0:
                    df = df.set_index("ID")
                    df["max"] = pd.to_datetime(df["max"])
                    df["min"] = pd.to_datetime(df["min"])
                    return df
        else:
            which = which.upper()
            if which not in ("MIN", "MAX"):
                return pd.Series([], dtype=np.float32)
            if ide is not None:
                ide = int(ide)
                query = f"SELECT {which}(Fecha) FROM {self.ptable} WHERE ID = {ide}"
                df = pd.read_sql(query, self.conn)
                if len(df) == 1:
                    return pd.to_datetime(df.values[0, 0])
            else:
                query = f"SELECT ID, {which}(Fecha) AS {which.lower()} FROM {self.ptable} GROUP BY ID"
                df = pd.read_sql(query, self.conn)
                if len(df) > 0:
                    df = df.set_index("ID")
                    return pd.to_datetime(df[which.lower()])
        return pd.Series([], dtype=np.float32)

    def get_station_pressure(self, ide=1, date=None, year=None, month=None, period=None):
        ide = int(ide)
        fields = "Fecha, Valor"
        if date is not None:
            dt = pd.Timedelta(1, "minutes")
            date1 = (pd.to_datetime(date) - dt).strftime("%Y-%m-%d %H:%M")
            date2 = (pd.to_datetime(date) + dt).strftime("%Y-%m-%d %H:%M")
            query = f"SELECT {fields} FROM {self.ptable} WHERE ID = {ide} AND Fecha BETWEEN '{date1}' AND '{date2}'"
        elif type(period) in (tuple, list):
            dt = pd.Timedelta(30, "minutes")
            date1 = (pd.to_datetime(period[0]) - dt).strftime("%Y-%m-%d %H:%M")
            date2 = (pd.to_datetime(period[1]) + dt).strftime("%Y-%m-%d %H:%M")
            query = f"SELECT {fields} FROM {self.ptable} WHERE ID = {ide} AND Fecha BETWEEN '{date1}' AND '{date2}'"
        elif year is not None and month is not None:
            query = f"SELECT {fields} FROM {self.ptable} WHERE ID = {ide} AND Ano = {int(year)} AND Mes = {int(month)} ORDER BY Fecha"
        elif month is not None:
            query = f"SELECT {fields} FROM {self.ptable} WHERE ID = {ide} AND Mes = {int(month)} ORDER BY Fecha"
        else:
            query = f"SELECT {fields} FROM {self.ptable} WHERE ID = {ide} ORDER BY Fecha"
        df = pd.read_sql(query, self.conn)
        if len(df) > 0:
            df["Fecha"] = pd.to_datetime(df["Fecha"])
            return df.set_index("Fecha")["Valor"]
        else:
            return pd.Series([], dtype=np.float32)
    
    def get_hourly_pressure(self, date, hour, ide=None):
        date1 = pd.to_datetime(date)
        year = date1.year
        month = date1.month
        day = date1.day
        query_date = f"Ano = {year} AND Mes = {month} AND Dia = {day} AND Hora = {hour}"
        if type(ide) in (int, float, str):
            ide = int(ide)
            query = f"SELECT ID, Valor FROM {self.ptable} WHERE ID = {ide} AND {query_date}"
        elif type(ide) in (tuple, list, np.ndarray):
            ids = ", ".join([str(x) for x in ide])
            query = f"SELECT ID, Valor FROM {self.ptable} WHERE ID IN ({ids}) AND {query_date}"
        else:
            query = f"SELECT ID, Valor FROM {self.ptable} WHERE {query_date}"
        df = pd.read_sql(query, self.conn)
        if len(df) > 0:
            df.set_index("ID", inplace=True)
        return df

    def get_pressure_by_day(self, date, ide=None):
        dt1 = pd.Timedelta(30, "minutes")
        dt2 = pd.Timedelta(23, "hours")
        day = pd.to_datetime(date).strftime("%Y-%m-%d")
        date1 = (pd.to_datetime(day) - dt1).strftime("%Y-%m-%d %H:%M")
        date2 = (pd.to_datetime(day) + dt1 + dt2).strftime("%Y-%m-%d %H:%M")
        if type(ide) in (int, float, str):
            ide = int(ide)
            query = f"SELECT Hora, Valor FROM {self.ptable} WHERE ID = {ide} AND Fecha BETWEEN '{date1}' AND '{date2}'"
            df = pd.read_sql(query, self.conn)
            if len(df) > 0:
                return df.set_index("Hora")["Valor"]
            else:
                return pd.Series([], dtype=np.float32)
        elif type(ide) in (tuple, list, np.ndarray):
            ids = ", ".join([str(x) for x in ide])
            query = f"SELECT ID, Hora, Valor FROM {self.ptable} WHERE ID IN ({ids}) AND Fecha BETWEEN '{date1}' AND '{date2}'"        
        else:
            query = f"SELECT ID, Hora, Valor FROM {self.ptable} WHERE Fecha BETWEEN '{date1}' AND '{date2}'"
        df = pd.read_sql(query, self.conn)
        if len(df) > 0:
            return pd.pivot_table(df, values="Valor", index="Hora", columns="ID")
        else:
            return pd.DataFrame([], dtype=np.float32)
    
    def get_hourly_pressure_by_month(self, year, month, ide=None):
        if type(ide) in (int, float, str):
            ide = int(ide)
            query = "SELECT Hora, MIN(Valor) AS min, AVG(Valor) AS mean, MAX(Valor) AS max"
            query += f" FROM {self.ptable} WHERE ID = {ide} AND Ano = {year} AND Mes = {month}"
            query += " GROUP BY Hora"
            df = pd.read_sql(query, self.conn)
            if len(df) > 0:
                return df.set_index("Hora")
            else:
                return pd.Series([], dtype=np.float32)
        elif type(ide) in (tuple, list, np.ndarray):
            ids = ", ".join([str(x) for x in ide])
            query = f"SELECT ID, Hora, AVG(Valor) AS mean FROM {self.ptable}"
            query += f" WHERE ID IN ({ids}) AND Ano = {year} AND Mes = {month}"
            query += " GROUP BY ID, Hora"
        else:
            query = f"SELECT ID, Hora, AVG(Valor) AS mean FROM {self.ptable}"
            query += f" WHERE Ano = {year} AND Mes = {month}"
            query += " GROUP BY ID, Hora"
        df = pd.read_sql(query, self.conn)
        if len(df) > 0:
            return pd.pivot_table(df, values="mean", index="Hora", columns="ID")
        else:
            return pd.DataFrame([], dtype=np.float32)
        
    def get_daily_pressure_by_month(self, year, month, ide=None):
        if type(ide) in (int, float, str):
            ide = int(ide)
            query = "SELECT Dia, MIN(Valor) AS min, AVG(Valor) AS mean, MAX(Valor) AS max"
            query += f" FROM {self.ptable} WHERE ID = {ide} AND Ano = {year} AND Mes = {month}"
            query += " GROUP BY Dia"
            df = pd.read_sql(query, self.conn)
            if len(df) > 0:
                return df.set_index("Dia")
            else:
                return pd.Series([], dtype=np.float32)
        elif type(ide) in (tuple, list, np.ndarray):
            ids = ", ".join([str(x) for x in ide])
            query = f"SELECT ID, Dia, AVG(Valor) AS mean FROM {self.ptable}"
            query += f" WHERE ID IN ({ids}) AND Ano = {year} AND Mes = {month}"
            query += " GROUP BY ID, Dia"
        else:
            query = f"SELECT ID, Dia, AVG(Valor) AS mean FROM {self.ptable}"
            query += f" WHERE Ano = {year} AND Mes = {month}"
            query += " GROUP BY ID, Dia"
        df = pd.read_sql(query, self.conn)
        if len(df) > 0:
            return pd.pivot_table(df, values="mean", index="Dia", columns="ID")
        else:
            return pd.DataFrame([], dtype=np.float32)

    def get_monthly_pressure_by_year(self, year, ide=None):
        if type(ide) in (int, float, str):
            ide = int(ide)
            query = "SELECT Mes, MIN(Valor) AS min, AVG(Valor) AS mean, MAX(Valor) AS max"
            query += f" FROM {self.ptable} WHERE ID = {ide} AND Ano = {year}"
            query += " GROUP BY Mes"
            df = pd.read_sql(query, self.conn)
            if len(df) > 0:
                return df.set_index("Mes")
            else:
                return pd.Series([], dtype=np.float32)
        elif type(ide) in (tuple, list, np.ndarray):
            ids = ", ".join([str(x) for x in ide])
            query = f"SELECT ID, Mes, AVG(Valor) AS mean FROM {self.ptable}"
            query += f" WHERE ID IN ({ids}) AND Ano = {year}"
            query += " GROUP BY ID, Mes"
        else:
            query = f"SELECT ID, Mes, AVG(Valor) AS mean FROM {self.ptable}"
            query += f" WHERE Ano = {year}"
            query += " GROUP BY ID, Mes"
        df = pd.read_sql(query, self.conn)
        if len(df) > 0:
            return pd.pivot_table(df, values="mean", index="Mes", columns="ID")
        else:
            return pd.DataFrame([], dtype=np.float32)
        
    def get_monthly_records_by_year(self, year, ide=None):
        if type(ide) in (int, float, str):
            ide = int(ide)
            query = "SELECT Mes, COUNT(Valor) AS count FROM {self.ptable}"
            query += f" WHERE ID = {ide} AND Ano = {year}"
            query += " GROUP BY Mes"
            df = pd.read_sql(query, self.conn)
            if len(df) > 0:
                return df.set_index("Mes")
            else:
                return pd.Series([], dtype=np.float32)
        elif type(ide) in (tuple, list, np.ndarray):
            ids = ", ".join([str(x) for x in ide])
            query = f"SELECT ID, Mes, COUNT(Valor) AS count FROM {self.ptable}"
            query += f" WHERE ID IN ({ids}) AND Ano = {year}"
            query += " GROUP BY ID, Mes"
        else:
            query = f"SELECT ID, Mes, COUNT(Valor) AS count FROM {self.ptable}"
            query += f" WHERE Ano = {year}"
            query += " GROUP BY ID, Mes"
        df = pd.read_sql(query, self.conn)
        if len(df) > 0:
            return pd.pivot_table(df, values="count", index="Mes", columns="ID")
        else:
            return pd.DataFrame([], dtype=np.float32)

    def close(self):
        self.conn.close()


#%% Base de datos de rangos de presiones

class PresionesRangosDB:
    
    def __init__(self):
        self.folder = os.path.join(path, "Datos")
        self.fname = os.path.join(path, "Datos", "RangosPresiones.sqlite")
        
        self.prtable = "rangos"
        self.prfields = {
            "Clave": "text NOT NULL",        # nombre del rango
            "ID": "INTEGER NOT NULL",        # id estacion
            "MinPresion": "float NOT NULL",  # presion minima
            "MaxPresion": "float NOT NULL",  # presion minima
        }
        
        self.init_db()
    
    def init_db(self):
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
        if not os.path.exists(self.fname):
            self.conn = sqlite3.connect(self.fname)
            cursor = self.conn.cursor()
            fieldstr = ", ".join([f"{key} {value}" for key, value in self.prfields.items()])
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.prtable} ({fieldstr})")
            self.conn.commit()
            self.add_default_table()
        else:
            self.conn = sqlite3.connect(self.fname)
            
    def check_if_exists(self, clave):
        query = f"SELECT COUNT(*) AS count FROM {self.prtable} WHERE Clave = '{clave}'"
        cursor = self.conn.cursor()
        return bool(cursor.execute(query).fetchone()[0])
            
    def add_ranges_table(self, clave, table):
        if self.check_if_exists(clave):
            return False, "Ya existe una tabla con esa clave"
        # check for columns
        for key in self.prfields.keys():
            if key == "Clave":
                continue
            if key not in table.columns:
                return False, "Error con las columnas de la tabla. Descarga la tabla de ejemplo."
        dtable = table.copy()
        dtable["Clave"] = clave
        dtable.to_sql(self.prtable, self.conn, if_exists="append", index=False)
        return True, "Datos cargados de forma correcta."
        
    def add_default_table(self):
        filename = os.path.join(path, "DatosIniciales", "RangosPresiones.csv")
        table = pd.read_csv(filename)
        self.add_ranges_table("Constantes", table)
        
    def delete_table(self, clave: str):
        if clave == "Constante":
            return False, "No se puede eliminar la tabla por defecto."
        if not self.check_if_exists(clave):
            return False, "No existe la clave especificada."
        query = f"DELETE FROM {self.prtable} WHERE Clave = '{clave}'"
        cursor = self.conn.cursor()
        cursor.execute(query)
        self.conn.commit()
        return True, f"Tabla '{clave}' borrada con éxito."
        
    def get_claves(self):
        query = f"SELECT DISTINCT Clave FROM {self.prtable}"
        claves = pd.read_sql(query, self.conn).squeeze()
        if type(claves) is str:
            claves = [claves]
        else:
            claves = claves.to_list()
        return claves
    
    def get_pressure_ranges(self, clave, ids=None):
        if not self.check_if_exists(clave):
            return pd.Series([np.nan, np.nan], index=["MinPresion", "MaxPresion"])
        if type(ids) in (int, str):
            query = f"SELECT MinPresion, MaxPresion FROM {self.prtable} WHERE Clave = '{clave}' AND ID = {int(ids)}"
            pressure = pd.read_sql(query, self.conn).squeeze()
            if len(pressure) == 0:
                pressure = pd.Series([np.nan, np.nan], index=["MinPresion", "MaxPresion"])
        elif type(ids) in (list, tuple):
            ids_str = ", ".join([str(x) for x in ids])
            query = f"SELECT MinPresion, MaxPresion FROM {self.prtable} WHERE Clave = '{clave}' AND ID IN ({ids_str})"
            pressure = pd.read_sql(query, self.conn)
        else:
            query = f"SELECT ID, MinPresion, MaxPresion FROM {self.prtable} WHERE Clave = '{clave}'"
            pressure = pd.read_sql(query, self.conn)
        return pressure
    
    @staticmethod
    def interpolate_pressure(pressures, start, end):
        serie = pd.Series(np.ones(24) * pressures["MinPresion"], index=np.arange(0, 24))
        serie[(serie.index >= start) & (serie.index <= end)] = pressures["MaxPresion"]
        return serie
    
    @staticmethod
    def timeseries_pressure(pressures, dates, start, end):
        serie = pd.Series(np.ones(len(dates)) * pressures["MinPresion"], index=dates)
        serie[(serie.index.hour >= start) & (serie.index.hour <= end)] = pressures["MaxPresion"]
        return serie
    
    def check_is_table_is_valid(self, table):
        
        if not isinstance(table, pd.DataFrame):
            return False, "Error con los datos ingresados."
        for key in self.prfields.keys():
            if key == "Clave":
                continue
            if key not in table:
                return False, f"No se encontró la columna '{key}'"
        if len(table["ID"].unique()) != table.shape[0]:
            return False, "Error con la tabla ingresada, existen claves repetidas de estaciones"
        return True, "Tabla cargada de forma correcta"
        
    def close(self):
        self.conn.close()


