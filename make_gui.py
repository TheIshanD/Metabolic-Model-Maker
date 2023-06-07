"""Create the GUI which will be able to start up the KGML visualizer"""
import os
import sys

from PySide6.QtWidgets import (QFileDialog,
                               QLabel,
                               QLineEdit,
                               QPushButton,
                               QVBoxLayout,
                               QWidget,
                               QApplication)

from create_visual import display_kgml


class MyWidget(QWidget):
    """Define a main GUI"""

    def __init__(self):
        super().__init__()

        # Create GUI variables and state
        self.kgml_file_name = ""
        self.old_kgml_file_name = ""
        self.model_file_name = ""
        self.setWindowTitle("KGML Model Creator GUI")

        # Set up GUI Components
        self.kgml_path_text = QLabel("KGML Path: --")
        self.model_path_text = QLabel("Model Path: --")
        self.model_file_text = QLabel("Generated Model File Name (if generating):")
        self.model_file_edit = QLineEdit("example-model-file-name")
        self.choose_kgml_file_button = QPushButton("Choose KGML File (Required)")
        self.choose_model_file_button = QPushButton("Choose Model File (Optional)")
        self.toggle_generate_model_button = QPushButton("Toggle Model Generation: currently off")
        self.run_button = QPushButton("Run Simulation")

        # Set Initial State of GUI Components
        self.toggle_generate_model_button.setCheckable(True)
        self.toggle_generate_model_button.setStyleSheet("background-color : lightgrey")
        self.choose_kgml_file_button.setStyleSheet("background-color : rgb(255,105,97)")
        self.choose_model_file_button.setStyleSheet("background-color : lightgrey")

        # Add GUI Components to the full GUI
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.kgml_path_text)
        self.layout.addWidget(self.model_path_text)
        self.layout.addWidget(self.model_file_text)
        self.layout.addWidget(self.model_file_edit)
        self.layout.addWidget(self.choose_kgml_file_button)
        self.layout.addWidget(self.choose_model_file_button)
        self.layout.addWidget(self.toggle_generate_model_button)
        self.layout.addWidget(self.run_button)

        # Make GUI components clickable and assign them to callback functions
        self.choose_kgml_file_button.clicked.connect(self.choose_kgml_file)
        self.choose_model_file_button.clicked.connect(self.choose_model_file)
        self.toggle_generate_model_button.clicked.connect(self.change_gen_model_button_color)
        self.run_button.clicked.connect(self.run_display)

    def change_gen_model_button_color(self):
        """Change the generate model button color to represent a toggle"""
        if self.toggle_generate_model_button.isChecked():
            # Turn the button to an "ON" state
            self.toggle_generate_model_button.setStyleSheet("background-color : lightgreen")
            self.toggle_generate_model_button.setText("Toggle Model Generation (currently on)")
        else:
            # Turn the button to an "OFF" state
            self.toggle_generate_model_button.setStyleSheet("background-color : lightgrey")
            self.toggle_generate_model_button.setText("Toggle Model Generation (currently off)")

    def run_display(self):
        """Run the visualizer based on data from the GUI for arguments"""
        if self.kgml_file_name != "":
            #  Define file location to save the model in and determine if application is a script file or frozen exe
            application_path = ""
            if getattr(sys, 'frozen', False):
                application_path = os.path.dirname(sys.executable)
            elif __file__:
                application_path = os.path.dirname(__file__)
            generated_model_file_name = os.path.join(application_path, "models/" + self.model_file_edit.text() + ".txt")
            generated_model_file_name = generated_model_file_name.replace(" ", "-")

            # Display the file
            display_kgml(self.kgml_file_name,
                         self.model_file_name,
                         self.toggle_generate_model_button.isChecked(),
                         generated_model_file_name)

    def choose_kgml_file(self):
        """Opens a file dialog to be able to choose the base kgml file"""
        #  Determine if application is a script file or frozen exe
        application_path = os.getcwd()
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        elif __file__:
            application_path = os.path.dirname(__file__)
        # Open a file dialog to select a KGML file
        self.kgml_file_name, _ = QFileDialog.getOpenFileName(self,
                                                             "Open a KGML XML File",
                                                             application_path + "/kgml_files",
                                                             "XML Files (*.xml)")
        if self.kgml_file_name == "":
            # If dialog is canceled, don't change the current value
            self.kgml_file_name = self.old_kgml_file_name
        else:
            # Change the KGML file to the selected value
            self.old_kgml_file_name = self.kgml_file_name
            self.choose_kgml_file_button.setStyleSheet("background-color : lightgreen")
        self.kgml_path_text.setText("KGML Path: --" + self.kgml_file_name)

    def choose_model_file(self):
        """Opens a file dialog to be able to choose a model file"""
        if self.model_file_name == "":
            #  Determine if application is a script file or frozen exe
            application_path = os.getcwd()
            if getattr(sys, 'frozen', False):
                application_path = os.path.dirname(sys.executable)
            elif __file__:
                application_path = os.path.dirname(__file__)
            # If you don't have a current model file, open file dialog to choose one
            self.model_file_name, _ = QFileDialog.getOpenFileName(self,
                                                                  "Open a Network Model File",
                                                                  application_path + "/models",
                                                                  "TXT Files (*.txt)")
            if self.model_file_name != "":
                # If a file is selected, change the button to indicate that a model is chosen
                self.choose_model_file_button.setStyleSheet("background-color : lightgreen")
        else:
            # If a current model file exists, clear the current model file
            self.model_file_name = ""
            self.choose_model_file_button.setStyleSheet("background-color : lightgrey")
        self.model_path_text.setText("Model Path: --" + self.model_file_name)


# Run the app
if __name__ == "__main__":
    app = QApplication([])

    widget = MyWidget()
    widget.resize(700, 200)
    widget.show()

    sys.exit(app.exec())
