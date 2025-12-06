# authors:
# David Hernandez Lopez, david.hernandez@uclm.es

import os
import sys
import json
import xmltodict

from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog, QFileDialog, QPushButton, QComboBox
from PyQt5.QtCore import QDir, QFileInfo, QFile, QDate, QDateTime

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(current_path, '..'))
sys.path.append(os.path.join(current_path, '../..'))

from pyLibProcesses.defs import defs_project as processes_defs_project
from pyLibProcesses.defs import defs_processes as processes_defs_processes
# from pyLibPhotogrammetry.defs import defs_project, defs_processes
# from pyLibPhotogrammetry.defs import defs_images as defs_img
# from pyLibPhotogrammetry.defs import defs_metashape_markers as defs_msm
from pyLibParameters import defs_pars
from pyLibParameters.ParametersManager import ParametersManager
# from pyLibPhotogrammetry.gui.ProjectDefinitionDialog import ProjectDefinitionDialog
# from pyLibPhotogrammetry.lib.ATBlockMetashape import ATBlockMetashape
# from pyLibPhotogrammetry.lib.IExifTool import IExifTool
from pyLibCRSs import CRSsDefines as defs_crs
from pyLibCRSs.CRSsTools import CRSsTools
from pyLibQtTools import Tools
from pyLibGDAL import defs_gdal
from pyLibGDAL.GDALTools import GDALTools
from pyLibGDAL.PostGISTools import PostGISTools
# from pyLibGDAL.RasterDEM import RasterDEM
from pyLibProject.defs import defs_project_definition
from pyLibProject.gui.ProjectDefinitionDialog import ProjectDefinitionDialog
from pyLibProject.defs import defs_project

