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
from PyQt4 import QtCore, QtGui
import os
import psutil
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

INFORMATION = QtGui.QSystemTrayIcon.Information
CRITICAL = QtGui.QSystemTrayIcon.Critical


#####################################
# QueueProcessor Class Definition
#####################################
class QueueProcessor(QtCore.QThread):

    task_done = QtCore.pyqtSignal()
    show_messagebox = QtCore.pyqtSignal(str, str, int, int)

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

        # ########## Connect messagebox signal to main gui slot ##########
        self.show_messagebox.connect(self.master.main_window.on_tray_icon_messagebox_needed_slot)

        # ########## Start worker thread ##########
        self.start()

    def run(self):
        if self.task_type == PROCESS_TASK:
            self.logger.info("##### PROCESSING TASK RUNNING #####")
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
                    matlab_engine.quit()
                    del matlab_engine

                    stop_time = time.clock()

                    diff_time_str = str((stop_time-start_time)/60.0)

                    self.logger.info("Processing completed in " + diff_time_str + " minutes.")

                    new_out_csv_count = self.file_count(self.local_csv_path)
                    csv_diff = new_out_csv_count - original_out_csv_count

                    if csv_diff == count:
                        self.logger.info("All SEQ files processed successfully!\n")
                    else:
                        self.logger.info("SEQ files not processed successfully!" +
                                         " Processed " + str(count) + " SEQ files, but only " + str(csv_diff) +
                                         " CSV files were created. Please check your SEQ files!\n")
                else:
                    self.logger.info("Attempted to process SEQ files, but none exist.")

            else:
                self.logger.info("Local video path does not exist! Processing failed!" +
                                 " Please check that \"" + self.local_vid_path + "\" exists.")
                self.show_messagebox.emit("Processing", "Processing failed!\nPlease check logs!",
                                          CRITICAL, 60)

        elif self.task_type == TRANSFER_TASK:
            self.kill_process_if_running("Streampix5-single.exe")
            self.logger.info("##### TRANSFER TASK RUNNING #####")
            if os.path.isdir(self.local_vid_path):
                if os.path.isdir(self.local_csv_path):
                    if not os.path.isdir(self.csv_transfer_path):
                        os.makedirs(self.csv_transfer_path)
                        self.logger.info("CSV transfer folder does not exist. Making directory.")

                    self.do_file_transfers()
                    self.cleanup_old_seq_files()

                else:
                    self.logger.info("Attempted to transfer files, but local csv path does not exist. Please check " +
                                     "directory.")
                    self.show_messagebox.emit("File Transfer", "File transfer failed!\nPlease check logs!",
                                              CRITICAL, 60)
            else:
                self.logger.info("Attempted to transfer files, but local video path does not exist. Please check " +
                                 "directory.")
                self.show_messagebox.emit("File Transfer", "File transfer failed!\nPlease check logs!",
                                          CRITICAL, 60)
        self.task_done.emit()

    def do_file_transfers(self):
        seq_csv_pairs = self.get_seq_csv_pairs(self.local_vid_path, self.local_csv_path)

        if seq_csv_pairs:

            self.logger.info("Attempting to transfer files. This will take some time.")
            start_time = time.clock()

            for seq_path, csv_path in seq_csv_pairs:

                seq_mod_date = datetime.datetime.fromtimestamp(os.path.getmtime(seq_path))
                seq_folder_string = str(seq_mod_date.month) + "-" + str(seq_mod_date.day) + "-" + \
                    str(seq_mod_date.year)

                seq_full_folder_path = self.vid_transfer_path + "\\" + seq_folder_string
                seq_full_transfer_path = seq_full_folder_path + "\\" + seq_path.split("\\")[-1]

                csv_full_transfer_path = self.csv_transfer_path + "\\" + csv_path.split("\\")[-1]

                if not os.path.isdir(seq_full_folder_path):
                    os.makedirs(seq_full_folder_path)

                self.logger.info("Transferring SEQ file \"" + seq_path + "\" to \"" + seq_full_transfer_path +
                                 "\".")
                if os.path.isfile(seq_full_transfer_path):
                    try:
                        os.unlink(seq_full_transfer_path)
                        shutil.copy(seq_path, seq_full_transfer_path)
                    except:
                        self.logger.info("Insufficient Permissions! Could not transfer to \"" + seq_full_transfer_path + "\"!")
                else:
                    shutil.copy(seq_path, seq_full_transfer_path)

                self.logger.info("Transferring CSV file \"" + csv_path + "\" to \"" + csv_full_transfer_path +
                                 "\".")
                if os.path.isfile(csv_full_transfer_path):
                    try:
                        os.unlink(csv_full_transfer_path)
                        shutil.copy(csv_path, csv_full_transfer_path)
                    except:
                        self.logger.info("Insufficient Permissions! Could not transfer to \"" + seq_full_transfer_path + "\"!")
                else:
                    shutil.copy(csv_path, csv_full_transfer_path)

                if os.path.isfile(seq_full_transfer_path) and os.path.isfile(csv_full_transfer_path):
                    try:
                        os.unlink(seq_path)
                        self.logger.info("Deleted SEQ file \"" + seq_path + "\"")
                    except:
                        self.logger.info("Failed to delete SEQ file \"" + seq_path + "\"!!!!!")

                    try:
                        os.unlink(csv_path)
                        self.logger.info("Deleted CSV file \"" + csv_path + "\".\n")
                    except:
                        self.logger.info("Failed to delete CSV file \"" + csv_path + "\"!!!!!")

                elif not os.path.isfile(seq_full_transfer_path):
                    self.logger.log("\"" + seq_full_transfer_path + "\" does not exist. File transfer failed! SEQ and "
                                    + "CSV will not be deleted. Please check permissions.")
                    self.show_messagebox.emit("File Transfer", "File transfer failed!\nPlease check logs!",
                                              CRITICAL, 60)
                elif not os.path.isfile(csv_full_transfer_path):
                    self.logger.log("\"" + csv_full_transfer_path + "\" does not exist. File transfer failed! SEQ and "
                                    + "CSV will not be deleted. Please check permissions.")
                    self.show_messagebox.emit("File Transfer", "File transfer failed!\nPlease check logs!",
                                              CRITICAL, 60)

            stop_time = time.clock()
            diff_time_str = str((stop_time-start_time)/60.0)
            self.logger.info("Transferring completed in " + diff_time_str + " minutes.\n")
        else:
            self.logger.info("No files to transfer.\n")

    def cleanup_old_seq_files(self):
        seq_names_paths_and_age = []
        csv_names_paths = []

        for root, dirs, files in os.walk(self.vid_transfer_path):
            for name in files:
                full_path = os.path.join(root, name)
                age = os.path.getmtime(full_path)
                seq_names_paths_and_age.append([name[:-4], full_path, age])

        for root, dirs, files in os.walk(self.csv_transfer_path):
            for name in files:
                full_path = os.path.join(root, name)
                csv_names_paths.append([name[:-4], full_path])

        for seq_name, seq_full_path, seq_age in seq_names_paths_and_age:
            if seq_age < (time.time() - (86400 * self.cleanup_age)):
                for csv_name, csv_path in csv_names_paths:
                    if seq_name == csv_name:
                        self.logger.info("Deleting \"" + seq_full_path + "\". SEQ is older than " +
                                         str(self.cleanup_age) + " days and has corresponding CSV.")
                        os.unlink(seq_full_path)
                        self.delete_folder_if_empty("\\".join(seq_full_path.split("\\")[:-1]))

    def delete_folder_if_empty(self, path_to_folder):
        for root, dirs, files in os.walk(path_to_folder):
            if not files:
                self.logger.info("Deleting empty folder \"" + path_to_folder + "\".")
                os.rmdir(path_to_folder)

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

    @staticmethod
    def kill_process_if_running(process_name):
        pid_list = psutil.get_pid_list()
        for pid in pid_list:
            try:
                process = psutil.Process(pid)
                name = str(process.name())
                if name == process_name:
                    process.terminate()
                    process.wait(timeout=3)
            except:
                pass

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
            while self.processing_thread or self.transfer_thread:
                self.msleep(1000)

            self.processing_done = False
            self.transfer_done = False
            self.logger.info("#####Processing and file transfers have been reset for next day use.#####")
            self.msleep(1000)

        elif process_reset:
            while self.processing_thread:
                self.msleep(1000)
            self.processing_done = False
            self.settings.setValue("do_process_reset", int(False))

        elif transfer_reset:
            while self.transfer_thread:
                self.msleep(1000)
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
