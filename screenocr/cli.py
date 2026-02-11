import multiprocessing
import sys

from .app import main as app_main
from .editor_host import run_editor_window


def main():
    multiprocessing.freeze_support()

    if len(sys.argv) >= 3 and sys.argv[1] == "--editor":
        run_editor_window(sys.argv[2])
        return

    app_main()


if __name__ == "__main__":
    main()

