# Flask Face Recognition App

This repository contains a Flask application for face recognition. It allows users to add their face to a database and then perform face recognition to identify if the person is known. The application uses `face_recognition`, `Flask`, `SQLAlchemy`, and `pytz` for handling timezone-aware datetime objects.

## Features

- Add a face to the database with a unique username.
- Perform face recognition to check if the face is already in the database.
- Update the "last seen" timestamp for recognized faces.
- Responsive web interface for adding faces and performing recognition.

## Installation

### Prerequisites

- Python 3.6+
- pip

### Setup

1. Clone the repository to your local machine.

2. Install the required Python packages.

3. Set up the environment variable for the database URL. Replace `your_database_url` with your actual database URL.

4. Initialize the database.

5. Run the Flask application.

## Usage

### Adding a Face

1. Navigate to `/add_face` in your web browser.
2. Enter a username and upload an image of the face.
3. Submit the form to add the face to the database.

### Performing Face Recognition

1. Send a POST request to `/compare_face` with an image.
2. The application will respond with whether the face is recognized, along with the username and last seen timestamp if a match is found.

## API Reference

- `POST /face` - Add a new face to the database.
- `POST /compare_face` - Compare a face against the known faces in the database.

## Contributing

Contributions to this project are welcome. Please fork the repository and submit a pull request with your changes.
