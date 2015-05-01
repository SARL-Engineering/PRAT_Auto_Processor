"""
    Main file used to launch the prat transfer gui.
    No other files should be used for launching this application.
"""

__author__ = "Corwin Perren"
__copyright__ = "None"
__credits__ = [""]
__license__ = "GPL (GNU General Public License)"
__version__ = "0.1 Alpha"
__maintainer__ = "Corwin Perren"
__email__ = "caperren@caperren.com"
__status__ = "Development"

# This file is part of "PRAT Transfer Utility".
#
# "Pick And Plate" is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# "Pick And Plate" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "PRAT Transfer Utility".  If not, see <http://www.gnu.org/licenses/>.

#####################################
# Imports
#####################################
# Python native imports
from PyQt4 import QtCore, QtGui

# Custom imports

#####################################
# Global Variables
#####################################


#####################################
# SettingsTab Class Definition
#####################################
class SettingsTab(QtCore.QObject):
    def __init__(self, main_window):
        QtCore.QObject.__init__(self)

        # ########## Reference to top level window ##########
        self.main_window = main_window

        # ########## Get the settings instance ##########
        self.settings = QtCore.QSettings()

        # ########## Reference to main_window gui elements ##########
        self.local_video_le = self.main_window.local_video_line_edit
        self.local_video_bb = self.main_window.local_video_browse_button

        self.video_transfer_le = self.main_window.video_transfer_line_edit
        self.video_transfer_bb = self.main_window.video_transfer_browse_button

        self.local_csv_le = self.main_window.local_csv_line_edit
        self.local_csv_bb = self.main_window.local_csv_browse_button

        self.csv_transfer_le = self.main_window.csv_transfer_line_edit
        self.csv_transfer_bb = self.main_window.csv_transfer_browse_button

        self.process_csv_te = self.main_window.process_csv_time_edit
        self.transfer_te = self.main_window.transfer_time_edit
        self.cleanup_age_sb = self.main_window.cleanup_age_spin_box

        # ########## Load all saved schedules ##########
        self.load_saved_settings()

        # ########## Connect buttons to methods ##########
        self.connect_signals_to_slots()

    def connect_signals_to_slots(self):
        self.local_video_le.textChanged.connect(self.save_settings)
        self.local_video_bb.clicked.connect(self.on_local_video_browse_clicked_slot)

        self.video_transfer_le.textChanged.connect(self.save_settings)
        self.video_transfer_bb.clicked.connect(self.on_video_transfer_browse_clicked_slot)

        self.local_csv_le.textChanged.connect(self.save_settings)
        self.local_csv_bb.clicked.connect(self.on_local_csv_browse_clicked_slot)

        self.csv_transfer_le.textChanged.connect(self.save_settings)
        self.csv_transfer_bb.clicked.connect(self.on_csv_transfer_browse_clicked_slot)

        self.process_csv_te.timeChanged.connect(self.save_settings)
        self.transfer_te.timeChanged.connect(self.save_settings)
        self.cleanup_age_sb.valueChanged.connect(self.save_settings)

    def load_saved_settings(self):
        self.local_video_le.setText(self.settings.value("local_video_path", "").toString())
        self.video_transfer_le.setText(self.settings.value("video_transfer_path", "").toString())
        self.local_csv_le.setText(self.settings.value("local_csv_path", "").toString())
        self.csv_transfer_le.setText(self.settings.value("csv_transfer_path", "").toString())

        self.process_csv_te.setTime(QtCore.QTime.fromString(
            self.settings.value("csv_time", "12:00 PM").toString(), "h:mm AP"))

        self.transfer_te.setTime(QtCore.QTime.fromString(
            self.settings.value("transfer_time", "12:00 PM").toString(), "h:mm AP"))

        self.cleanup_age_sb.setValue(self.settings.value("cleanup_age", "365").toInt()[0])

    def save_settings(self):
        self.settings.setValue("local_video_path", self.local_video_le.text())
        self.settings.setValue("video_transfer_path", self.video_transfer_le.text())
        self.settings.setValue("local_csv_path", self.local_csv_le.text())
        self.settings.setValue("csv_transfer_path", self.csv_transfer_le.text())

        self.settings.setValue("csv_time", self.process_csv_te.time().toString("h:mm AP"))
        self.settings.setValue("transfer_time", self.transfer_te.time().toString("h:mm AP"))
        self.settings.setValue("cleanup_age", self.cleanup_age_sb.value())

    def on_local_video_browse_clicked_slot(self):
        self.local_video_le.setText(self.get_folder_dialog_and_results())

    def on_video_transfer_browse_clicked_slot(self):
        self.video_transfer_le.setText(self.get_folder_dialog_and_results())

    def on_local_csv_browse_clicked_slot(self):
        self.local_csv_le.setText(self.get_folder_dialog_and_results())

    def on_csv_transfer_browse_clicked_slot(self):
        self.csv_transfer_le.setText(self.get_folder_dialog_and_results())

    def get_folder_dialog_and_results(self):
        file_dialog = QtGui.QFileDialog(self.main_window)
        file_dialog.setFileMode(QtGui.QFileDialog.DirectoryOnly)
        file_dialog.exec_()

        return file_dialog.selectedFiles()[0]