import netCDF4
from netCDF4 import Dataset
import matplotlib
import matplotlib.pyplot as plt
import cartopy
import cartopy.crs as ccrs
from cartopy.feature import ShapelyFeature
import pandas as pd
import geopandas
from geopandas import GeoDataFrame
import numpy as np
from shapely.geometry import Polygon, mapping
import csv
import os

#matplotlib inline

os.environ["CARTOPY_USER_BACKGROUNDS"] = r"/home/ana/Escritorio/backgrounds"
path =(r'/home/ana/Escritorio/glmFiles/')


for file in os.listdir(path):
    if file.endswith('.nc'):
        file = os.path.join(path,file)
        
        #Cargamos los datos del GLM del GOES-16
        g16glm = Dataset(file,'r')
        hora = g16glm.time_coverage_start[12:19]
        fecha = g16glm.date_created[:9]
        
       
        #obtenemos las coordenadas de los eventos, grupos y flashes
        event_lat = g16glm.variables['event_lat'][:]
        event_lon = g16glm.variables['event_lon'][:]


        group_lat = g16glm.variables['group_lat'][:]
        group_lon = g16glm.variables['group_lon'][:]

        flash_lat = g16glm.variables['flash_lat'][:]
        flash_lon = g16glm.variables['flash_lon'][:]
        
        #filtrar puntos
        #Cargamos el mundo
        world = geopandas.read_file(
            geopandas.datasets.get_path('naturalearth_lowres')
        )

        #Los limites de colombia
        colombia = (world.loc[world["name"] == "Colombia"])
        col_box = colombia.envelope.scale(2,1.6).bounds.values[0]

        #Los limites Maritimos de Colombia
        maritim = geopandas.read_file('/home/ana/Escritorio/eez/eez.shp')

        #Unimos el poligono terrestre de Colombia con el maritimo
        union = geopandas.overlay(colombia,maritim,how='union')

        #cargamos datos
        event = GeoDataFrame(geometry=geopandas.points_from_xy(event_lon, event_lat), crs={'init' :'epsg:4326'})
        group = GeoDataFrame(geometry=geopandas.points_from_xy(group_lon, group_lat), crs={'init' :'epsg:4326'})
        flash = GeoDataFrame(geometry=geopandas.points_from_xy(flash_lon, flash_lat), crs={'init' :'epsg:4326'})

       
        #intersecciones maritimas
        flashM= geopandas.sjoin(flash, maritim, how="inner", op="intersects")
        groupsM= geopandas.sjoin(flash, maritim, how="inner", op="intersects")
        eventsM= geopandas.sjoin(flash, maritim, how="inner", op="intersects")


        event = geopandas.sjoin(event, union, how="inner", op="intersects")
        group = geopandas.sjoin(group, union, how="inner", op="intersects")
        flash = geopandas.sjoin(flash, union, how="inner", op="intersects")
        plate = ccrs.PlateCarree()

        #cargamos los estados y los limites maritimos
        states = ShapelyFeature(
            geopandas.read_file(r'/home/ana/Escritorio/gadm36_COL_shp/gadm36_COL_1.shp').geometry, crs = plate
        )

        maritimo = ShapelyFeature(
            maritim.geometry, crs = plate
        )
       
        #Dibujamos los limites maritimos y estados colombianos
        fig = plt.figure(figsize=(16,8))
        ax = plt.axes(projection=plate)
        ax.set_global()
        ax.set_extent((col_box[0], col_box[2], col_box[1], col_box[3]))
        ax.background_img(name='BlueMarble', resolution='high', extent=[col_box[0], col_box[2],
                                                                        col_box[1], col_box[3]])
        ax.gridlines(color='black', draw_labels=True)
        ax.coastlines()

        #mostrar estados
        ax.add_feature(states, facecolor='None', edgecolor='gray')
        ax.add_feature(maritimo, facecolor='None', edgecolor='gray')


        #Convertir rango de 0 a 1 a coordenadas del axes
        scale_x = lambda x: (ax.get_xlim()[1] - ax.get_xlim()[0])*x + ax.get_xlim()[0]
        scale_y = lambda x: (ax.get_ylim()[1] - ax.get_ylim()[0])*x + ax.get_ylim()[0]

       
        ax.text(scale_x(0.05), scale_y(0.95), "Flashes = " + str(len(flash.index)), color = 'white')

        ax.text(scale_x(0.05), scale_y(0.90), "Events ="+ str(len(event.index)), color = 'white')

        ax.text(scale_x(0.05), scale_y(0.85), "Groups = {len(group.index)}", color = 'white')

        ax.text(scale_x(0.05), scale_y(0.10), f"Flashes Mar = {len(flashM.index)}", color = 'white')
        ax.text(scale_x(0.05), scale_y(0.10), f"Grupos Mar = {len(groupsM.index)}", color = 'white')
        ax.text(scale_x(0.05), scale_y(0.10), f"Eventos Mar = {len(eventsM.index)}", color = 'white')

        #Mostrar puntos
        ax.scatter([p.x for p in event.geometry],
                [p.y for p in event.geometry],
                transform=plate,
                color='blue', s=15
                )

        ax.scatter([p.x for p in group.geometry],
                [p.y for p in group.geometry],
                transform=plate,
                color='green', s=13
                )

        ax.scatter([p.x for p in flash.geometry],
                [p.y for p in flash.geometry],
                transform=plate,
                color='red', s=10
                )
        
        #Guardamos los datos en un csv
        row= [fecha,hora,len(event.index),len(group.index),len(flash.index)]
        
        
  