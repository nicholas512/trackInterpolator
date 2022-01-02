from scipy.interpolate import interp1d
import dateutil.parser
import numpy as np
import pytz

from qgis.PyQt.QtCore import QDateTime
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsField, QgsProject

def timestamp_mapper(GPS_layer, GPS_time, data_table, data_table_time):
    GPS_time = [dateutil.parser.isoparse(t) for t in get_timestamps(GPS_layer, GPS_time)]
    data_time = [dateutil.parser.isoparse(t) for t in get_timestamps(data_table, data_table_time)]
    
    # make both times naieve- we assume they're both UTC
    GPS_time = [dt_tz.replace(tzinfo=None) for dt_tz in GPS_time]
    data_time = [dt_tz.replace(tzinfo=None) for dt_tz in data_time]
    
    geom = get_geometry(GPS_layer)
    f = make_interpolator(GPS_time, geom)
    
    data_geom = [f(t.timestamp()) for t in data_time]
    write_geometry(data_table, data_geom)
    print(list(zip(data_time, data_geom)))
    return zip(data_time, data_geom)

# Get geometry + timestamp from GPS track
# sort by timestamp
# convert timestamp to seconds after 2010
# create 1d interpolation on X and Y coordinates
# get timestamp from table data
# convert timestamps into seconds 
# use interpolated function to get (X,Y)
# (create new spatial layer with same coordinates? add XY to table?)

def write_geometry(data, geom):
    vl = QgsVectorLayer("Point", "temporary_points", "memory")
    pr = vl.dataProvider()
    
    # Enter editing mode
    vl.startEditing()
    
    # add fields
    for field in data.fields():
        pr.addAttributes([ QgsField(field.name(), field.type())] )
    
    data_features = data.getFeatures() # getFeature(i) might have leading 'dummy' features
    # add a feature
    for i, g in enumerate(geom):
        feature = next(data_features)
        fet = QgsFeature()
        fet.setGeometry( QgsGeometry.fromPointXY(QgsPointXY(g[0],g[1])) )
        fet.setAttributes(feature.attributes())
        pr.addFeatures( [ fet ] )
    # Commit changes
    vl.commitChanges()
    # Show in project
    QgsProject.instance().addMapLayer(vl)

def make_interpolator(timestamps: list, geom: list):
    x = [t.timestamp() for t in timestamps]
    y = np.array(geom)
    f = interp1d(x, y.transpose(), fill_value='extrapolate')
    return f

def get_geometry(layer):
    if len(layer) < 1:
        raise ValueError("No features in layer")
    
    geoms = []
    for feature in layer.getFeatures():
        geom = feature.geometry().asPoint()
        geoms.append((geom.x(), geom.y()))
    return geoms

def get_timestamps(layer, fieldname):
    if len(layer) < 1:
        raise ValueError("No features in layer")
    
    ti = [i for i, field in enumerate(layer.fields()) if field.name() == fieldname][0] # TODO: get index from combovox instead of name
    isQ = isinstance(layer.getFeature(0).attributes()[ti], QDateTime)
    
    times = list()
    
    for feature in layer.getFeatures():
        time = feature.attributes()[ti]
        if isQ:
            time = time.toString(format=Qt.ISODate)
        times.append(time)
    return times

