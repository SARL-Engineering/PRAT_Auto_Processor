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
from PyQt4 import QtCore
import os
import logging
from distutils.dir_util import copy_tree
import time

# Custom imports

#####################################
# Global Variables
#####################################


#####################################
# QueueProcessor Class Definition
#####################################
class QueueProcessor(QtCore.QThread):

    task_done = QtCore.pyqtSignal()

    def __init__(self, master, task):
        QtCore.QThread.__init__(self)

        self.master = master

        # ########## Get the instances of the loggers ##########
        self.transfer_logger = logging.getLogger("TRANSFER_PRAT")
        self.cleanup_logger = logging.getLogger("CLEANUP_PRAT")

        self.task = list(task)

        self.task_done.connect(self.master.on_task_done_slot)

        self.start()

    def run(self):
        a = self.task[0].replace("\\", "/")
        b = self.task[1].replace("\\", "/")
        a_to_b = self.task[2]
        clean_a = self.task[3]
        c_a_if_in_b = self.task[4]
        c_b_and_a = self.task[5]
        cleanup_age = self.task[6]

        is_error = False

        if (a_to_b == "True") and not is_error:
            if os.path.isdir(a) and os.path.isdir(b):
                try:
                    self.transfer_logger.info("Transferring " + a + " to " + b)

                    start_time = time.clock()
                    copy_tree(a, b)
                    stop_time = time.clock()
                    diff_time = str(stop_time-start_time)

                    self.transfer_logger.info("Transferred " + a + " to " + b + " in " + diff_time + " seconds.\n")

                except Exception, e:
                    self.transfer_logger.info("Directories exist, but file copy failed! Please check permissions.\n" +
                                              str(e) + "\n")
            else:
                is_error = True
                self.transfer_logger.info("One or both of the specified paths does not exist. File copy failed.\n"
                                          + "Please check paths:\n" + a + " and " + b + ".\n")

        if (clean_a == "True") and (c_a_if_in_b == "False") and not is_error:
            if os.path.isdir(a):
                is_error = self.clean_path(a, "", "False", cleanup_age)
            else:
                is_error = True
                self.cleanup_logger.info("The specified path does not exist. Folder cleanup failed.\n" +
                                         "Please check path: " + a)

        elif (clean_a == "True") and not is_error:
            if os.path.isdir(a) and os.path.isdir(b):
                self.clean_path(a, b, c_a_if_in_b, cleanup_age)
                if c_b_and_a == "True":
                    self.clean_path(b, b, "False", cleanup_age)
            else:
                self.cleanup_logger.info("One or both of the specified paths does not exist. Folder cleanup failed.\n" +
                                         "Please check paths:\n" + a + " and " + b + ".\n")

        self.task_done.emit()

    def clean_path(self, a, b, check_b_before_clean, age):
        for file_folder in os.listdir(a):
            file_path_a = os.path.join(a, file_folder)
            file_path_b = os.path.join(b, file_folder)

            try:
                if os.path.isfile(file_path_a):
                    if os.path.getmtime(file_path_a) < (time.time() - (86400 * int(age[:-5]))):
                        if check_b_before_clean == "True":
                            if os.path.exists(file_path_b):
                                os.unlink(file_path_a)
                                self.cleanup_logger.info("Cleaned up file: " + str(file_path_a))
                        else:
                            os.unlink(file_path_a)
                            self.cleanup_logger.info("Cleaned up file: " + str(file_path_a))

                elif os.path.isdir(file_path_a):
                    self.clean_path(file_path_a, file_path_b, check_b_before_clean, age)
                    for dirpath, dirnames, files in os.walk(file_path_a):
                        if not files:
                            os.rmdir(file_path_a)
                            self.cleanup_logger.info("Cleaned up empty folder: " + str(file_path_a))
            except Exception, e:
                self.cleanup_logger.info("Directory(s) exists, but cleanup failed. Please check permissions.")
                return True

        return False


