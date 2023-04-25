"""
WORKS !!
"""
import sys
import os
import traceback

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal

from audio import Audio


class WorkerSignals(QtCore.QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        `tuple` (exctype, value, traceback.format_exc() )

    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class Worker(QtCore.QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle("Recorder")

        self.home_folder = os.path.dirname(os.path.realpath(__file__))
        # if sys.platform.startswith("win"):
        #     self.home_folder = "C:\\"
        # else:
        #     self.home_folder = "./"

        self.file_name = "output_test"
        self.path_to_file = os.path.join(self.home_folder, self.file_name + ".mp3")

        self.file_found_text = "<font color='red'>File already exists.</font>"

        self.recording = False

        self.audio = Audio(self)

        self.central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.vertical_layout = QtWidgets.QVBoxLayout()

        self.group_box = QtWidgets.QGroupBox()
        layout = QtWidgets.QGridLayout()

        self.label_home_folder = QtWidgets.QLabel(self.home_folder)
        self.line_edit_file_name = QtWidgets.QLineEdit(self.file_name)
        self.line_edit_file_name.setEnabled(True)
        self.file_found_label = QtWidgets.QLabel("")
        self.check_file_existence()

        layout.addWidget(QtWidgets.QLabel("Folder"), 0, 0)
        layout.addWidget(self.label_home_folder, 0, 1)
        layout.addWidget(QtWidgets.QLabel("File name:"), 1, 0)
        layout.addWidget(self.line_edit_file_name, 1, 1)
        layout.addWidget(QtWidgets.QLabel(".mp3"), 1, 2)
        layout.addWidget(self.file_found_label, 1, 3)
        self.group_box.setLayout(layout)
        self.line_edit_file_name.textChanged.connect(self.line_edit_text_change)

        self.hbox_buttons = QtWidgets.QHBoxLayout()

        self.button_record = QtWidgets.QPushButton("Record")
        self.hbox_buttons.addWidget(self.button_record)
        self.button_record.clicked.connect(self.record)
        self.button_record.setStyleSheet("background-color: red")

        self.button_stop = QtWidgets.QPushButton("Stop")
        self.hbox_buttons.addWidget(self.button_stop)
        self.button_stop.clicked.connect(self.stop)
        self.button_stop.setDisabled(True)

        self.vertical_layout.addWidget(self.group_box)
        self.vertical_layout.addLayout(self.hbox_buttons)

        self.central_widget.setLayout(self.vertical_layout)

        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")

        # Add actions to file menu
        home_folder_action = QtWidgets.QAction("Set home folder", self)
        close_action = QtWidgets.QAction("Close App", self)
        file_menu.addAction(home_folder_action)
        file_menu.addAction(close_action)
        #
        close_action.triggered.connect(self.closeEvent)
        home_folder_action.triggered.connect(self.set_folder)
        # settings_folder_action.triggered.connect(self.set_settings_folder)

        self.show()

        self.threadpool = QtCore.QThreadPool()
        # print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        # QtWidgets.QMessageBox.about(self,
        #                             "Reminder",
        #                             "Remember to deactivate your microphone.")
        #                             # QtWidgets.QMessageBox.Ok)

    def execute_recorder(self, progress_callback):
        self.audio.record_to_file()

    # def thread_complete(self):
    #     print("THREAD COMPLETE!")

    def record(self):
        # Pass the function to execute
        worker = Worker(self.execute_recorder)  # Any other args, kwargs are passed to the run function
        # worker.signals.result.connect(self.print_output)
        # worker.signals.finished.connect(self.thread_complete)
        # worker.signals.progress.connect(self.progress_fn)

        # Execute
        self.threadpool.start(worker)
        self.button_record.setDisabled(True)
        self.button_stop.setEnabled(True)

    def stop(self, event):
        self.recording = False
        self.button_stop.setDisabled(True)
        self.button_record.setEnabled(True)

    def closeEvent(self, event):
        self.close()

    def set_folder(self):
        dialog_txt = "Choose Media Folder"
        folder_name = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                 dialog_txt,
                                                                 os.path.expanduser(self.home_folder))
        self.home_folder = folder_name
        self.path_to_file = os.path.join(self.home_folder, self.file_name + '.mp3')
        self.label_home_folder.setText(self.home_folder)
        self.check_file_existence()

    def line_edit_text_change(self, event):
        text = self.line_edit_file_name.text()
        self.file_name = text
        self.path_to_file = os.path.join(self.home_folder, text + ".mp3")
        self.check_file_existence()

    def check_file_existence(self):
        path = os.path.join(self.home_folder, self.file_name + '.mp3')
        if os.path.isfile(path):
            self.file_found_label.setText(self.file_found_text)
        else:
            self.file_found_label.setText("")


app = QtWidgets.QApplication([])
window = MainWindow()
app.exec_()
