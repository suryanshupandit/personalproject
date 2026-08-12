import sys
import os
import subprocess

# Ensure required packages are installed for the current Python interpreter.
def ensure_dependencies():
    missing = []
    try:
        import PIL  # pillow
    except Exception:
        missing.append('Pillow')
    try:
        import exifread
    except Exception:
        missing.append('exifread')
    try:
        import cv2
    except Exception:
        missing.append('opencv-python')
    try:
        import numpy
    except Exception:
        missing.append('numpy')

    if missing:
        print('Installing missing packages:', ', '.join(missing))
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
        except subprocess.CalledProcessError as e:
            print('Failed to install packages:', e)
            sys.exit(1)
        # Spawn a new interpreter process so newly-installed packages are importable
        print('Packages installed. Launching a fresh Python process...')
        try:
            rc = subprocess.call([sys.executable] + sys.argv)
            sys.exit(rc)
        except Exception as e:
            print('Failed to restart Python process:', e)
            sys.exit(1)


if __name__ == '__main__':
    ensure_dependencies()

    # now that deps exist, import the analyzer and continue
    from backend.analyzer.image_analyzer import analyze_image_bytes

    print('AI Content Detector - Image Analyzer')
    print('Application started successfully!')
