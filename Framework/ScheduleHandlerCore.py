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
import os
import logging
import shutil
import time
import matlab.engine
import datetime

# Custom imports

#####################################
# Global Variables
#####################################
midnight_qtime_string = QtCore.QTime.fromString("12:00:00 AM", "h:mm:ss AP").toString("h:mm:ss AP")

PROCESS_TASK = 0
TRANSFER_TASK = 1

#####################################
# QueueProcessor Class Definition
#####################################
class QueueProcessor(QtCore.QThread):
    task_done = QtCore.pyqtSignal()

    def __init__(self, master, task_type, local_vid_path, local_csv_path, vid_transfer_path, csv_transfer_path, age):
        QtCore.QThread.__init__(self)

        self.master = master

        # ########## Worker thread variables ##########
        self.task_type = task_type
        self.local_vid_path = str(local_vid_path)
        self.local_csv_path = str(local_csv_path)
        self.vid_transfer_path = str(vid_transfer_path)
        self.csv_transfer_path = str(csv_transfer_path)
        self.cleanup_age = int(age)

        # ########## Get the instances of the loggers ##########
        self.logger = logging.getLogger("PRAT Auto Processor")

        if self.task_type == PROCESS_TASK:
            self.task_done.connect(self.master.on_processing_done_slot)
        elif self.task_type == TRANSFER_TASK:
            self.task_done.connect(self.master.on_transfer_done_slot)

        self.start()

    def run(self):
        if self.task_type == PROCESS_TASK:
            if os.path.isdir(self.local_vid_path):
                if not os.path.isdir(self.local_csv_path):
                    os.makedirs(self.local_csv_path)
                    self.logger.info("Local CSV output folder does not exist. Making directory.")

                count = self.file_count(self.local_vid_path)
                original_out_csv_count = self.file_count(self.local_csv_path)

                if count > 0:
                    self.logger.info("Attempting to process " + str(count) + " SEQ files. This will take some time.")

                    start_time = time.clock()
                    matlab_engine = matlab.engine.start_matlab()
                    matlab_engine.PRAT_Processor(self.local_vid_path, self.local_csv_path)
                    stop_time = time.clock()

                    diff_time_str = str((stop_time-start_time)/60.0)

                    self.logger.info("Processing completed in " + diff_time_str + " minutes.")

                    new_out_csv_count = self.file_count(self.local_csv_path)
                    csv_diff = new_out_csv_count - original_out_csv_count

                    if csv_diff == count:
                        self.logger.info("All SEQ files processed successfully!")
                    else:
                        self.logger.log("SEQ files not processed successfully!" +
                                        " Processed " + str(count) + " SEQ files, but only " + str(csv_diff) +
                                        " CSV files were created. Please check your SEQ files!")
                else:
                    self.logger.info("Attempted to process SEQ files, but none exist.")

            else:
                self.logger.info("Local video path does not exist! Processing failed!" +
                                 " Please check that \"" + self.local_vid_path + "\" exists.")

        elif self.task_type == TRANSFER_TASK:
            if os.path.isdir(self.local_vid_path):
                if os.path.isdir(self.local_csv_path):
                    if not os.path.isdir(self.csv_transfer_path):
                        os.makedirs(self.csv_transfer_path)
                        self.logger.info("CSV transfer folder does not exist. Making directory.")

                    seq_csv_pairs = self.get_seq_csv_pairs(self.local_vid_path, self.local_csv_path)

                    self.logger.info("Attempting to transfer files. This will take some time.")
                    start_time = time.clock()

                    for seq_path, csv_path in seq_csv_pairs:

                        seq_mod_date = datetime.datetime.fromtimestamp(os.path.getmtime(seq_path))
                        seq_folder_string = str(seq_mod_date.month) + "-" + str(seq_mod_date.day) + "-" + \
                            str(seq_mod_date.year)

                        seq_full_folder_path = self.vid_transfer_path + "\\" + seq_folder_string

                        if not os.path.isdir(seq_full_folder_path):
                            os.makedirs(seq_full_folder_path)
                            self.logger.info("Making seq date directory: " + seq_full_folder_path)

                        self.logger.info("Transferring seq file \"" + seq_path + "\" to \"" + seq_full_folder_path +
                                         "\".")
                        shutil.copy(seq_path, seq_full_folder_path)

                        self.logger.info("Transferring CSV file \"" + csv_path + "\" to \"" + self.csv_transfer_path +
                                         "\".")
                        shutil.copy(csv_path, self.csv_transfer_path)

                    stop_time = time.clock()
                    diff_time_str = str((stop_time-start_time)/60.0)
                    self.logger.info("Transferring completed in " + diff_time_str + " minutes.")

                    # TODO: Implement checking that files transfered
                    # TODO: Delete local files that have been transfered
                    # TODO: Delete transferred video files older than a certain age that have a csv on the server

                else:
                    self.logger.info("Attempted to transfer files, but local csv path does not exist. Please check " +
                                     "directory.")
            else:
                self.logger.info("Attempted to transfer files, but local video path does not exist. Please check " +
                                 "directory.")
        self.task_done.emit()

    def get_seq_csv_pairs(self, local_seq, local_csv):
        csv_list = []
        seq_csv_pairs = []

        for file_or_folder in os.listdir(local_csv):
            full_path = os.path.join(local_csv, file_or_folder).replace('/', "\\")
            try:
                if os.path.isfile(full_path):
                    csv_list.append([file_or_folder[:-4], full_path])
            except:
                    self.logger.info("Local video directory exists, but cannot be accessed.\nPlease check permissions.")

        for file_or_folder in os.listdir(local_seq):
            full_path = os.path.join(local_seq, file_or_folder).replace('/', "\\")
            try:
                if os.path.isfile(full_path):
                    for csv_name, csv_path in csv_list:
                        if csv_name == file_or_folder[:-4]:
                            seq_csv_pairs.append([full_path, csv_path])
            except:
                    self.logger.info("Local video directory exists, but cannot be accessed.\nPlease check permissions.")

        return seq_csv_pairs


    def file_count(self, path):
        count = 0
        for file_or_folder in os.listdir(path):
                full_path = os.path.join(path, file_or_folder)
                try:
                    if os.path.isfile(full_path):
                        count += 1
                except:
                    self.logger.info("Local video directory exists, but cannot be accessed.\nPlease check permissions.")
        return count

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

        # ########## Get the instances of the loggers ##########
        self.logger = logging.getLogger("PRAT Auto Processor")

        # ########## Thread flags ##########
        self.not_abort_flag = True

        # ########## Class Variables ##########
        self.processing_thread = None
        self.transfer_thread = None

        self.processing_done = False
        self.transfer_done = False

        # ########## Make signal/slot connections ##########
        self.connect_signals_to_slots()

        # ########## Start timer ##########
        self.start()

    def connect_signals_to_slots(self):
        pass

    def run(self):
        while self.not_abort_flag:
            self.check_for_midnight_and_reset()
            self.check_schedules_and_process()
            self.msleep(100)

        if self.processing_thread:
            self.processing_thread.wait()

        if self.transfer_thread:
            self.transfer_thread.wait()

    def check_for_midnight_and_reset(self):
        current_time = QtCore.QTime.currentTime()

        process_reset = self.settings.value("do_process_reset", 0).toInt()[0]
        transfer_reset = self.settings.value("do_transfer_reset", 0).toInt()[0]

        if current_time.toString("h:mm:ss AP") == midnight_qtime_string:
            self.processing_done = False
            self.transfer_done = False
            self.logger.info("Processing and file transfers have been reset for next day use.")
            self.msleep(1000)
        elif process_reset:
            self.processing_done = False
            self.settings.setValue("do_process_reset", int(False))
        elif transfer_reset:
            self.transfer_done = False
            self.settings.setValue("do_transfer_reset", int(False))

    def check_schedules_and_process(self):
        current_time = QtCore.QTime.currentTime()

        enabled = self.settings.value("enabled", 0).toInt()[0]

        if enabled:
            process_time = QtCore.QTime.fromString(self.settings.value("csv_time").toString(), "h:mm AP")
            transfer_time = QtCore.QTime.fromString(self.settings.value("transfer_time").toString(), "h:mm AP")

            if (process_time.hour() == current_time.hour()) and (process_time.minute() == current_time.minute()):
                if not self.processing_thread and not self.processing_done:
                    local_vid = self.settings.value("local_video_path").toString()
                    local_csv = self.settings.value("local_csv_path").toString()

                    self.processing_thread = QueueProcessor(self, PROCESS_TASK, local_vid, local_csv, "", "", 0)

            if (transfer_time.hour() == current_time.hour()) and (transfer_time.minute() == current_time.minute()):
                if not self.transfer_thread and not self.transfer_done:
                    local_vid = self.settings.value("local_video_path").toString()
                    local_csv = self.settings.value("local_csv_path").toString()
                    transfer_vid = self.settings.value("video_transfer_path").toString()
                    transfer_csv = self.settings.value("csv_transfer_path").toString()
                    age = self.settings.value("cleanup_age").toInt()[0]

                    self.transfer_thread = QueueProcessor(self, TRANSFER_TASK, local_vid, local_csv, transfer_vid,
                                                          transfer_csv, age)

    def on_processing_done_slot(self):
        self.processing_done = True
        self.processing_thread = None

    def on_transfer_done_slot(self):
        self.transfer_done = True
        self.transfer_thread = None

    def on_kill_threads_slot(self):
        self.not_abort_flag = False