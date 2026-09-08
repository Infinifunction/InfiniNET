import os
import sys
import time
import importlib
import threading

#-------------------------------------------#
# Defines the file extensions monitored by the hot-reload system.
# These extensions cover Python source files and the frontend assets
# that can change during development.
#-------------------------------------------#
WATCHED_EXTENSIONS = ('.py', '.js', '.html', '.css')

#-------------------------------------------#
# Defines directories that should be ignored while recursively scanning
# the project tree. These locations normally contain generated files,
# version-control metadata, IDE configuration, or isolated environments
# that do not need to trigger a reload.
#-------------------------------------------#
EXCLUDE_DIRS = {'__pycache__', '.git', '.idea', '.vscode', 'venv', 'env'}

#-------------------------------------------#
# Resolves the absolute path of the directory containing this reloader.
# This directory is treated as the root of the project that should be
# monitored for source-code and frontend changes.
#-------------------------------------------#
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

_RELOADER_THREAD = None
_RUNNING = False


def get_all_file_times():
    #-------------------------------------------#
    # Recursively scans the project directory for supported files and
    # stores each file's last modification timestamp. The resulting
    # dictionary is later used to detect modified or newly created files.
    #-------------------------------------------#
    file_times = {}

    for root, dirs, files in os.walk(PROJECT_ROOT):
        #-------------------------------------------#
        # Removes excluded directories from the active traversal list.
        # Updating dirs in place prevents os.walk from entering folders
        # that are intentionally ignored by the reloader.
        #-------------------------------------------#
        dirs[:] = [directory for directory in dirs if directory not in EXCLUDE_DIRS]

        for file in files:
            if file.endswith(WATCHED_EXTENSIONS):
                file_path = os.path.join(root, file)

                try:
                    file_times[file_path] = os.path.getmtime(file_path)
                except OSError:
                    pass

    return file_times


def reload_all_loaded_modules(changed_file=None):
    #-------------------------------------------#
    # Reloads Python modules belonging to the current project when a
    # relevant source file changes. Frontend-only changes are reported
    # without unnecessarily reloading Python modules.
    #-------------------------------------------#
    file_name = os.path.basename(changed_file) if changed_file else "Unknown File"

    if changed_file:
        print(
            f"\n[⚡ CHANGE DETECTED] '{file_name}' was updated. Refreshing the system..."
        )
    else:
        print(
            "\n[🔄 MANUAL TRIGGER] Hot Reload was triggered from the Admin Panel..."
        )

    #-------------------------------------------#
    # JavaScript, HTML, and CSS files do not require Python module
    # reloading. The frontend update is reported so the browser can
    # be refreshed when necessary.
    #-------------------------------------------#
    if changed_file and changed_file.endswith(('.js', '.html', '.css')):
        print(
            f"  └─ 🌐 [FRONTEND UPDATED] '{file_name}' was updated. "
            "(Refreshing the browser is sufficient)\n"
        )
        return True

    reload_successful = True

    #-------------------------------------------#
    # Collects only loaded Python modules whose source files are located
    # inside the project directory. The main module and this reloader
    # module are excluded to prevent unsafe or unnecessary reloads.
    #-------------------------------------------#
    loaded_project_modules = []

    for module_name, module in list(sys.modules.items()):
        if (
            module_name != '__main__'
            and module
            and hasattr(module, '__file__')
            and module.__file__
        ):
            module_file = os.path.abspath(module.__file__)

            if (
                module_file.startswith(PROJECT_ROOT)
                and not module_file.endswith('auto_reloader.py')
            ):
                loaded_project_modules.append((module_name, module))

    #-------------------------------------------#
    # Reloads every collected project module and reports the result
    # individually. If any module fails to reload, the overall operation
    # is marked as unsuccessful while the remaining modules continue.
    #-------------------------------------------#
    for module_name, module in loaded_project_modules:
        try:
            importlib.reload(module)
            print(f"  └─ 🟢 [RAM UPDATED] {module_name}")
        except Exception as error:
            print(f"  └─ 🔴 [RELOAD ERROR] {module_name}: {error}")
            reload_successful = False

    #-------------------------------------------#
    # Reports whether the complete reload operation succeeded. A failed
    # reload may indicate a syntax or other runtime-related code issue
    # that should be investigated in the latest changes.
    #-------------------------------------------#
    if reload_successful:
        print(
            "[✓ HOT RELOAD COMPLETED] Changes were successfully applied "
            "to the live system!\n"
        )
    else:
        print(
            "[⚠️ WARNING] The code may contain a syntax or writing error. "
            "Please check the latest changes.\n"
        )

    return reload_successful


def file_watcher():
    #-------------------------------------------#
    # Starts the continuous file-monitoring loop. The watcher periodically
    # compares the current modification timestamps with the previous scan
    # and triggers a reload whenever a supported file is created or changed.
    #-------------------------------------------#
    global _RUNNING

    print("[🔄 DYNAMIC HOT RELOAD] Automatic Watcher Active!")
    print(f"  └─ Root Directory: {PROJECT_ROOT}")
    print(
        "  └─ Monitored: *.py, *.js, *.html, *.css "
        "(Including all subdirectories)\n"
    )

    last_file_times = get_all_file_times()

    while _RUNNING:
        #-------------------------------------------#
        # Waits briefly between scans to continuously monitor the project
        # without consuming unnecessary CPU resources.
        #-------------------------------------------#
        time.sleep(1)

        current_file_times = get_all_file_times()

        #-------------------------------------------#
        # Detects newly created files and files whose modification timestamp
        # is newer than the timestamp recorded during the previous scan.
        # The first detected change triggers a project reload.
        #-------------------------------------------#
        for file_path, modification_time in current_file_times.items():
            if (
                file_path not in last_file_times
                or modification_time > last_file_times[file_path]
            ):
                reload_all_loaded_modules(changed_file=file_path)
                last_file_times = get_all_file_times()
                break

        #-------------------------------------------#
        # Detects file deletions by comparing the number of files found in
        # the current scan with the previous scan. The timestamp snapshot
        # is synchronized again when the directory contents differ.
        #-------------------------------------------#
        if len(current_file_times) != len(last_file_times):
            last_file_times = current_file_times


def start_hot_reload():
    #-------------------------------------------#
    # Starts the background watcher thread when the hot-reload service is
    # inactive. If the watcher is already running, this function performs
    # an immediate synchronous reload instead of creating another thread.
    #-------------------------------------------#
    global _RELOADER_THREAD, _RUNNING

    if (
        not _RUNNING
        or _RELOADER_THREAD is None
        or not _RELOADER_THREAD.is_alive()
    ):
        _RUNNING = True
        _RELOADER_THREAD = threading.Thread(
            target=file_watcher,
            daemon=True,
            name="DynamicHotReloader",
        )
        _RELOADER_THREAD.start()
        return True
    else:
        return reload_all_loaded_modules()
