from netCDF4 import Dataset
import cartopy.crs as ccrs
from cartopy.feature import ShapelyFeature
import pandas as pd
import geopandas
from geopandas import GeoDataFrame
import numpy as np
from shapely.geometry import Polygon, mapping
from fiona.crs import from_epsg
import MySQLdb
import os
import time
from datetime import datetime
from google.cloud import storage
import subprocess

while True:
#########################################################################   
# Code to download the latest file provided by the GLM every 20 seconds #
#########################################################################
    
    dt = datetime.utcnow() 
    tt = dt.timetuple()

    # Build the url base
    bucketname = 'gcp-public-data-goes-16'
    domain = "https://storage.cloud.google.com" 
    folder  = "GLM-L2-LCFA/" + str(dt.year) + "/" + str(tt.tm_yday).zfill(3) + "/" + str(dt.hour).zfill(2)

    # Create the key for the service account
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/home/ana/Escritorio/GLM/codigos/sivamGLM-df86d6cc0225.json"

    # Consult in the storage to get the data for that hour
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucketname)
    files = bucket.list_blobs(prefix=folder)
    fileList = [file.name for file in files if '.' in file.name]

    # Take the latest file in the list of files
    lastFile  = fileList[-1]

    # Download the latest file 
    url1 = bucketname + "/" + lastFile

    # Save the file in the desire folder with a given name (In this case we call it "lastGLM")
    subprocess.call('/home/ana/google-cloud-sdk/bin/gsutil cp gs://%s /home/ana/Escritorio/GLM/glmFiles/lastGLM.nc' %(url1), shell=True)
    
    #=========================================================================================================================================

    ################################################################################################
    # Extract and filter the data depending of the flag quality and just for the region of interest#
    ################################################################################################

    # Upload the data of the file previously saved 
    g16glm = Dataset("/home/ana/Escritorio/GLM/glmFiles/lastGLM.nc")

    # Extract the interest variables

    name = str(g16glm.dataset_name) # dataset name
    date = g16glm.date_created[:10] # date the data were taken by the satellite
    hour = g16glm.time_coverage_start[11:13] 
    hour = str(int(hour)-5) # because the data is shown in UTC, we adjust to the Colombian time
    minutes = str(g16glm.time_coverage_start[14:16])
    seconds = str(g16glm.time_coverage_start[17:19])
    dateT = str(date+" "+hour + ":"+minutes+":"+seconds) 

    # Get the coordinates, flag quality and radiant energy for each flash
    flash_lat = g16glm.variables['flash_lat'][:] # Flash latitude
    flash_lon = g16glm.variables['flash_lon'][:] # Flash Longitude
    quality = g16glm.variables['flash_quality_flag'][:] # Flag quality 
    energy = g16glm.variables['flash_energy'][:] # Radiant energy

    # Filter the data mark with the flag of good quality

    # Create an index that show us the position of the data with 
    goodQuality = []
    for i in range(0, len(quality)):
        if quality[i] == 0: # if the quality flag value is 0 it means the data has good quality, otherwise will be ignored
            goodQuality.append(i)

    # Filter the coordinates and radiant energy depending on the position of the good quality flag
    latitude = []
    longitude = []
    energyNew = []
    for i in goodQuality:
        latitude.append(flash_lat[i])
        longitude.append(flash_lon[i])
        energyNew.append(energy[i])
    flash_lat = latitude
    flash_lon = longitude
    energy = energyNew

    # Load the shape of the region of interest
    border = geopandas.read_file(r"/home/ana/Escritorio/GLM/limites/colombia/fronteras.shp")  
    Colombia = geopandas.read_file(r"/home/ana/Escritorio/GLM/limites/colombia/Colombia.shp")
    Colombia.iloc[44, Colombia.columns.get_loc('NAME_1')]= "Mar" 

    # Create a data frame with geographic coodinates and transform latitude and longitude into a list of shapely.point
    # It is necesary to plot this points later in a map
    flash = GeoDataFrame(geometry=geopandas.points_from_xy(flash_lon, flash_lat), crs={'init' :'epsg:4326'})

    #Intersecciones de flashes y territorio
    flashb = geopandas.sjoin(flash, border, how="inner", op="intersects") # intersectamos los flashes dentro del poligono mas grande
    flashC = geopandas.sjoin(flash,Colombia,how= 'inner',op = 'intersects') # Intersectamos los flashes dentro del territorio colombiano

    #Creamos las etiquetas para diferenciar los eventos ocurridos en el territorio y en la frontera
    country = []
    for i in flashb.geometry.index:
        if i in flashC.geometry.index:
            country.append('COLOMBIA')
        else:
            country.append('FRONTERA')

    #Creamos una etiqueta para los nombres de los departamentos y el mar
    department = []
    indexb = list(flashb.geometry.index)
    indexC = list(flashC.geometry.index)
    for i in indexb:
        if i in indexb and i in indexC:
            department.append(str(flashC.NAME_1[i]))
        else:
            department.append("Fronterizo")
  
    #Creamos una lista de coordenadas de los flashes que ocurren dentro del ROI
    coordinates = []
    for i in indexb: 
        coordinates.append(str(flashb.geometry[i]))   

    #Eliminamos agunos caracteres no deseados
    for i in range(0,len(coordinates)):
        coordinates[i] = coordinates[i].replace('POINT (','')
        coordinates[i] = coordinates[i].replace(')','')
    coordinates = [tuple(map(float, sub.split(' '))) for sub in coordinates]   
    
     #agregamos la cantidad de datos a una tabla
    db=MySQLdb.connect(host='localhost',user='glm',passwd='*****',db='dbGLM') 
    cursor=db.cursor()
    cursor.execute("INSERT INTO Prueba2 (Fecha,Cantidad) VALUES ({},{})",(dateT,len(coordinates)))
    db.commit()
    cursor.close
    db.close() 

    if len(coordinates) == 0:
        time.sleep(20)

    else:
        for i in range(0,len(coordinates)):
            db=MySQLdb.connect(host='localhost',user='glm',passwd='*****',db='dbGLM') 
            cursor=db.cursor()
            cursor.execute(
               "INSERT INTO Prueba (Pais,Dept,Lat,Lon,Date) VALUES ({},{},{},{},{})",
               (str(country[i]),str(department[i]),coordinates[i][0],coordinates[i][1],dateT,)
            )
            db.commit()
            cursor.close
            db.close()
        time.sleep(20)

   
    
    


   




        
    

        
        
