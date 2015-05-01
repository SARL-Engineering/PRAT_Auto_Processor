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
from os import getenv, makedirs
from os.path import exists
import logging

# Custom imports

#####################################
# Global Variables
#####################################
application_hidden_path_root = getenv('APPDATA') + "\\PRAT Auto Processor"
application_log_path = application_hidden_path_root + "\\log.txt"


#####################################
# Logger Class Definition
#####################################
class Logger(QtCore.QObject):
    def __init__(self, main_window):
        QtCore.QObject.__init__(self)
        # ########## Reference to top level window ##########
        self.main_window = main_window

        # ########## Get the instances of the loggers ##########
        self.logger = logging.getLogger("PRAT Auto Processor")

        # ########## Set up logger with desired settings ##########
        self.setup_logger()

        # ########## Get the logging file ##########
        self.logger_file = open(application_log_path, 'a')

        # ########## Place divider in log file to see new program launch ##########
        self.add_startup_log_buffer_text()

    def setup_logger(self):
        # fmt='%(levelname)s : %(asctime)s :  %(message)s'  In case this needs to be fixed later
        formatter = logging.Formatter(fmt='%(asctime)s :  %(message)s', datefmt='%m/%d/%y %H:%M:%S')

        if not exists(application_hidden_path_root):
            makedirs(application_hidden_path_root)

        self.logger.setLevel(logging.DEBUG)
        transfer_file_handler = logging.FileHandler(filename=application_log_path)
        transfer_file_handler.setFormatter(formatter)
        transfer_file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(transfer_file_handler)

    def add_startup_log_buffer_text(self):
        self.logger_file.write("\n########## New Instance of Application Started ##########\n\n")
        self.logger_file.close()
