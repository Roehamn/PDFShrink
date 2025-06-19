import shutil
import importlib.util

# Check for at least one Qt binding: PySide6, PySide2, or PyQt5
QT_BINDINGS = ["PySide6", "PySide2", "PyQt5"]
DEPENDENCIES = [
    # Recommend system package python3-pyqt5 (Qt5) if no Qt binding found
    ("Qt", "sudo apt install python3-pyqt5", "python"),
    ("ocrmypdf", "sudo apt install ocrmypdf", "cli"),
    ("ghostscript", "sudo apt install ghostscript", "cli"),
]

def check_dependencies():
    missing = []
    # Qt bindings check
    if not any(importlib.util.find_spec(binding) for binding in QT_BINDINGS):
        missing.append(("Qt", "sudo apt install python3-pyqt5"))

    # Other dependencies
    for name, command, dtype in DEPENDENCIES[1:]:
        if dtype == "python":
            if importlib.util.find_spec(name) is None:
                missing.append((name, command))
        else:
            if shutil.which(name) is None:
                missing.append((name, command))
    return missing


def suggest_installs():
    missing = check_dependencies()
    if not missing:
        return True

    print("\n🚨 Missing dependencies detected:")
    for name, command in missing:
        print(f"- {name}: install with `{command}`")
    print("\nPlease install these and re-run the application.")
    return False
