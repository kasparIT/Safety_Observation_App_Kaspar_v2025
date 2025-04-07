###venv\Scripts\Activate  ---- to activate env

from app import create_app

app = create_app()

if __name__ == "__main__":
    print("Starting Flask server...")  # Debugging output
    #app.run(debug=True) # For development purposes only
    app.run(host="0.0.0.0", port=5000, debug=False) # For production use, set debug=False
