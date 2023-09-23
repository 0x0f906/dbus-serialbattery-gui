import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QMessageBox, QDialogButtonBox, QScrollArea, QDialog
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QDesktopServices

# Import Paramiko for SSH/SCP functionality
import paramiko

class ConfigEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("dbus-serialbattery-gui")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(20, 20, 20, 20)  # Set some margin around the layout

        self.scroll_area = None
        self.scroll_content = None
        self.scroll_layout = None
        self.config_data = {}
        self.config_file_path = None
        self.config_file_lines = None
        self.config_loaded = False
        self.config_modified = False  # To track if the config has been modified

        # Load SSH settings from ssh_config.txt when the program starts
        self.load_ssh_settings()

        self.init_ui()

    def load_ssh_settings(self):
        # Load SSH settings from ssh_config.txt if it exists
        ssh_config_dir = os.path.join(os.path.expanduser("~"), ".dbus-serialbattery-gui")
        os.makedirs(ssh_config_dir, exist_ok=True)
        ssh_config_path = os.path.join(ssh_config_dir, "ssh_config.txt")
        if os.path.exists(ssh_config_path):
            with open(ssh_config_path, "r") as ssh_config_file:
                lines = ssh_config_file.readlines()
                ssh_settings = {}
                for line in lines:
                    key, value = line.strip().split('=')
                    ssh_settings[key] = value
                self.ssh_settings = ssh_settings
        else:
            self.ssh_settings = {}

    def init_ui(self):
        self.scroll_area = self.create_scroll_area()
        self.layout.addWidget(self.scroll_area)

        button_layout = QHBoxLayout()  # Create a horizontal layout for buttons
        self.load_button = QPushButton("Load Local Config", self)
        self.load_button.clicked.connect(self.load_config_file)
        button_layout.addWidget(self.load_button)

        # Pull Remote Config button
        self.pull_remote_button = QPushButton("Pull Remote Config", self)
        self.pull_remote_button.clicked.connect(self.pull_remote_config)
        button_layout.addWidget(self.pull_remote_button)

        # Push Local Config button
        self.push_local_button = QPushButton("Push Config to Remote", self)
        self.push_local_button.clicked.connect(self.push_local_config)
        button_layout.addWidget(self.push_local_button)

        self.save_button = QPushButton("Save Config", self)
        self.save_button.clicked.connect(self.save_config_file)
        button_layout.addWidget(self.save_button)

        # SSH Config button
        self.ssh_config_button = QPushButton("SSH Config", self)
        self.ssh_config_button.clicked.connect(self.configure_ssh)
        button_layout.addWidget(self.ssh_config_button)

        # Apply config button
        self.apply_config_button = QPushButton("Apply Remote Config", self)
        self.apply_config_button.clicked.connect(self.apply_config)
        button_layout.addWidget(self.apply_config_button)

        self.close_button = QPushButton("Close", self)
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)

        self.layout.addLayout(button_layout)  # Add the button layout to the main layout

    def create_scroll_area(self):
        scroll_area = QScrollArea(self.central_widget)
        scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget(scroll_area)
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)  # Set the margin to zero
        scroll_area.setWidget(self.scroll_content)
        return scroll_area

    def load_config_file(self):
        if self.config_loaded:
            reply = QMessageBox.question(self, 'Save Changes', 'Do you want to save changes before loading a new file?',
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.save_config_file()
            elif reply == QMessageBox.Cancel:
                return

            self.clear_config_editor()

        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly

        file_path, _ = QFileDialog.getOpenFileName(self, "Open Config File", "", "INI Files (*.ini);;All Files (*)", options=options)

        if file_path:
            self.config_file_path = file_path
            self.populate_edit_boxes()
            self.config_loaded = True

    def clear_config_editor(self):
        # Clear the previous config data
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.scroll_layout.update()

    def populate_edit_boxes(self):
        self.config_data = {}
        if self.config_file_path:
            with open(self.config_file_path, 'r') as config_file:
                self.config_file_lines = config_file.readlines()
                current_section = None
                for line in self.config_file_lines:
                    line = line.strip()
                    if line.startswith(';'):
                        section_name = line.lstrip(';').strip()
                        current_section = QLabel(f"<b>{section_name}</b>")
                        current_section.setFont(QFont('Arial', 12, QFont.Bold))
                        self.scroll_layout.addWidget(current_section)
                    elif current_section is not None:
                        parts = line.split('=')
                        if len(parts) == 2:
                            variable_name = parts[0].strip()
                            value = parts[1].strip()
                            label = QLabel(f"{variable_name} = ")
                            edit = QLineEdit(value)
                            edit.textChanged.connect(self.mark_config_modified)
                            self.config_data[variable_name] = edit
                            self.scroll_layout.addWidget(label)
                            self.scroll_layout.addWidget(edit)

    def mark_config_modified(self):
        self.config_modified = True

    def save_config_file(self):
      if not self.config_modified:
        QMessageBox.information(self, "No Changes", "No changes have been made to the configuration.")
        return

      if self.config_file_path:
        updated_config_data = []
        for line in self.config_file_lines:
            variable_name = line.split('=')[0].strip()
            if variable_name in self.config_data:
                line = f'{variable_name} = {self.config_data[variable_name].text()}\n'
            updated_config_data.append(line)

        try:
            with open(self.config_file_path, 'w') as config_file:
                config_file.writelines(updated_config_data)

            self.config_modified = False
            QMessageBox.information(self, "Success", "Config file saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save config file: {str(e)}")



    def open_documentation(self):
        QDesktopServices.openUrl(QUrl("https://github.com/Louisvdw/dbus-serialbattery"))

    def configure_ssh(self):
        # Create an SSH configuration dialog
        dialog = SSHConfigDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # Save the SSH settings here
            self.ssh_settings = {
                "username": dialog.username_field.text(),
                "password": dialog.password_field.text(),
                "hostname": dialog.hostname_field.text(),
                "remote_config_path": dialog.remote_config_field.text()
            }
            
            # Save SSH settings to ssh_config.txt
            ssh_config_dir = os.path.join(os.path.expanduser("~"), ".dbus-serialbattery-gui")
            os.makedirs(ssh_config_dir, exist_ok=True)
            ssh_config_path = os.path.join(ssh_config_dir, "ssh_config.txt")
            with open(ssh_config_path, "w") as ssh_config_file:
                ssh_config_file.write(f"username={self.ssh_settings['username']}\n")
                ssh_config_file.write(f"password={self.ssh_settings['password']}\n")
                ssh_config_file.write(f"hostname={self.ssh_settings['hostname']}\n")
                ssh_config_file.write(f"remote_config_path={self.ssh_settings['remote_config_path']}\n")

            QMessageBox.information(self, "Success", "SSH settings saved successfully.")

    def pull_remote_config(self):
        # Ensure SSH settings are configured
        if not hasattr(self, 'ssh_settings'):
            QMessageBox.critical(self, "Error", "SSH settings are not configured. Please use SSH Config to set them up.")
            return

        # Connect and pull the remote config
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.load_system_host_keys()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(
                self.ssh_settings['hostname'],
                username=self.ssh_settings['username'],
                password=self.ssh_settings['password']
            )
            
            # Open an SFTP session
            sftp = ssh_client.open_sftp()

            # Define the remote config file path
            remote_config_path = self.ssh_settings['remote_config_path']

            # Define a local path to save the remote config
            local_config_path = os.path.join(os.path.expanduser("~"), ".dbus-serialbattery-gui", "config.ini")

            # Ensure the local directory exists
            os.makedirs(os.path.dirname(local_config_path), exist_ok=True)

            # Download the remote config file
            sftp.get(remote_config_path, local_config_path)

            # Close the SFTP session and SSH connection
            sftp.close()
            ssh_client.close()

            # Clear existing config data
            self.clear_config_editor()

            # Load the downloaded config file
            self.config_file_path = local_config_path
            self.populate_edit_boxes()
            self.config_loaded = True

            QMessageBox.information(self, "Success", f"Remote config downloaded and loaded successfully from {remote_config_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to download remote config: {str(e)}")

    def push_local_config(self):
        # Ensure SSH settings are configured
        if not hasattr(self, 'ssh_settings'):
            QMessageBox.critical(self, "Error", "SSH settings are not configured. Please use SSH Config to set them up.")
            return

        # Get the local config file path
        local_config_path = self.config_file_path

        # Ensure the local config file exists
        if not local_config_path or not os.path.isfile(local_config_path):
            QMessageBox.critical(self, "Error", "Local config file is missing or invalid.")
            return

        # Check if the local config has been modified and not saved
        if self.config_modified:
            reply = QMessageBox.question(self, 'Save Changes', 'The local config has been modified but not saved. Save changes before pushing?',
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.save_config_file()
            else:
                return
            
        # Confirmation dialog before pushing
        reply = QMessageBox.question(self, 'Confirmation', 'This will overwrite your existing dbus-serialbattery config. Are you sure?',
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Connect and push the local config to the remote location
            try:
                ssh_client = paramiko.SSHClient()
                ssh_client.load_system_host_keys()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(
                    self.ssh_settings['hostname'],
                    username=self.ssh_settings['username'],
                    password=self.ssh_settings['password']
                )

                # Open an SFTP session
                sftp = ssh_client.open_sftp()

                # Define the remote config file path
                remote_config_path = self.ssh_settings['remote_config_path']

                # Upload the local config file to the remote location, overwriting the existing file
                sftp.put(local_config_path, remote_config_path)

                # Close the SFTP session and SSH connection
                sftp.close()
                ssh_client.close()

                QMessageBox.information(self, "Success", f"Local config pushed to remote location at {remote_config_path}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to push local config to remote location: {str(e)}")

    def apply_config(self):
        # Ensure SSH settings are configured
        if not hasattr(self, 'ssh_settings'):
            QMessageBox.critical(self, "Error", "SSH settings are not configured. Please use SSH Config to set them up.")
            return

        reply = QMessageBox.question(self, 'Confirmation', 'Are you sure you want apply the config? This will restart the dbus-serialbattery driver',
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                ssh_client = paramiko.SSHClient()
                ssh_client.load_system_host_keys()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(
                    self.ssh_settings['hostname'],
                    username=self.ssh_settings['username'],
                    password=self.ssh_settings['password']
                )

                # Run the remote script to restart dbus-serialbattery
                ssh_client.exec_command("/data/etc/dbus-serialbattery/restart-driver.sh")

                ssh_client.close()

                QMessageBox.information(self, "Success", "config has been applied.")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to restart apply config {str(e)}")

class SSHConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SSH Configuration")

        layout = QVBoxLayout()

        self.username_field = QLineEdit(self)
        self.username_field.setPlaceholderText("SSH Username")
        layout.addWidget(self.username_field)

        self.password_field = QLineEdit(self)
        self.password_field.setPlaceholderText("SSH Password")
        self.password_field.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_field)

        self.hostname_field = QLineEdit(self)
        self.hostname_field.setPlaceholderText("Hostname or IP Address")
        layout.addWidget(self.hostname_field)

        self.remote_config_field = QLineEdit(self)
        self.remote_config_field.setPlaceholderText("Remote Config File Path (e.g., /path/to/config.ini)")
        layout.addWidget(self.remote_config_field)

        # SSH Config
        ssh_config_dir = os.path.join(os.path.expanduser("~"), ".dbus-serialbattery-gui")
        os.makedirs(ssh_config_dir, exist_ok=True)
        ssh_config_path = os.path.join(ssh_config_dir, "ssh_config.txt")
        if os.path.exists(ssh_config_path):
            with open(ssh_config_path, "r") as ssh_config_file:
                lines = ssh_config_file.readlines()
                ssh_settings = {}
                for line in lines:
                    key, value = line.strip().split('=')
                    ssh_settings[key] = value
            self.username_field.setText(ssh_settings.get("username", ""))
            self.password_field.setText(ssh_settings.get("password", ""))
            self.hostname_field.setText(ssh_settings.get("hostname", ""))
            self.remote_config_field.setText(ssh_settings.get("remote_config_path", ""))

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)
        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConfigEditor()
    window.show()
    sys.exit(app.exec_())
