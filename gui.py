import os
# Try Qt6, fallback to Qt5 via PySide2 or PyQt5
try:
    from PySide6.QtWidgets import (
        QApplication, QWidget, QFileDialog, QPushButton, QLabel,
        QSlider, QProgressBar, QTextEdit, QVBoxLayout, QHBoxLayout, QMessageBox
    )
    from PySide6.QtCore import Qt, QThread
    exec_attr = 'exec'
except ImportError:
    try:
        from PySide2.QtWidgets import (
            QApplication, QWidget, QFileDialog, QPushButton, QLabel,
            QSlider, QProgressBar, QTextEdit, QVBoxLayout, QHBoxLayout, QMessageBox
        )
        from PySide2.QtCore import Qt, QThread
        exec_attr = 'exec_'
    except ImportError:
        from PyQt5.QtWidgets import (
            QApplication, QWidget, QFileDialog, QPushButton, QLabel,
            QSlider, QProgressBar, QTextEdit, QVBoxLayout, QHBoxLayout, QMessageBox
        )
        from PyQt5.QtCore import Qt, QThread
        exec_attr = 'exec_'

from compressor import CompressWorker

class PDFShrinkWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDFShrink")
        self.resize(600, 500)
        layout = QVBoxLayout(self)

        # File selection
        self.input_label = QLabel("No file selected.")
        layout.addWidget(self.input_label)
        browse_btn = QPushButton("Browse PDF")
        browse_btn.clicked.connect(self.select_file)
        layout.addWidget(browse_btn)

        # Output folder selection
        self.output_label = QLabel("Output folder: Same as source")
        layout.addWidget(self.output_label)
        out_btn = QPushButton("Select Output Folder")
        out_btn.clicked.connect(self.select_output_folder)
        layout.addWidget(out_btn)

        # Quality slider
        q_layout = QHBoxLayout()
        q_layout.addWidget(QLabel("Quality:"))
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(15, 50)
        self.quality_slider.setValue(40)
        self.quality_slider.valueChanged.connect(self.update_quality_label)
        q_layout.addWidget(self.quality_slider)
        self.quality_label = QLabel(str(self.quality_slider.value()))
        q_layout.addWidget(self.quality_label)
        layout.addLayout(q_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        # Shrink button
        self.shrink_btn = QPushButton("Shrink PDF")
        self.shrink_btn.clicked.connect(self.start_compression)
        layout.addWidget(self.shrink_btn)

        # Log toggle button
        self.toggle_log_btn = QPushButton("Show Log")
        self.toggle_log_btn.setCheckable(True)
        self.toggle_log_btn.toggled.connect(self.toggle_log)
        layout.addWidget(self.toggle_log_btn)

        # Log output box
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.hide()
        layout.addWidget(self.log_edit)

        # Thread placeholder
        self.worker_thread = None

    def update_quality_label(self, value):
        self.quality_label.setText(str(value))

    def toggle_log(self, checked):
        self.log_edit.setVisible(checked)
        self.toggle_log_btn.setText("Hide Log" if checked else "Show Log")

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if path:
            self.input_path = path
            self.input_label.setText(path)

    def select_output_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if path:
            self.output_path = path
            self.output_label.setText(f"Output folder: {path}")

    def start_compression(self):
        if not getattr(self, 'input_path', None):
            QMessageBox.critical(self, "Error", "No PDF selected.")
            return

        # Disable the button and show log
        self.shrink_btn.setEnabled(False)
        if not self.toggle_log_btn.isChecked():
            self.toggle_log_btn.setChecked(True)

        # Reset UI
        self.log_edit.clear()
        self.progress_bar.setValue(0)

        quality = self.quality_slider.value()
        out_dir = getattr(self, 'output_path', os.path.dirname(self.input_path))

        # Set up worker and thread
        worker = CompressWorker(self.input_path, out_dir, quality)
        self.worker = worker  # keep a reference so it's not garbage-collected

        thread = QThread()
        self.thread = thread  # keep a reference to prevent premature GC
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.progress.connect(self.progress_bar.setValue)
        worker.log_line.connect(self.log_edit.append)
        worker.finished.connect(lambda ok, out: self.on_finished(ok, out))

        # Clean up after finish
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        # Start compression
        thread.start()
        self.worker_thread = thread

    def on_finished(self, success, output_file):
        self.shrink_btn.setEnabled(True)

        if success:
            self.log_edit.append(f"\nOutput saved to: {output_file}")
            QMessageBox.information(self, "Done", f"Saved to:\n{output_file}")
        else:
            self.log_edit.append("\nCompression failed. Check the log.")
            QMessageBox.critical(self, "Error", "Compression failed. Check the log.")

# Optional run function
def run_gui():
    import sys
    app = QApplication(sys.argv)
    window = PDFShrinkWindow()
    window.show()
    getattr(app, exec_attr)()

