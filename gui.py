import os
import shutil
import re
import subprocess
from utils import generate_output_filename

# Qt imports with fallback
try:
    from PySide6.QtWidgets import (
        QApplication, QWidget, QFileDialog, QPushButton, QLabel,
        QLineEdit, QSlider, QProgressBar, QTextEdit,
        QVBoxLayout, QHBoxLayout, QMessageBox, QGroupBox, QCheckBox, QSpacerItem, QSizePolicy
    )
    from PySide6.QtCore import Qt, QThread
    exec_attr = 'exec'
except ImportError:
    try:
        from PySide2.QtWidgets import (
            QApplication, QWidget, QFileDialog, QPushButton, QLabel,
            QLineEdit, QSlider, QProgressBar, QTextEdit,
            QVBoxLayout, QHBoxLayout, QMessageBox, QGroupBox, QCheckBox, QSpacerItem, QSizePolicy
        )
        from PySide2.QtCore import Qt, QThread
        exec_attr = 'exec_'
    except ImportError:
        from PyQt5.QtWidgets import (
            QApplication, QWidget, QFileDialog, QPushButton, QLabel,
            QLineEdit, QSlider, QProgressBar, QTextEdit,
            QVBoxLayout, QHBoxLayout, QMessageBox, QGroupBox, QCheckBox, QSpacerItem, QSizePolicy
        )
        from PyQt5.QtCore import Qt, QThread
        exec_attr = 'exec_'

from compressor import CompressWorker

class PDFShrinkWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDFShrink")
        self.resize(650, 430)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)
        self.main_layout.setContentsMargins(5, 5, 5, 5)

        # Source PDF
        src_group = QGroupBox("Source PDF")
        src_layout = QHBoxLayout()
        self.input_label = QLabel("No file selected.")
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self.select_file)
        src_layout.addWidget(self.input_label)
        src_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        src_layout.addWidget(browse_btn)
        src_group.setLayout(src_layout)
        self.main_layout.addWidget(src_group)

        # Destination (folder + filename)
        dest_group = QGroupBox("Destination")
        dest_layout = QHBoxLayout()
        self.output_label = QLabel("Same as source folder")
        self.filename_edit = QLineEdit()
        self.filename_edit.setPlaceholderText("Output filename (auto-generated if blank)")
        self.filename_edit.setMinimumWidth(400)
        folder_btn = QPushButton("Change Folder…")
        folder_btn.clicked.connect(self.select_output_folder)
        dest_layout.addWidget(self.output_label)
        dest_layout.addWidget(self.filename_edit)
        dest_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        dest_layout.addWidget(folder_btn)
        dest_group.setLayout(dest_layout)
        self.main_layout.addWidget(dest_group)

        # JPEG Quality
        quality_group = QGroupBox("JPEG Quality")
        q_layout = QHBoxLayout()
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(15, 50)
        self.quality_slider.setValue(40)
        self.quality_slider.valueChanged.connect(self.update_quality_label)
        self.quality_label = QLabel(str(self.quality_slider.value()))
        q_layout.addWidget(self.quality_slider)
        q_layout.addWidget(self.quality_label)
        quality_group.setLayout(q_layout)
        self.main_layout.addWidget(quality_group)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.hide()
        self.main_layout.addWidget(self.progress_bar)

        # Action Button
        action_layout = QHBoxLayout()
        action_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.shrink_btn = QPushButton("Shrink PDF")
        self.shrink_btn.setMinimumHeight(50)
        self.shrink_btn.setStyleSheet("font-size: 18px;")
        self.shrink_btn.clicked.connect(self.start_compression)
        action_layout.addWidget(self.shrink_btn)
        action_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.main_layout.addLayout(action_layout)

                # Dark Mode Toggle
        self.dark_toggle = QCheckBox("Dark Mode")
        self.dark_toggle.stateChanged.connect(self.toggle_dark_mode)

        # Log Output (collapsible)
        self.log_group = QGroupBox("Log Output")
        self.log_group.setCheckable(True)
        self.log_group.setChecked(False)
        lg_layout = QVBoxLayout()
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.hide()
        self.log_group.toggled.connect(self.log_edit.setVisible)
        lg_layout.addWidget(self.log_edit)
        self.log_group.setLayout(lg_layout)
        self.main_layout.addWidget(self.log_group)

        # Dark Mode Toggle (aligned right)
        toggle_layout = QHBoxLayout()
        toggle_layout.addStretch()
        toggle_layout.addWidget(self.dark_toggle)
        self.main_layout.addLayout(toggle_layout)

        # Worker/Thread refs
        self.worker = None
        self.thread = None

    def update_quality_label(self, value):
        self.quality_label.setText(str(value))

    def toggle_dark_mode(self, state):
        if state == Qt.Checked:
            self.setStyleSheet("""
                QWidget { background-color: #2b2b2b; color: #e0e0e0; }
                QLineEdit, QTextEdit { background-color: #3c3c3c; color: #e0e0e0; }
                QSlider::groove:horizontal { background: #444444; height: 8px; border-radius: 4px; }
                QSlider::sub-page:horizontal { background: #888888; border-radius: 4px; }
                QSlider::handle:horizontal { background: #dddddd; border: 1px solid #777777; width: 14px; margin: -3px 0; border-radius: 7px; }
            """)
        else:
            self.setStyleSheet("")

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF", "", "PDF Files (*.pdf)")
        if path:
            self.input_path = path
            base = os.path.basename(path)
            self.input_label.setText(base)
            self.output_path = os.path.dirname(path)
            self.output_label.setText(os.path.basename(self.output_path) or "Same as source folder")
            name = os.path.splitext(base)[0]
            default = f"{name}_compressed_q{self.quality_slider.value()}.pdf"
            self.filename_edit.setText(default)

    def select_output_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if path:
            self.output_path = path
            self.output_label.setText(os.path.basename(path) or path)

    def start_compression(self):
        if not getattr(self, 'input_path', None):
            QMessageBox.critical(self, "Error", "Please select a PDF first.")
            return

        self.shrink_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.log_edit.clear()

        quality = self.quality_slider.value()
        out_dir = self.output_path
        out_name = self.filename_edit.text().strip() or None

        self.worker = CompressWorker(self.input_path, out_dir, quality, output_filename=out_name)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.log_line.connect(self.log_edit.append)
        self.worker.finished.connect(self.on_finished)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_finished(self, success, output_file):
        self.shrink_btn.setEnabled(True)
        self.progress_bar.hide()
        if success:
            QMessageBox.information(self, "Success", f"Saved to:\n{output_file}")
        else:
            QMessageBox.critical(self, "Failure", "Compression failed. See log for details.")
