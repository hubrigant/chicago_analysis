#!/usr/bin/env python
import csv
import time
import sys
import pandas as pd
import geopandas as gpd
import shapely
from shapely.ops import nearest_points
from scipy import spatial

def distance_to_nearest(row, geom_union, df1, df2, geom1_col='geometry', geom2_col='geometry', src_column=None):
    """Find the nearest point and return the corresponding value from specified column."""
    distances = []
    # Find the geometry that is closest
    nearest = df2[geom2_col] == nearest_points(row[geom1_col], geom_union)[1]
    #df2.set_index("UNIT_ID")
    # Get the corresponding value from df2 (matching is based on the geometry)
    nearest_id = df2[nearest][src_column].get_values()[0]
    start_point = row['geometry']
    end_point = df2[nearest]['geometry'].iloc[0]
    #end_point = end_point_series.iloc[0]
    dist_to_point = start_point.distance(end_point)
    distances.append(dist_to_point)
    #dist_to_point = []
    return nearest_id, dist_to_point


prefix = sys.argv[1]
filename = sys.argv[2]
colnames = ['record id', 'case no', 'date', 'block', 'iucr','primary type', 'description', 'location description', 'arrest', 'domestic',
            'beat', 'district', 'ward', 'community area', 'fbi code', 'x coordinate', 'y coordinate', 'year', 'updated on', 'latitude',
            'longitude', 'location']
crimesdf = pd.read_csv("{0}/{1}".format(prefix, filename), names=colnames, header=None)
crimesdf.dropna(inplace=True)
print(crimesdf.shape)
del crimesdf['block']
del crimesdf['iucr']
del crimesdf['domestic']
del crimesdf['beat']
del crimesdf['district']
del crimesdf['fbi code']
del crimesdf['x coordinate']
del crimesdf['y coordinate']
del crimesdf['year']
del crimesdf['updated on']
del crimesdf['location']

crimesdf['geometry'] = list(zip(crimesdf['latitude'], crimesdf['longitude']))
crimesdf['geometry'] = crimesdf['geometry'].apply(shapely.geometry.Point)
crimesgpd = gpd.GeoDataFrame(crimesdf)
print(crimesgpd.iloc[0])

# Read in the school locations data, fix the type of the UNIT_ID column, create shapely points from X/Y
# and create the geopandas DataFrame
schools = pd.read_csv("school-locations-2010-2011.csv", index_col=2)
schools['UNIT_ID'] = schools.index
schools = schools.astype({'UNIT_ID': int})
schools['geometry'] = list(zip(schools['X'], schools['Y']))
schools['geometry'] = schools['geometry'].apply(shapely.geometry.Point)
schools = gpd.GeoDataFrame(schools)
schools.info()

# Create unary_union of object from schools dataset
schools_unary_union = schools.unary_union

# Locate the nearest school to each reported crime's location
start_time = time.time()
unpackdf = pd.DataFrame(crimesgpd.apply(distance_to_nearest,
                                      geom_union=schools_unary_union,
                                      df1=crimesgpd,
                                      df2=schools,
                                      src_column='UNIT_ID',
                                      axis=1).tolist(),
                        columns = ['nearest_school_id', 'nearest_school_distance'], index=crimesgpd.index)
crimesgpd=pd.concat([unpackdf, crimesgpd], axis=1)
end_time = time.time()
print("That took {0} seconds".format(end_time - start_time))
print(crimesgpd.head())

start_time2 = time.time()
D = spatial.distance_matrix(crimesgpd['geometry'], schools['geometry'])
nn = np.array([[np.min(d[i,]), np.argmin([i,])] for i in range(crimesgpd['geometry'].shape[0])])
crimesgpd['scypi distance'] = nn[:,0]
crimesgpd['scypi distance2'] = nn[:,1]
end_time = time.time()
print("That took {0} seconds".format(end_time - start_time))
print(crimesgpd.head())
