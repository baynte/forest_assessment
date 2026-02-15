# Post-Typhoon Forest Damage Assessment

A web application for assessing forest damage after typhoons using deep learning and image processing techniques.

## Installation (Windows with Conda)

**Prerequisites:** Conda (Miniconda or Anaconda) on Windows. Install from [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/download) if needed.

1. Clone the repository and enter the project directory:
   ```
   git clone <repository-url>
   cd forest_assessment
   ```

2. Create a Conda environment with a compatible Python version (e.g. 3.11 for TensorFlow):
   ```
   conda create -n forest_assessment python=3.11 -y
   ```

3. Activate the environment (Windows):
   ```
   conda activate forest_assessment
   ```

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Run the application:
   ```
   python run.py
   ```

6. Open your browser at `http://localhost:5000` (or the URL shown in the terminal).

You can optionally create an `environment.yml` from this environment later for a one-command setup: `conda env create -f environment.yml`.

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Image Processing**: OpenCV, NumPy
- **Deep Learning**: TensorFlow
- **Frontend**: HTML, CSS, JavaScript, Bootstrap

## System Functionality

### Overview and purpose

This application analyzes pre- and post-typhoon images to perform semantic segmentation and compute forest damage percentages. It supports forest management and recovery decisions after natural disasters by quantifying vegetation loss between two image dates.

### User authentication and management

- **Registration:** Users register with username, email, and password (with confirmation). The app validates unique username and email and enforces password length.
- **Login / Logout:** Login uses username (or email in some flows), with an optional "remember me" option. After login, users are redirected to the dashboard or the page they requested. Logout clears the session.
- **User model:** Each user has id, username, email, password hash, role, and created_at, and is linked to their assessments.

### Dashboard and navigation

- **Dashboard:** Shows the current user’s assessments, split into completed (with damage percentage) and pending. Recent assessments (e.g. last 5) are listed, with links to create a new assessment and to view all assessments.
- **Navigation:** The app provides Home, About, Dashboard, My Assessments, and either Login/Register or Logout depending on authentication state.

### Assessment lifecycle

- **Create assessment:** User enters title, location, description, typhoon name, and typhoon date. The assessment is stored and the user is redirected to the upload step.
- **Upload images:** Pre-typhoon and post-typhoon images are uploaded (formats: PNG, JPG, JPEG, TIF, TIFF). Files are saved under `static/uploads` with unique names; the assessment is updated with `pre_image_path` and `post_image_path`. Both images are required before processing.
- **Process images:** From the assessment view or upload step, the user triggers processing. The pipeline loads and aligns image sizes, runs segmentation, computes damage, and saves a segmented visualization. Results (forest area before/after, damage percentage, segmented image path) are stored on the assessment.
- **View assessment:** The detail page shows metadata, pre/post images, the segmented image, damage statistics (forest area before/after, damage %), and actions such as export report (placeholder) and delete assessment.
- **Delete assessment:** The assessment record and its files (pre, post, segmented) are removed from disk and the database. Only the owner can delete.

### Research basis (manuscript methods)

The application follows the methodology described in the thesis *Post-Typhoon Forest Damage Assessment using Deep-Learning and Unmanned Aerial Vehicle Images* (Milagan & Enriquez, Caraga State University, 2021). The manuscript specifies:

- **Semantic segmentation:** Six classes—Building, Land, Road, Vegetation, Water, Unlabeled—with pixel-wise labels. Masks use fixed RGB values converted to HEX and then integer-encoded (e.g. Building `#3C1098`, Land `#8429F6`, Road `#6EC1E4`, Vegetation `#FEDD3A`, Water `#E2A929`, Unlabeled `#9B9B9B`). The thesis uses a U-Net (Ronneberger) with ResNet34 backbone, 256×256 patches, MinMaxScaler normalization, and dice + focal loss for training.
- **Change detection:** Pre- and post-typhoon masks are converted to integer labels; per-class pixel counts are computed with `np.sum(label == class_id)`. Forest/vegetation and other class coverages are reported as percentages of total pixels. Damage is derived from the difference in these percentages between pre and post (focus on forested/vegetation area).
- **Plotting and visualization:** The manuscript uses matplotlib (e.g. `pyplot`) to display segmented predictions and ground-truth masks (side-by-side pre/post), with legends for Forest, Vegetation, Water, Unlabeled (and Building, Road where applicable). Results include area percentages per class and damage assessment percentage.


### Image processing and damage assessment pipeline

The pipeline in `app/utils/image_processing.py` implements a subset of the above:

- **Loading and alignment:** Pre- and post-typhoon images are loaded with OpenCV. If sizes differ, the post image is resized to match the pre image. Images are converted to RGB/HSV as needed.
- **Semantic segmentation (`perform_segmentation`):** Pixel classification into the same conceptual classes (unlabeled, land, water, vegetation), using the manuscript’s HEX/RGB color convention where applicable. The current code uses rule-based indices (Excess Green, channel dominance) rather than a trained U-Net; output is integer class labels compatible with the manuscript’s encoding.
- **Change detection:** Pre- and post-segmentation masks are compared. Vegetation in the pre-image that is no longer vegetation in the post (by class or by strong HSV change) is treated as damaged. This aligns with the manuscript’s change detection by pixel count and class difference.
- **Damage calculation (`calculate_damage`):** Damage = (pixels that were vegetation in pre but not in post) / (vegetation pixels in pre) × 100, clamped to 0–100%. Forest area before/after are reported as percentages of total pixels, matching the manuscript’s “forest covered area” and “vegetation covered area” style metrics.
- **Visualization and output:** Segmentation and change maps are color-coded (vegetation green, land brown, water blue; damaged areas red). Pre/post/change images are saved under `static/uploads` and shown in the assessment view with a legend-style presentation consistent with the manuscript’s figures.

### Data and access control

- **Database:** SQLite (`forest_assessment.db`). Tables are created on first run via `db.create_all()` in `run.py`.
- **Access control:** Assessments are scoped by `user_id`. Upload, process, view, and delete checks ensure only the owning user can access or modify an assessment.

## Usage

1. Register a new account or log in with existing credentials.
2. Create a new assessment (title, location, optional description, typhoon name/date).
3. Upload pre-typhoon and post-typhoon images for that assessment.
4. Run “Process images” to perform segmentation and damage assessment.
5. View the results (metadata, images, damage stats) and optionally delete or export (when implemented).

## Project Structure

```
forest_assessment/
├── app/
│   ├── forms/           # WTForms (auth, assessment)
│   ├── models.py        # SQLAlchemy models (User, Assessment)
│   ├── routes.py        # Legacy route handlers
│   ├── routes/          # Blueprint route handlers (main, auth, assessment)
│   ├── static/          # Static files (CSS, JS, uploads)
│   ├── templates/       # HTML templates
│   ├── utils/           # Utilities (e.g. image_processing.py)
│   └── __init__.py      # App factory and config
├── run.py               # Application entry point
├── read_manuscript.py   # Extract text from manuscript.docx (requires python-docx)
├── requirements.txt     # Python dependencies
├── recreate_db.py      # Optional DB recreation script
├── check_db.py          # Optional DB check script
├── debug_db.py          # Optional DB debug script
└── README.md            # Project documentation
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Based on research by GORAN PHILLIPS P. MILAGAN and DESFER JOHN A. ENRIQUEZ
- Utilizes concepts from "Post-Typhoon Forest Damage Assessment using Deep-Learning and Unmanned Aerial Vehicle Images"
