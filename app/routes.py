from app import app, db
from flask import render_template, url_for, flash, redirect, request, send_from_directory
from flask_login import login_user, current_user, logout_user, login_required
from app.models import User, Assessment
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from app.utils.image_processing import process_images

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', title='Home')

@app.route('/about')
def about():
    return render_template('about.html', title='About')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if username or email already exists
        user_exists = User.query.filter_by(username=username).first()
        email_exists = User.query.filter_by(email=email).first()
        
        if user_exists:
            flash('Username already taken. Please choose a different one.', 'danger')
            return redirect(url_for('register'))
        
        if email_exists:
            flash('Email already registered. Please use a different one.', 'danger')
            return redirect(url_for('register'))
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    
    return render_template('login.html', title='Login')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    assessments = Assessment.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', title='Dashboard', assessments=assessments)

@app.route('/assessments')
@login_required
def assessments():
    assessments = Assessment.query.filter_by(user_id=current_user.id).all()
    return render_template('assessments.html', title='My Assessments', assessments=assessments)

@app.route('/assessment/new', methods=['GET', 'POST'])
@login_required
def new_assessment():
    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        description = request.form.get('description')
        
        assessment = Assessment(
            name=name,
            location=location,
            description=description,
            user_id=current_user.id
        )
        
        db.session.add(assessment)
        db.session.commit()
        
        flash('Assessment created successfully!', 'success')
        return redirect(url_for('assessment_upload', assessment_id=assessment.id))
    
    return render_template('new_assessment.html', title='New Assessment')

@app.route('/assessment/<int:assessment_id>/upload', methods=['GET', 'POST'])
@login_required
def assessment_upload(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    
    # Check if user owns this assessment
    if assessment.user_id != current_user.id:
        flash('You do not have permission to view this assessment', 'danger')
        return redirect(url_for('assessments'))
    
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'pre_image' not in request.files or 'post_image' not in request.files:
            flash('Both pre and post typhoon images are required', 'danger')
            return redirect(request.url)
        
        pre_image = request.files['pre_image']
        post_image = request.files['post_image']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if pre_image.filename == '' or post_image.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if pre_image and post_image:
            # Ensure upload folder exists
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            try:
                # Save pre-typhoon image
                pre_filename = secure_filename(f"pre_{assessment_id}_{pre_image.filename}")
                pre_path = os.path.join(app.config['UPLOAD_FOLDER'], pre_filename)
                pre_image.save(pre_path)
                
                # Verify the file was saved
                if not os.path.exists(pre_path):
                    flash('Failed to save pre-typhoon image. Please try again.', 'danger')
                    return redirect(request.url)
                
                # Save post-typhoon image
                post_filename = secure_filename(f"post_{assessment_id}_{post_image.filename}")
                post_path = os.path.join(app.config['UPLOAD_FOLDER'], post_filename)
                post_image.save(post_path)
                
                # Verify the file was saved
                if not os.path.exists(post_path):
                    flash('Failed to save post-typhoon image. Please try again.', 'danger')
                    return redirect(request.url)
                
                # Update assessment with image paths
                assessment.pre_image = os.path.join('static/uploads', pre_filename)
                assessment.post_image = os.path.join('static/uploads', post_filename)
                db.session.commit()
                
                app.logger.info(f"Images saved successfully: {pre_path} and {post_path}")
                flash('Images uploaded successfully!', 'success')
                return redirect(url_for('assessment_process', assessment_id=assessment_id))
            
            except Exception as e:
                import traceback
                app.logger.error(f"Image upload error: {str(e)}")
                app.logger.error(traceback.format_exc())
                flash(f'Error uploading images: {str(e)}', 'danger')
                return redirect(request.url)
    
    return render_template('upload_images.html', title='Upload Images', assessment=assessment)

@app.route('/assessment/<int:assessment_id>/process', methods=['GET', 'POST'])
@login_required
def assessment_process(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    
    # Check if user owns this assessment
    if assessment.user_id != current_user.id:
        flash('You do not have permission to view this assessment', 'danger')
        return redirect(url_for('assessments'))
    
    # Check if images are uploaded
    if not assessment.pre_image or not assessment.post_image:
        flash('Please upload both pre and post typhoon images first', 'warning')
        return redirect(url_for('assessment_upload', assessment_id=assessment_id))
    
    # Process images - use the correct path
    pre_image_path = os.path.join(app.root_path, assessment.pre_image)
    post_image_path = os.path.join(app.root_path, assessment.post_image)
    
    app.logger.info(f"Processing images at: {pre_image_path} and {post_image_path}")
    
    # Check if image files exist
    if not os.path.exists(pre_image_path):
        flash(f'Pre-typhoon image file not found at {pre_image_path}. Please upload again.', 'danger')
        return redirect(url_for('assessment_upload', assessment_id=assessment_id))
        
    if not os.path.exists(post_image_path):
        flash(f'Post-typhoon image file not found at {post_image_path}. Please upload again.', 'danger')
        return redirect(url_for('assessment_upload', assessment_id=assessment_id))
    
    try:
        # Process images and get results
        result_data = process_images(pre_image_path, post_image_path)
        
        # Update assessment with results
        assessment.forest_area_before = result_data['forest_area_before']
        assessment.forest_area_after = result_data['forest_area_after']
        assessment.damage_percentage = result_data['damage_percentage']
        assessment.pre_vis_path = result_data['pre_vis_path']
        assessment.post_vis_path = result_data['post_vis_path']
        assessment.change_vis_path = result_data['change_vis_path']
        assessment.processed_date = datetime.now()
        
        db.session.commit()
        
        flash('Assessment processed successfully', 'success')
        return redirect(url_for('assessment_view', assessment_id=assessment_id))
    
    except Exception as e:
        import traceback
        app.logger.error(f"Image processing error: {str(e)}")
        app.logger.error(traceback.format_exc())
        flash(f'Error processing images: {str(e)}', 'danger')
        return redirect(url_for('assessment_upload', assessment_id=assessment_id))

@app.route('/assessment/<int:assessment_id>/view')
@login_required
def assessment_view(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    
    # Check if user owns this assessment
    if assessment.user_id != current_user.id:
        flash('You do not have permission to view this assessment', 'danger')
        return redirect(url_for('assessments'))
    
    # Check if assessment has been processed
    if not assessment.processed:
        flash('This assessment has not been processed yet', 'warning')
        return redirect(url_for('assessment_upload', assessment_id=assessment_id))
    
    # Log image paths for debugging
    app.logger.info(f"Pre-image path: {assessment.pre_image}")
    app.logger.info(f"Post-image path: {assessment.post_image}")
    app.logger.info(f"Pre-vis path: {assessment.pre_vis_path}")
    app.logger.info(f"Post-vis path: {assessment.post_vis_path}")
    app.logger.info(f"Change-vis path: {assessment.change_vis_path}")
    
    return render_template('assessment_view.html', 
                          title='Assessment Results',
                          assessment=assessment)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files directly for debugging purposes"""
    app.logger.info(f"Serving uploaded file: {filename}")
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename) 