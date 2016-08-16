import subprocess

import fiona
import shapely
import shapefile
import os
from osgeo import ogr

OGR2OGR_PATH = '/home/silent/anaconda2/bin/ogr2ogr'

mask_types = ['osm','ned']
option_types = ['filter_start_points', 'filter_end_points', 'filter_intersection']

script_path = os.path.dirname(os.path.realpath(__file__))
temp_path = script_path + '/temp/'

def clear_temp_dir():
    filelist = [ f for f in os.listdir(temp_path)]
    for f in filelist:
        print f
        #os.remove(f)

def generate_start_points_layer (input_shapefile_path, output_shapefile_path):
    # Open shapefile
    sf = shapefile.Reader(input_shapefile_path)
    shapes = sf.shapes()
    records = sf.records()

    pts_cords = []
    for shape in shapes:
        pts_cords.append(shape.points[0])

    pts_atr = []
    for record in records:
        pts_atr.append(record)

    output = shapefile.Writer(shapefile.POINT)
    output.field('ID','C','40')

    i = 0
    while i < len(shapes):
        output.point (pts_cords[i][0],pts_cords[i][1])
        output.record (pts_atr[i][0])
        i += 1

    output.save(output_shapefile_path)

def generate_end_points_layer (input_shapefile_path, output_shapefile_path):
    # Open shapefile
    sf = shapefile.Reader(input_shapefile_path)
    shapes = sf.shapes()
    records = sf.records()

    pts_cords = []
    for shape in shapes:
        pts_cords.append(shape.points[len(shape.points)-1])

    pts_atr = []
    for record in records:
        pts_atr.append(record)

    output = shapefile.Writer(shapefile.POINT)
    output.field('ID','C','40')

    i = 0
    while i < len(shapes):
        output.point (pts_cords[i][0],pts_cords[i][1])
        output.record (pts_atr[i][0])
        i += 1

    output.save(output_shapefile_path)

def clip_vector_layer_by_bbox (input_shapefile_path, output_shapefile_path, xmin,ymin,xmax,ymax):
    cmd = '-clipsrc ' + str(xmin) + ' ' + str(ymin) + ' ' + str(xmax) + ' ' + str(ymax) + ' ' + output_shapefile_path + ' ' + input_shapefile_path
    clip = subprocess.check_output(OGR2OGR_PATH + ' {}'.format(cmd), shell=True)

def mask_filter (input_shapefile_path, option, mask_type = 'osm'):
    if mask_type not in mask_types:
        print 'invalid mask type'
        return -1

    if option not in option_types:
        print 'invalid option'
        return -1

    #clear_temp_dir()

    if mask_type == 'osm':
        mask_path = script_path + '/land_masks/osm_simplified.shp'
    if mask_type == 'ned':
        mask_path = script_path + '/land_masks/ned.shp'

    # PREPARE CUTTED MASK LAYER
    drv = ogr.GetDriverByName('ESRI Shapefile')

    user_layer_source = drv.Open(input_shapefile_path)
    user_layer = user_layer_source.GetLayer(0)
    user_layer_bounds = user_layer.GetExtent()

    clipped_mask_path = temp_path + 'clipped_mask.shp'
    clip_vector_layer_by_bbox(mask_path,clipped_mask_path,user_layer_bounds[0],user_layer_bounds[2],user_layer_bounds[1],user_layer_bounds[3])

    clipped_mask_source = drv.Open(clipped_mask_path)
    clipped_mask_layer = clipped_mask_source.GetLayer(0)

    fid_list = []

    if option == 'filter_intersection':
        for mask_feature in clipped_mask_layer:
            mask_feature_geom = mask_feature.GetGeometryRef()
            user_layer.ResetReading()
            for user_feature in user_layer:
                user_feature_geom = user_feature.GetGeometryRef()
                if mask_feature_geom.Intersects(user_feature_geom):
                    fid_list.append(user_feature.GetFID())


    if (option == 'filter_start_points') or (option == 'filter_end_points'):
        points_path = temp_path + 'points.shp'
        if option == 'filter_start_points':
            generate_start_points_layer(input_shapefile_path,points_path)
        else:
            generate_end_points_layer(input_shapefile_path,points_path)

        points_source = drv.Open(points_path)
        points_layer = points_source.GetLayer(0)
        for mask_feature in clipped_mask_layer:
            mask_feature_geom = mask_feature.GetGeometryRef()
            points_layer.ResetReading()
            for point_feature in points_layer:
                point_feature_geom = point_feature.GetGeometryRef()
                if mask_feature_geom.Intersects(point_feature_geom):
                    fid_list.append(point_feature.GetFID())

    # now we have ids of features, which must be deleted


mask_filter('/home/silent/filter_test/drift1.shp','filter_end_points')
