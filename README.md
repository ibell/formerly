# formerly
An experiment with minimal services with a UI

## Setup
``` 
conda env create -f environment.yml
```

## Run

1. Run the Flask app natively:
```
python calculator.py
```
Then open your browser and go to localhost:5000

2. Run the Flask app in pywebview
```
python run_webview.py
```

# Package the executable
On OSX:
```
python py2app_setup.py py2app
./dist/run_webview.app/Contents/MacOS/run_webview
```

N.B. Had to copy the libpython in webview folder; py2app was looking for the wrong one

### Other Flask->EXE wrappers
* Electron
* WebUI
* github.com/widdershin/flask-desktop.git