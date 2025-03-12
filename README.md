# Post-Typhoon Forest Damage Assessment

A web application for assessing forest damage after typhoons using deep learning and image processing techniques.

## Overview

This application uses Convolutional Neural Networks (CNN) with U-Net architecture to analyze pre and post-typhoon images, perform semantic segmentation, and calculate forest damage percentages. It is designed to help forest management authorities make informed decisions after natural disasters.

## Features

- User authentication and management
- Upload and management of pre and post-typhoon images
- Semantic segmentation of forest images
- Change detection between pre and post-typhoon images
- Damage assessment calculation
- Visualization of results
- Report generation

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Image Processing**: OpenCV, NumPy
- **Deep Learning**: TensorFlow
- **Frontend**: HTML, CSS, JavaScript, Bootstrap

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd forest-assessment
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   python run.py
   ```

5. Access the application in your web browser at `http://localhost:5000`

## Usage

1. Register a new account or login with existing credentials
2. Create a new assessment by providing basic information
3. Upload pre and post-typhoon images
4. Process the images to perform semantic segmentation and damage assessment
5. View the results and generate reports

## Project Structure

```
forest_assessment/
├── app/
│   ├── models/          # Database models
│   ├── routes/          # Route handlers
│   ├── static/          # Static files (CSS, JS, images)
│   ├── templates/       # HTML templates
│   ├── utils/           # Utility functions
│   └── __init__.py      # Application factory
├── run.py               # Application entry point
└── README.md            # Project documentation
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Based on research by GORAN PHILLIPS P. MILAGAN and DESFER JOHN A. ENRIQUEZ
- Utilizes concepts from "Post-Typhoon Forest Damage Assessment using Deep-Learning and Unmanned Aerial Vehicle Images" 