import sys
from check_dependencies import suggest_installs

if not suggest_installs():
    sys.exit(1)

# Try Qt6, fallback to Qt5 (PySide2 or PyQt5)
try:
    from PySide6.QtWidgets import QApplication
    exec_method = 'exec'
except ImportError:
    try:
        from PySide2.QtWidgets import QApplication
        exec_method = 'exec_'
    except ImportError:
        from PyQt5.QtWidgets import QApplication
        exec_method = 'exec_'

from gui import PDFShrinkWindow

def main():
    app = QApplication(sys.argv)
    window = PDFShrinkWindow()
    window.show()
    # Use correct exec based on binding
    exit_code = getattr(app, exec_method)()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