class Project:
    def __init__(self,
                 qgis_iface,
                 settings,
                 crs_tools):
        self.qgis_iface = qgis_iface
        self.settings = settings
        self.file_path = None
        self.project_definition = {}
        self.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_NAME] = None
        self.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_TAG] = None
        self.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_AUTHOR] = None
        self.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_CRS] = defs_project_definition.CRS_DEFAULT
        self.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_OUTPUT_PATH] = None
        self.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_DESCRIPTION] = None
        self.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_START_DATE] = None
        self.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_FINISH_DATE] = None
        self.crs_id = ''
        self.crs_tools = crs_tools
        # self.gpkg_tools = None
        self.locations_layer_name = None
        self.map_views = {}
        self.process_by_label = {}
        self.sqls_to_process = []
        self.initialize()

    def create_layers(self,
                      file_path = None,
                      db_schema = None): # file_path is None, set sqls
        str_error = ''
        self.sqls_to_process.clear()
        for layer_name in defs_project.fields_by_layer:
            layers_definition = {}
            layers_definition[layer_name] = {}
            layers_definition[layer_name] \
                = defs_project.fields_by_layer[layer_name]
            layers_crs_id = {}
            if defs_project.fields_by_layer[layer_name][defs_gdal.LAYERS_GEOMETRY_TAG] == defs_gdal.geometry_type_by_name['none']:
                layers_crs_id[layer_name] = None
            else:
                # project_crs_id =  self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_PROJECTED_CRS]
                # self.project_definition[defs_project.PROJECT_DEFINITIONS_TAG_VERTICAL_CRS] = defs_project.CRS_VERTICAL_DEFAULT
                layer_crs_id = self.crs_id
                layers_crs_id[layer_name] = layer_crs_id
            ignore_existing_layers = True  # create new gpkg
            create_options = defs_project.create_options
            if file_path:
                str_error = GDALTools.create_vector(file_path,
                                                    layers_definition,
                                                    layers_crs_id,
                                                    ignore_existing_layers,
                                                    create_options)
                if str_error:
                    str_error = (
                        'Creating layer:\n{}\nin file:\n{}\nError:\n{}'.format(layer_name, file_path, str_error))
                    return str_error
            else:
                str_error, sqls = PostGISTools.get_sql_create_spatial_table(layers_definition,
                                                                            layers_crs_id,
                                                                            defs_project.restrictions_in_fields_by_layer,
                                                                            db_schema)
                if str_error:
                    str_error = (
                        'Getting SQLs for creating layer:\n{}\nError:\n{}'.format(layer_name, str_error))
                    return str_error
                for sql in sqls:
                    self.sqls_to_process.append(sql)
        return str_error

    def get_map_views(self):
        return self.map_views.keys()

    def initialize(self):
        self.crs_id = self.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_CRS]
        if self.qgis_iface:
            self.qgis_iface.set_project(self)
        return

    def load_map_views(self,
                       wfs = None):# [wfs_url, wfs_user, wfs_password]):
        str_error = ''
        self.map_views.clear()
        if self.locations_layer_name is None:
            self.locations_layer_name = defs_project.LOCATIONS_LAYER_NAME
        file_path = self.file_path
        # str_error, layer_names = self.gpkg_tools.get_layers_names(file_name)
        str_error, layer_names = GDALTools.get_layers_names(file_path = file_path,
                                                            wfs = wfs)
        if str_error:
            str_error = ('Loading gpgk:\n{}\nError:\n{}'.
                         format(file_path, str_error))
            return str_error
        if not self.locations_layer_name in layer_names:
            str_error = ('Loading gpgk:\n{}\nError: not exists layer:\n{}'.
                         format(file_path, defs_project.LOCATIONS_LAYER_NAME))
            return str_error
        layer_name = self.locations_layer_name
        fields = defs_project.fields_by_layer[defs_project.LOCATIONS_LAYER_NAME]
        fields = {}
        field_name = defs_project.LOCATIONS_FIELD_NAME
        # provisional porque no lee el campo name
        field_name = defs_project.LOCATIONS_FIELD_TEMP
        fields[field_name] = defs_project.fields_by_layer[defs_project.LOCATIONS_LAYER_NAME][field_name]
        field_geometry = defs_project.LOCATIONS_FIELD_GEOMETRY
        fields[field_geometry] = defs_project.fields_by_layer[defs_project.LOCATIONS_LAYER_NAME][field_geometry]
        filter_fields = None
        str_error, features = GDALTools.get_features(file_path,
                                                     layer_name,
                                                     fields,
                                                     filter_fields,
                                                     wfs = wfs)
        if str_error:
            str_error = ('Getting locations from gpgk:\n{}\nError:\n{}'.
                         format(file_path, str_error))
            return str_error
        for i in range(len(features)):
            # name = features[i][defs_project.LOCATIONS_FIELD_NAME]
            # provisional porque no lee el campo name
            name = features[i][defs_project.LOCATIONS_FIELD_TEMP]
            wkb_geometry = features[i][defs_project.LOCATIONS_FIELD_GEOMETRY]
            self.map_views[name] = wkb_geometry
        return str_error

    def load_project_definition(self,
                                file_path = None,
                                db_schema = None):
        str_error = ''
        self.sqls_to_process.clear()

        # "Project Definition"
        layer_name = defs_project.MANAGEMENT_LAYER_NAME
        fields = defs_project.fields_by_layer[defs_project.MANAGEMENT_LAYER_NAME]
        fields = {}
        field_name = defs_project.MANAGEMENT_FIELD_CONTENT
        fields[field_name] = defs_project.fields_by_layer[layer_name][field_name]
        filter_fields = {}
        filter_field_name = defs_project.MANAGEMENT_FIELD_NAME
        filter_field_value = defs_project_definition.PROJECT_DEFINITIONS_MANAGEMENT_FIELD_NAME
        filter_fields[filter_field_name] = filter_field_value

        if file_path:
            str_error, layer_names = GDALTools.get_layers_names(file_path)
            if str_error:
                str_error = ('Loading gpgk:\n{}\nError:\n{}'.
                             format(file_path, str_error))
                return str_error
            if not defs_project.MANAGEMENT_LAYER_NAME in layer_names:
                str_error = ('Loading gpgk:\n{}\nError: not exists layer:\n{}'.
                             format(file_path, defs_project.MANAGEMENT_LAYER_NAME))
                return str_error
            str_error, features = GDALTools.get_features(file_path,
                                                         layer_name,
                                                         fields,
                                                         filter_fields)
            if str_error:
                str_error = ('Getting {} from management from gpgk:\n{}\nError:\n{}'.
                             format(defs_project.PROJECT_DEFINITIONS_MANAGEMENT_FIELD_NAME,
                                    file_path, str_error))
                return str_error
            if len(features) != 1:
                str_error = (
                    'Loading {} from management from gpgk:\n{}\nError: not one value for field: {} in layer: {}'.
                    format(defs_project.PROJECT_DEFINITIONS_MANAGEMENT_FIELD_NAME,
                           file_path, defs_project.MANAGEMENT_FIELD_CONTENT, defs_project.MANAGEMENT_LAYER_NAME))
                return str_error
            value = features[0][defs_project.MANAGEMENT_FIELD_CONTENT]
            # json_acceptable_string = value.replace("'", "\"")
            # management_json_content = json.loads(json_acceptable_string)
            project_definition_json_content = json.loads(value)
            str_error = self.set_definition_from_json(project_definition_json_content)
            if str_error:
                str_error = (
                    '\nSetting definition from json project file:\n{}\nerror:\n{}'.format(file_path, str_error))
                return str_error
        else:
            str_error, sqls = PostGISTools.get_sql_get_features(layer_name,
                                                                fields,
                                                                filter_fields,
                                                                db_schema = db_schema)
            if str_error:
                str_error = (
                    'Getting SQLs for get features from layer:\n{}\nError:\n{}'.format(layer_name, str_error))
                return str_error
            for sql in sqls:
                self.sqls_to_process.append(sql)
        return str_error

    def project_definition_gui(self,
                               is_process_creation,
                               parent_widget = None):
        str_error = ""
        title = defs_project_definition.PROJECT_DEFINITION_DIALOG_TITLE
        dialog = ProjectDefinitionDialog(self, title, is_process_creation,
                                         display_sucess_save = False, parent = parent_widget)
        dialog_result = dialog.exec()
        # if dialog_result != QDialog.Accepted:
        #     return str_error
        definition_is_saved = dialog.is_saved
        if dialog_result != QDialog.Accepted:
            return str_error, definition_is_saved
        return str_error, definition_is_saved

    def save(self):
        str_error = ""
        yo = 1
        return str_error

    def save_project_definition(self,
                                update=False,
                                file_path = None,
                                db_schema = None):
        str_error = ""
        # value_as_string = str(self.project_definition)
        value_as_json = json.dumps(self.project_definition, indent=4)
        features = []
        feature = []
        field = {}
        field[defs_gdal.FIELD_NAME_TAG] = defs_project.MANAGEMENT_FIELD_NAME
        field[defs_gdal.FIELD_TYPE_TAG] \
            = defs_project.fields_by_layer[defs_project.MANAGEMENT_LAYER_NAME][defs_project.MANAGEMENT_FIELD_NAME]
        field[defs_gdal.FIELD_VALUE_TAG] = defs_project_definition.PROJECT_DEFINITIONS_MANAGEMENT_FIELD_NAME
        feature.append(field)
        field = {}
        field[defs_gdal.FIELD_NAME_TAG] = defs_project.MANAGEMENT_FIELD_CONTENT
        field[defs_gdal.FIELD_TYPE_TAG] \
            = defs_project.fields_by_layer[defs_project.MANAGEMENT_LAYER_NAME][defs_project.MANAGEMENT_FIELD_CONTENT]
        field[defs_gdal.FIELD_VALUE_TAG] = value_as_json
        feature.append(field)
        geometry_value = None
        field = {}
        field[defs_gdal.FIELD_NAME_TAG] = defs_project.MANAGEMENT_FIELD_GEOMETRY
        field[defs_gdal.FIELD_TYPE_TAG] \
            = defs_project.fields_by_layer[defs_project.MANAGEMENT_LAYER_NAME][defs_project.MANAGEMENT_FIELD_GEOMETRY]
        field[defs_gdal.FIELD_VALUE_TAG] = defs_project.fields_by_layer[
            defs_project.MANAGEMENT_LAYER_NAME][defs_project.MANAGEMENT_FIELD_GEOMETRY]
        feature.append(field)
        features.append(feature)
        features_by_layer = {}
        features_by_layer[defs_project.MANAGEMENT_LAYER_NAME] = features
        if file_path is None:
            if not update:
                str_error, sqls = PostGISTools.get_sql_write_features(features_by_layer,
                                                                      db_schema)
                if str_error:
                    str_error = (
                        'Getting SQLs for write features in layer:\n{}\nError:\n{}'.format(layer_name, str_error))
                    return str_error
                for sql in sqls:
                    self.sqls_to_process.append(sql)
        else:
            yo = 1

        # if not update:
        #     str_error = GDALTools.write_features(self.file_path, features_by_layer)
        #     # str_error = self.gpkg_tools.write(self.file_name,
        #     #                                   features_by_layer)
        # else:
        #     features_filters = []
        #     feature_filters= []
        #     filter = {}
        #     filter[defs_gdal.FIELD_NAME_TAG] = defs_project.MANAGEMENT_FIELD_NAME
        #     filter[defs_gdal.FIELD_TYPE_TAG] \
        #         = defs_project.fields_by_layer[defs_project.MANAGEMENT_LAYER_NAME][defs_project.MANAGEMENT_FIELD_NAME]
        #     filter[defs_gdal.FIELD_VALUE_TAG] = defs_project.PROJECT_DEFINITIONS_MANAGEMENT_FIELD_NAME
        #     feature_filters.append(filter)
        #     features_filters.append(feature_filters)
        #     features_filters_by_layer = {}
        #     features_filters_by_layer[defs_project.MANAGEMENT_LAYER_NAME] = features_filters
        #     str_error = GDALTools.update_features(self.file_path, features_by_layer, features_filters_by_layer)
        #     # str_error = self.gpkg_tools.update(self.file_name,
        #     #                                    features_by_layer,
        #     #                                    features_filters_by_layer)
        return str_error

    def set_definition_from_json(self, json_content):
        str_error = ''
        if not defs_project_definition.PROJECT_DEFINITIONS_TAG_NAME in json_content:
            str_error = ("No {} in json content {}".format(defs_project_definition.PROJECT_DEFINITIONS_TAG_NAME,
                                                           defs_project_definition.PROJECT_DEFINITIONS_TAG))
            return str_error
        if not defs_project_definition.PROJECT_DEFINITIONS_TAG_TAG in json_content:
            str_error = ("No {} in json content {}".format(defs_project_definition.PROJECT_DEFINITIONS_TAG_TAG,
                                                           defs_project_definition.PROJECT_DEFINITIONS_TAG))
            return str_error
        if not defs_project_definition.PROJECT_DEFINITIONS_TAG_AUTHOR in json_content:
            str_error = ("No {} in json content {}".format(defs_project_definition.PROJECT_DEFINITIONS_TAG_AUTHOR,
                                                           defs_project_definition.PROJECT_DEFINITIONS_TAG))
            return str_error
        if ((not defs_project_definition.PROJECT_DEFINITIONS_TAG_PROJECTED_CRS in json_content
                or not defs_project_definition.PROJECT_DEFINITIONS_TAG_VERTICAL_CRS in json_content)
                and not defs_project_definition.PROJECT_DEFINITIONS_TAG_CRS in json_content):
            str_error = ("No CRS data in json content {}".format(defs_project_definition.PROJECT_DEFINITIONS_TAG))
            return str_error
        if not defs_project_definition.PROJECT_DEFINITIONS_TAG_OUTPUT_PATH in json_content:
            str_error = ("No {} in json content {}".format(defs_project_definition.PROJECT_DEFINITIONS_TAG_OUTPUT_PATH,
                                                           defs_project_definition.PROJECT_DEFINITIONS_TAG))
            return str_error
        if not defs_project_definition.PROJECT_DEFINITIONS_TAG_START_DATE in json_content:
            str_error = ("No {} in json content {}".format(defs_project_definition.PROJECT_DEFINITIONS_TAG_START_DATE,
                                                           defs_project_definition.PROJECT_DEFINITIONS_TAG))
            return str_error
        if not defs_project_definition.PROJECT_DEFINITIONS_TAG_FINISH_DATE in json_content:
            str_error = ("No {} in json content {}".format(defs_project_definition.PROJECT_DEFINITIONS_TAG_FINISH_DATE,
                                                           defs_project_definition.PROJECT_DEFINITIONS_TAG))
            return str_error
        name = json_content[defs_project_definition.PROJECT_DEFINITIONS_TAG_NAME]
        tag = json_content[defs_project_definition.PROJECT_DEFINITIONS_TAG_TAG]
        author = json_content[defs_project_definition.PROJECT_DEFINITIONS_TAG_AUTHOR]
        crs_projected_id = None
        crs_vertical_id = None
        crs_id = None
        if(defs_project_definition.PROJECT_DEFINITIONS_TAG_PROJECTED_CRS in json_content
                and defs_project_definition.PROJECT_DEFINITIONS_TAG_VERTICAL_CRS in json_content):
            crs_projected_id = json_content[defs_project.PROJECT_DEFINITIONS_TAG_PROJECTED_CRS]
            crs_vertical_id = json_content[defs_project.PROJECT_DEFINITIONS_TAG_VERTICAL_CRS]
        else:
            if not defs_project_definition.PROJECT_DEFINITIONS_TAG_CRS in json_content:
                str_error = ("No {} in json content {}".format(defs_project_definition.PROJECT_DEFINITIONS_TAG_CRS,
                                                               defs_project_definition.PROJECT_DEFINITIONS_TAG))
                return str_error
            crs_id = json_content[defs_project_definition.PROJECT_DEFINITIONS_TAG_CRS]
        output_path = json_content[defs_project_definition.PROJECT_DEFINITIONS_TAG_OUTPUT_PATH]
        description = json_content[defs_project_definition.PROJECT_DEFINITIONS_TAG_DESCRIPTION]
        start_date = json_content[defs_project_definition.PROJECT_DEFINITIONS_TAG_START_DATE]
        if start_date:
            date_start_date = QDate.fromString(start_date, defs_project_definition.QDATE_TO_STRING_FORMAT)
            if not date_start_date.isValid():
                str_error = ("Invalid date: {} for format: {}".format(start_date, defs_project_definition.QDATE_TO_STRING_FORMAT))
                return str_error
        finish_date = json_content[defs_project_definition.PROJECT_DEFINITIONS_TAG_FINISH_DATE]
        if finish_date:
            date_finish_date = QDate.fromString(finish_date, defs_project_definition.QDATE_TO_STRING_FORMAT)
            if not date_finish_date.isValid():
                str_error = ("Invalid date: {} for format: {}".format(finish_date, defs_project_definition.QDATE_TO_STRING_FORMAT))
                return str_error
        self.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_NAME] = name
        self.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_TAG] = tag
        self.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_AUTHOR] = author
        if( not crs_projected_id is None and not crs_vertical_id):
            self.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_PROJECTED_CRS] = crs_projected_id
            self.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_VERTICAL_CRS] = crs_vertical_id
            epsg_crs_prefix = defs_crs.EPSG_TAG + ':'
            crs_2d_id = self.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_PROJECTED_CRS]
            crs_2d_epsg_code = int(crs_2d_id.replace(epsg_crs_prefix, ''))
            self.crs_id = epsg_crs_prefix + str(crs_2d_epsg_code)
            crs_vertical_id = self.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_VERTICAL_CRS]
            if crs_vertical_id != defs_crs.VERTICAL_ELLIPSOID_TAG:
                crs_vertical_epsg_code = int(crs_vertical_id.replace(epsg_crs_prefix, ''))
                self.crs_id += ('+' + str(crs_vertical_epsg_code))
        else:
            self.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_CRS] = crs_id
            self.crs_id = crs_id
            if not '+' in crs_id:
                crs_projected_id = crs_id
                crs_vertical_id = None
            else:
                epsg_crs_prefix = defs_crs.EPSG_TAG + ':'
                srs_id = crs_id.replace(defs_crs.EPSG_STRING_PREFIX, ' ')
                srs_id = srs_id.replace('+', ' ')
                srs_id = srs_id.strip()
                values = srs_id.split(' ')
                crs_projected_id = epsg_crs_prefix + values[0]
                crs_vertical_id = epsg_crs_prefix + values[1]
            self.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_PROJECTED_CRS] = crs_projected_id
            self.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_VERTICAL_CRS] = crs_vertical_id
        self.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_OUTPUT_PATH] = output_path
        self.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_DESCRIPTION] = description
        self.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_START_DATE] = start_date
        self.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_FINISH_DATE] = finish_date
        return str_error