#####################################
# ScheduleHandler Class Definition
#####################################
class ScheduleHandler(QtCore.QThread):
    def __init__(self, main_window):
        QtCore.QThread.__init__(self)

        # ########## Reference to top level window ##########
        self.main_window = main_window

        # ########## Get the settings instance ##########
        self.settings = QtCore.QSettings()

        # ########## Thread flags ##########
        self.not_abort_flag = True

        # ########## Class Variables ##########
        # Form of {{a, b, a_to_b, clean_a, c_a_if_in_b, c_b_and_a, cleanup_age},
        # {a, b, a_to_b, clean_a, c_a_if_in_b, c_b_and_a, cleanup_age}}
        self.to_process = []
        self.processing_thread = None
        self.processed = []  # Stored here once done processing

        # ########## Make signal/slot connections ##########
        self.connect_signals_to_slots()

        # ########## Start timer ##########
        self.start()

    def connect_signals_to_slots(self):
        pass

    def run(self):
        while self.not_abort_flag:
            self.check_for_midnight_reset()
            self.check_schedules_and_add_to_queue()
            self.process_queue_to_threads()
            self.msleep(100)

    def check_for_midnight_reset(self):
        current_time = QtCore.QTime.currentTime()
        midnight = QtCore.QTime.fromString("12:00:00 AM", "h:mm:ss AP")

        if current_time.toString("h:mm:ss AP") == midnight.toString("h:mm:ss AP"):
            self.processed = []
            self.msleep(1000)

    def check_schedules_and_add_to_queue(self):
        current_time = QtCore.QTime.currentTime()

        self.settings.beginGroup("TransferTable")
        for i in range(self.settings.childGroups().count()):
            self.settings.beginGroup(str(i))

            if self.settings.value("enabled").toString() == "True":
                sched_time = QtCore.QTime.fromString(self.settings.value("schedule").toString(), "h:mm AP")
                if (sched_time.hour() == current_time.hour()) and (sched_time.minute() == current_time.minute()):
                    a = self.settings.value("source").toString()
                    b = self.settings.value("destination").toString()
                    cleanup = self.settings.value("cleanup").toString()
                    cleanup_age = self.settings.value("cleanup_age").toString()
                    self.add_if_new_to_queue(a, b, "True", cleanup, cleanup, "False", cleanup_age)
            self.settings.endGroup()
        self.settings.endGroup()

        self.settings.beginGroup("CleanupTable")
        for i in range(self.settings.childGroups().count()):
            self.settings.beginGroup(str(i))

            if self.settings.value("enabled").toString() == "True":
                sched_time = QtCore.QTime.fromString(self.settings.value("schedule").toString(), "h:mm AP")
                if (sched_time.hour() == current_time.hour()) and (sched_time.minute() == current_time.minute()):
                    a = self.settings.value("a_path").toString()
                    b = self.settings.value("b_path").toString()
                    a_if_in_b = self.settings.value("a_if_in_b").toString()
                    b_and_a = self.settings.value("b_and_a").toString()
                    cleanup_age = self.settings.value("cleanup_age").toString()
                    self.add_if_new_to_queue(a, b, "False", "True", a_if_in_b, b_and_a, cleanup_age)

            self.settings.endGroup()
        self.settings.endGroup()

    def add_if_new_to_queue(self, a, b, a_to_b, clean_a, c_a_if_in_b, c_b_and_a, cleanup_age):
        new_entry = [str(a), str(b), str(a_to_b), str(clean_a), str(c_a_if_in_b), str(c_b_and_a), str(cleanup_age)]

        if (new_entry not in self.to_process) and (new_entry not in self.processed):
            self.to_process.append(new_entry)

    def process_queue_to_threads(self):
        if not self.processing_thread:
            if self.to_process:
                self.processing_thread = QueueProcessor(self, self.to_process[0])
                self.processed.append(self.to_process[0])
                del self.to_process[0]

    def on_task_done_slot(self):
        self.processing_thread = None

    def on_kill_threads_slot(self):
        self.not_abort_flag = False