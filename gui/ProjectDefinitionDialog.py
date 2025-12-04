# authors:
# David Hernandez Lopez, david.hernandez@uclm.es

import os
import sys
import math
import json

from PyQt5 import QtCore, QtWidgets
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import (QApplication, QMessageBox, QDialog, QTreeWidgetItem,
                             QFileDialog, QPushButton, QComboBox, QPlainTextEdit, QLineEdit,
                             QDialogButtonBox, QVBoxLayout, QTableWidget, QTableWidgetItem, QInputDialog)
from PyQt5.QtCore import QDir, QFileInfo, QFile, QSize, Qt, QDate

current_path = os.path.dirname(os.path.realpath(__file__))
# current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(current_path, '..'))
sys.path.append(os.path.join(current_path, '../..'))
# sys.path.insert(0, '..')
# sys.path.insert(0, '../..')


from pyLibCRSs.CompoundProjectedCRSDialog import CompoundProjectedCRSDialog
from pyLibCRSs import CRSsDefines as defs_crs
from pyLibQtTools import Tools
from pyLibQtTools.Tools import SimpleTextEditDialog
from pyLibQtTools.CalendarDialog import CalendarDialog
from pyLibProject.defs import defs_project_definition

class ProjectDefinitionDialog(QDialog):
    """Employee dialog."""

    def __init__(self,
                 project,
                 title,
                 is_process_creation,
                 display_sucess_save = False,
                 parent=None):
        super().__init__(parent)
        loadUi(os.path.join(os.path.dirname(__file__), 'ProjectDefinitionDialog.ui'), self)
        self.project = project
        self.last_path = None
        self.title = title
        self.is_process_creation = is_process_creation
        self.active_crs_line_edit_widget = None
        self.is_saved = False
        self.display_sucess_save = display_sucess_save
        self.initialize(title)

    def initialize(self, title):
        name = self.project.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_NAME]
        tag = self.project.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_TAG]
        author = self.project.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_AUTHOR]
        description = self.project.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_DESCRIPTION]
        output_path = self.project.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_OUTPUT_PATH]
        crs_id = self.project.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_CRS]
        str_start_date = self.project.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_START_DATE]
        str_finish_date = self.project.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_FINISH_DATE]
        current_date = QDate.currentDate()
        if not str_start_date:
            start_date = current_date
        else:
            start_date = QDate.fromString(str_start_date, defs_project_definition.QDATE_TO_STRING_FORMAT)
        if not str_finish_date:
            finish_date = QDate.fromJulianDay(current_date.toJulianDay() + 365)
        else:
            finish_date = QDate.fromString(str_finish_date, defs_project_definition.QDATE_TO_STRING_FORMAT)
        self.nameLineEdit.setText(name)
        self.tagLineEdit.setText(tag)
        self.authorLineEdit.setText(author)
        self.descriptionLineEdit.setText(description)
        if output_path:
            if os.path.exists(output_path):
                self.outputPathLineEdit.setText(output_path)
        self.startDateEdit.setDate(start_date)
        self.finishDateEdit.setDate(finish_date)
        self.crsLineEdit.setText(crs_id)
        self.last_path = self.project.settings.value("last_path")
        current_dir = QDir.current()
        if not self.last_path:
            self.last_path = QDir.currentPath()
            self.project.settings.setValue("last_path", self.last_path)
            self.project.settings.sync()
        self.setWindowTitle(title)
        self.savePushButton.clicked.connect(self.save)
        self.namePushButton.clicked.connect(self.select_name)
        self.tagPushButton.clicked.connect(self.select_tag)
        self.authorPushButton.clicked.connect(self.select_author)
        self.descriptionPushButton.clicked.connect(self.select_description)
        self.outputPathPushButton.clicked.connect(self.select_output_path)
        self.crsPushButton.clicked.connect(self.select_crs)

    def save(self):
        name = self.nameLineEdit.text()
        tag = self.tagLineEdit.text()
        author = self.authorLineEdit.text()
        description = self.descriptionLineEdit.text()
        output_path = self.outputPathLineEdit.text()
        star_date_as_str = self.startDateEdit.date().toString(defs_project_definition.QDATE_TO_STRING_FORMAT)
        finish_date_as_str = self.finishDateEdit.date().toString(defs_project_definition.QDATE_TO_STRING_FORMAT)
        crs_id = self.crsLineEdit.text()
        self.project.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_NAME] = name
        self.project.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_TAG] = tag
        self.project.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_AUTHOR] = author
        self.project.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_CRS] = crs_id
        self.project.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_OUTPUT_PATH] = output_path
        self.project.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_DESCRIPTION] = description
        self.project.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_START_DATE] = star_date_as_str
        self.project.project_definition[defs_project_definition.PROJECT_DEFINITIONS_TAG_FINISH_DATE] = finish_date_as_str
        str_aux_error = self.project.save()
        if str_aux_error:
            str_error = ('Error saving project definition:\n{}'.
                         format(str_aux_error))
            Tools.error_msg(str_error)
            self.is_saved = False
            return
        else:
            if self.display_sucess_save:
                str_msg = "Process completed"
                Tools.info_msg(str_msg)
        self.is_saved = True
        self.accept()
        return

    def select_author(self):
        current_text = self.authorLineEdit.text()
        text, okPressed = QInputDialog.getText(self, "Author", "Enter author:",
                                               QLineEdit.Normal, current_text)
        if okPressed and text != '':
            self.authorLineEdit.setText(text)

    def select_crs(self):
        crs_id = self.crsLineEdit.text()
        dialog = CompoundProjectedCRSDialog(self.project.crs_tools, crs_id)
        dialog_result = dialog.exec()
        if dialog.is_accepted:
            crs_id = dialog.crs_id
            self.crsLineEdit.setText(crs_id)
        return

    def select_description(self):
        current_text = self.descriptionLineEdit.text()
        # text, okPressed = QInputDialog.getText(self, "Description", "Enter description:",
        #                                        QLineEdit.Normal, current_text)
        # if okPressed and text != '':
        #     self.descriptionLineEdit.setText(text)
        title = "Enter description"
        dialog = SimpleTextEditDialog(title, current_text, False)
        ret = dialog.exec()
        # if ret == QDialog.Accepted:
        #     text = dialog.get_text()
        #     self.descriptionLineEdit.setText(text)
        text = dialog.get_text()
        if text != current_text:
            self.descriptionLineEdit.setText(text)

    def select_name(self):
        current_text = self.nameLineEdit.text()
        text, okPressed = QInputDialog.getText(self, "Name", "Enter name:",
                                               QLineEdit.Normal, current_text)
        if okPressed and text != '':
            self.nameLineEdit.setText(text)

    def select_output_path(self):
        dialog = QtWidgets.QFileDialog()
        # last_dir = QDir(self.project.last_path)
        last_path = self.project.settings.value("last_path")
        if not last_path:
            last_path = QDir.currentPath()
            self.settings.setValue("last_path", last_path)
            self.settings.sync()
        dialog.setDirectory(last_path)
        path = dialog.getExistingDirectory(self, "Select output path")
        if path:
            self.outputPathLineEdit.setText(path)
            self.project.last_path = path
            self.project.settings.setValue("last_path", self.project.last_path)
            self.project.settings.sync()

    def select_tag(self):
        current_text = self.tagLineEdit.text()
        text, okPressed = QInputDialog.getText(self, "Tag", "Enter tag:",
                                               QLineEdit.Normal, current_text)
        if okPressed and text != '':
            self.tagLineEdit.setText(text)
