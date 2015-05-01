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

# This file is part of "PRAT Auto Processor".
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
# along with "PRAT Auto Processor".  If not, see <http://www.gnu.org/licenses/>.

#####################################
# Imports
#####################################
# Python native imports
from PyQt4 import QtCore
from os.path import exists, getsize

# Custom imports
import Framework.LoggerCore as LC

#####################################
# Global Variables
#####################################


#####################################
# StatusLoggerTab Class Definition
#####################################
class StatusLoggerTab(QtCore.QThread):

    log_needs_visual_update = QtCore.pyqtSignal()

    def __init__(self, main_window):
        QtCore.QThread.__init__(self)

        # ########## Reference to top level window ##########
        self.main_window = main_window

        # ########## Reference to main_window gui elements ##########
        self.log_browser = self.main_window.log_text_browser

        # ########## Get the instances of the loggers ##########
        self.logger_path = LC.application_log_path

        self.logger_file = open(self.logger_path, 'r')

        # ########## Thread flags ##########
        self.not_abort_flag = True

        # ########## Class Variables ##########
        self.prev_size = None

        self.raw_text = None

        # ########## Make signal/slot connections ##########
        self.connect_signals_to_slots()

        # ########## Start thread ##########
        self.start()

    def connect_signals_to_slots(self):
        self.log_needs_visual_update.connect(self.update_transfer_log_visuals)

    def run(self):
        while self.not_abort_flag:
            if self.log_size_changed():
                self.logger_file.seek(0)
                self.raw_text = self.logger_file.readlines()
                self.log_needs_visual_update.emit()

            self.msleep(100)

    def log_size_changed(self):
        if not exists(self.logger_path):
            return False
        elif getsize(self.logger_path) != self.prev_size:
            self.prev_size = getsize(self.logger_path)
            return True
        return False

    def update_transfer_log_visuals(self):
        self.log_browser.setText("".join(self.raw_text))
        self.log_browser.verticalScrollBar().setValue(self.log_browser.verticalScrollBar().maximum())

    def on_kill_threads_slot(self):
        self.not_abort_flag = False