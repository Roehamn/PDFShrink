import os
import shutil
import re
import subprocess
from utils import generate_output_filename

# Qt signaling imports: try Qt6, PySide2, PyQt5
try:
    from PySide6.QtCore import QObject, Signal
except ImportError:
    try:
        from PySide2.QtCore import QObject, Signal
    except ImportError:
        from PyQt5.QtCore import QObject, pyqtSignal as Signal

class CompressWorker(QObject):
    log_line = Signal(str)
    progress = Signal(int)
    finished = Signal(bool, str)

    def __init__(self, input_path, output_dir, quality):
        super().__init__()
        self.input_path = input_path
        self.output_dir = output_dir
        self.quality = quality

    def run(self):
        # Check for OCRmyPDF
        if shutil.which("ocrmypdf") is None:
            self.log_line.emit("Error: 'ocrmypdf' not found in PATH.")
            self.finished.emit(False, "")
            return

        try:
            os.makedirs(self.output_dir, exist_ok=True)
            output_file = generate_output_filename(
                self.input_path, self.output_dir, self.quality
            )

            cmd = [
                "ocrmypdf", "--optimize", "3", "--output-type", "pdf",
                "--jpeg-quality", str(self.quality),
                "--skip-text", "--deskew",
                self.input_path, output_file
            ]
            self.log_line.emit(f"Running: {' '.join(cmd)}")

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            log_output = []
            for line in proc.stdout:
                text = line.rstrip()
                print(text)  # terminal mirror
                self.log_line.emit(text)
                log_output.append(text)

                match = re.search(r"page (\d+) of (\d+)", text)
                if match:
                    cur, tot = map(int, match.groups())
                    percent = int((cur / tot) * 100)
                    self.progress.emit(percent)

            proc.wait()
            if proc.returncode == 0:
                self.finished.emit(True, output_file)
            else:
                self.finished.emit(False, "")

        except Exception as e:
            self.log_line.emit(str(e))
            self.finished.emit(False, "")
