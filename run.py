from app import create_app

app = create_app()

if __name__ == "__main__":
    print("Starting Flask server...")  # Debugging output
    app.run(debug=True)
