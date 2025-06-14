# Backend

This is the Flask backend for the SpecBot application.

## Setup

1. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Run the server:
   ```
   python server.py
   ```

## Files

- `server.py` - Main Flask application
- `Analysis.py` - Code for algorithm analysis
- `requirements.txt` - Python dependencies

## Note

Large input files have been excluded from the repository. See the README in the Inputs directory for more information.

## How to run Docker img/ compilation of docker file

```
docker build -t your-image-name .
```