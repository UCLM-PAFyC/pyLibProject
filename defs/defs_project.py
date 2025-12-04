# authors:
# David Hernandez Lopez, david.hernandez@uclm.es
import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(current_path, '..'))

# from defs import defs_paths
# common_libs_absolute_path = os.path.join(current_path, defs_paths.COMMON_LIBS_RELATIVE_PATH)
# sys.path.append(common_libs_absolute_path)
from pyLibCRSs import CRSsDefines as defs_crs
from pyLibGDAL import defs_gdal

TEMPLATES_PATH = "templates"
NO_COMBO_SELECT = " ... "
EPSG_STRING_PREFIX = "EPSG:"

CRS_PROJECTED_DEFAULT = "EPSG:25830"
CRS_VERTICAL_DEFAULT = "EPSG:5782"

TEMPLATE_PROJECT_FILE = "template.gpkg"
create_options = ['CRS_WKT_EXTENSION=YES',
                  'METADATA_TABLES=YES']

PROJECT_FILE_GPKG_SUFFIX = '.gpkg'

MANAGEMENT_LAYER_NAME = 'management'
MANAGEMENT_FIELD_NAME = 'name'
MANAGEMENT_FIELD_CONTENT = 'content'
MANAGEMENT_FIELD_TEMP = 'temp'
MANAGEMENT_FIELD_REMARKS = 'remarks'
MANAGEMENT_FIELD_GEOMETRY = defs_gdal.LAYERS_GEOMETRY_TAG
fields_by_layer = {}
fields_by_layer[MANAGEMENT_LAYER_NAME] = {}
fields_by_layer[MANAGEMENT_LAYER_NAME][MANAGEMENT_FIELD_NAME] = defs_gdal.type_by_name['string']
fields_by_layer[MANAGEMENT_LAYER_NAME][MANAGEMENT_FIELD_CONTENT] = defs_gdal.type_by_name['string']
fields_by_layer[MANAGEMENT_LAYER_NAME][MANAGEMENT_FIELD_TEMP] = defs_gdal.type_by_name['string']
fields_by_layer[MANAGEMENT_LAYER_NAME][MANAGEMENT_FIELD_REMARKS] = defs_gdal.type_by_name['string']
fields_by_layer[MANAGEMENT_LAYER_NAME][MANAGEMENT_FIELD_GEOMETRY] = defs_gdal.geometry_type_by_name['none']

LOCATIONS_LAYER_NAME = 'locations'
LOCATIONS_FIELD_NAME = 'name'
LOCATIONS_FIELD_CONTENT = 'content'
LOCATIONS_FIELD_TEMP = 'temp'
LOCATIONS_FIELD_REMARKS = 'remarks'
LOCATIONS_FIELD_GEOMETRY = defs_gdal.LAYERS_GEOMETRY_TAG
fields_by_layer[LOCATIONS_LAYER_NAME] = {}
fields_by_layer[LOCATIONS_LAYER_NAME][LOCATIONS_FIELD_NAME] = defs_gdal.type_by_name['string']
fields_by_layer[LOCATIONS_LAYER_NAME][LOCATIONS_FIELD_CONTENT] = defs_gdal.type_by_name['string']
fields_by_layer[LOCATIONS_LAYER_NAME][LOCATIONS_FIELD_TEMP] = defs_gdal.type_by_name['string']
fields_by_layer[LOCATIONS_LAYER_NAME][LOCATIONS_FIELD_REMARKS] = defs_gdal.type_by_name['string']
fields_by_layer[LOCATIONS_LAYER_NAME][LOCATIONS_FIELD_GEOMETRY] = defs_gdal.geometry_type_by_name['polygon']

restrictions_in_fields_by_layer = {} # to add restrictions in fields example:
# restrictions_in_fields_by_layer[MANAGEMENT_LAYER_NAME][FIELD_ID] = ['PRIMARY KEY', 'NOT NULL']