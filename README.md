Running the Environment
-----------------------

To activate the virtual environment, navigate to your project folder (where the .venv directory is located) and run the appropriate command based on your operating system:

Windows:

  - Command Prompt:
      .venv\Scripts\activate.bat

  - PowerShell:
      .venv\Scripts\Activate.ps1

macOS and Linux:

  source .venv/bin/activate

-----------------------

Running the Streamlit App
-------------------------

To start the app, run:

  streamlit run Home.py

If that doesn't work, try the long-form command:

  python -m streamlit run Home.py

To stop the Streamlit server, press Ctrl+C in the terminal.

-----------------------

Deactivating the Environment
----------------------------

When you're finished, return to your normal shell by running:

  deactivate


Quick Recap of the Libraries:

Streamlit: For building the app.
Plotly: For interactive charts.
Pillow: For image handling (PIL).
NumPy: For array processing.
OpenCV: For image resizing and processing.
TensorFlow: For the model inference.

To install all packages:
pip install -r requirements.txt