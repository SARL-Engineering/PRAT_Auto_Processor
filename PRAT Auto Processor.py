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
import sys
from PyQt4 import QtCore, QtGui, uic
import signal

# Custom imports
from Framework.LoggerCore import Logger
from Framework.SettingsCore import Settings
from Interface.StatusLoggerCore import StatusLoggerTab
from Interface.SystemSettingsCore import SettingsTab

from Framework.ScheduleHandlerCore import ScheduleHandler

#####################################
# Global Variables
#####################################
form_class = uic.loadUiType("Interface/PRAT Auto Processor.ui")[0]  # Load the UI


#####################################
# ProgramWindow Class Definition
#####################################
class ProgramWindow(QtGui.QMainWindow, form_class):

    kill_all_threads = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)

        # ########## Set up QT Application Window ##########
        self.setupUi(self)  # Has to be first call in class in order to link gui form objects

        # ########## Create the system logger and get an instance of it ##########
        self.logger_core = Logger(self)

        # ########## Setup and get program settings ##########
        self.settings = Settings(self)

        # ########## Instantiations of tab classes ##########
        self.log_viewer_tab = StatusLoggerTab(self)
        self.settings_tab = SettingsTab(self)

        # ########## Instantiations of the scheduler class ##########
        self.scheduler = ScheduleHandler(self)

        # ########## Creation of the system tray icon ##########
        self.tray_icon = None
        self.tray_menu = None
        self.setup_tray_icon()

        # ########## Setup application taskbar icon ##########
        self.setup_taskbar_icon()

        # ########## Setup of gui elements ##########
        self.main_tab_widget.setCurrentIndex(0)

        # ########## Class variables ##########
        self.threads_to_wait_for = []
        self.threads_to_wait_for.append(self.log_viewer_tab)
        self.threads_to_wait_for.append(self.scheduler)

        # ########## Setup signal and slot connections ##########
        self.connect_signals_to_slots()

        # ########## Show startup messagebox ##########
        # self.tray_icon.showMessage

    def connect_signals_to_slots(self):
        self.main_tab_widget.currentChanged.connect(self.on_main_tab_widget_tab_changed)
        self.kill_all_threads.connect(self.log_viewer_tab.on_kill_threads_slot)
        self.kill_all_threads.connect(self.scheduler.on_kill_threads_slot)

    def setup_tray_icon(self):
        self.tray_icon = QtGui.QSystemTrayIcon(QtGui.QIcon("Resources/app_icon.png"))
        self.tray_icon.activated.connect(self.on_tray_exit_triggered_slot)

        self.tray_menu = QtGui.QMenu()
        self.tray_menu.addAction("Show")
        self.tray_menu.addAction("Exit")

        self.tray_menu.triggered.connect(self.on_tray_exit_triggered_slot)
        self.tray_icon.setContextMenu(self.tray_menu)

        self.tray_icon.show()
        self.tray_icon.showMessage("PRAT Auto Processor", "Application started.\nCritical messages will be shown " +
                                                          "here.", QtGui.QSystemTrayIcon.Information, 5000)

    def setup_taskbar_icon(self):
        app_icon = QtGui.QIcon()
        app_icon.addFile("Resources/app_icon.png", QtCore.QSize(16, 16))
        app_icon.addFile("Resources/app_icon.png", QtCore.QSize(24, 24))
        app_icon.addFile("Resources/app_icon.png", QtCore.QSize(32, 32))
        app_icon.addFile("Resources/app_icon.png", QtCore.QSize(48, 48))
        app_icon.addFile("Resources/app_icon.png", QtCore.QSize(256, 256))
        self.setWindowIcon(app_icon)

    def closeEvent(self, event):
        if self.isHidden():
            self.kill_all_threads.emit()
            self.wait_for_all_threads()
            event.accept()
        else:
            message = "Are you sure you want to exit? Press NO to hide instead."
            reply = QtGui.QMessageBox.question(self, "Exit Dialog", message, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

            if reply == QtGui.QMessageBox.Yes:
                self.kill_all_threads.emit()
                self.wait_for_all_threads()
                event.accept()
            else:
                self.hide()
                event.ignore()

    def on_tray_exit_triggered_slot(self, event):
        if event == 1:
            pass
        elif (event == 2) or (event == 3):
            self.show()
        elif event.text() == "Exit":
            self.close()
        elif event.text() == "Show":
            self.show()

    def on_main_tab_widget_tab_changed(self, index):
        if index == 0:
            self.resize(850, 700)
        elif index == 1:
            self.resize(575, 315)

    def on_tray_icon_messagebox_needed_slot(self, title, message, priority, duration):
        self.tray_icon.showMessage(title, message, priority, 1000*duration)

    def wait_for_all_threads(self):
        for thread in self.threads_to_wait_for:
            thread.wait()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # This allows the keyboard interrupt kill to work  properly

    app = QtGui.QApplication(sys.argv)  # Create the base qt gui application

    myWindow = ProgramWindow()  # Make a window in this application using the pnp MyWindowClass
    myWindow.setWindowTitle("PRAT Auto Processor")
    myWindow.setWindowFlags(myWindow.windowFlags() & ~QtCore.Qt.WindowMinimizeButtonHint)
    myWindow.setWindowFlags(myWindow.windowFlags() & ~QtCore.Qt.WindowMaximizeButtonHint)
    myWindow.resize(850, 700)
    myWindow.show()  # Show the window in the application

    app.exec_()  # Execute launching of the application

    del myWindow
    del app