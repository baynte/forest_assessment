from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.assessment import Assessment
from app.forms.assessment import AssessmentForm, UploadImagesForm
from app.utils.image_processing import process_images, perform_segmentation, calculate_damage, save_segmented_image
import os
from datetime import datetime
import uuid

assessment_bp = Blueprint('assessment', __name__)

def allowed_file(filename):
    """Check if the file has an allowed extension"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tif', 'tiff'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@assessment_bp.route('/')
@login_required
def index():
    """List all assessments"""
    assessments = Assessment.query.filter_by(user_id=current_user.id).all()
    return render_template('assessment/index.html', title='Assessments', assessments=assessments)

@assessment_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_assessment():
    """Create a new assessment"""
    form = AssessmentForm()
    if form.validate_on_submit():
        assessment = Assessment(
            title=form.title.data,
            location=form.location.data,
            description=form.description.data,
            typhoon_name=form.typhoon_name.data,
            typhoon_date=form.typhoon_date.data,
            user_id=current_user.id
        )
        db.session.add(assessment)
        db.session.commit()
        flash('Assessment created successfully!', 'success')
        return redirect(url_for('assessment.upload_images', assessment_id=assessment.id))
    
    return render_template('assessment/new.html', title='New Assessment', form=form)

@assessment_bp.route('/<int:assessment_id>/upload', methods=['GET', 'POST'])
@login_required
def upload_images(assessment_id):
    """Upload pre and post typhoon images"""
    assessment = Assessment.query.get_or_404(assessment_id)
    
    # Check if the current user is the owner of the assessment
    if assessment.user_id != current_user.id:
        flash('You do not have permission to access this assessment.', 'danger')
        return redirect(url_for('assessment.index'))
    
    form = UploadImagesForm()
    if form.validate_on_submit():
        # Process pre-typhoon image
        if form.pre_image.data:
            pre_image = form.pre_image.data
            if allowed_file(pre_image.filename):
                filename = secure_filename(f"pre_{uuid.uuid4()}_{pre_image.filename}")
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                pre_image.save(filepath)
                assessment.pre_image_path = filename
            else:
                flash('Invalid file format for pre-typhoon image.', 'danger')
        
        # Process post-typhoon image
        if form.post_image.data:
            post_image = form.post_image.data
            if allowed_file(post_image.filename):
                filename = secure_filename(f"post_{uuid.uuid4()}_{post_image.filename}")
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                post_image.save(filepath)
                assessment.post_image_path = filename
            else:
                flash('Invalid file format for post-typhoon image.', 'danger')
        
        db.session.commit()
        
        # If both images are uploaded, proceed to processing
        if assessment.pre_image_path and assessment.post_image_path:
            return redirect(url_for('assessment.process', assessment_id=assessment.id))
        else:
            flash('Please upload both pre and post typhoon images.', 'warning')
    
    return render_template('assessment/upload.html', title='Upload Images', form=form, assessment=assessment)

@assessment_bp.route('/<int:assessment_id>/process')
@login_required
def process(assessment_id):
    """Process the uploaded images and perform damage assessment"""
    assessment = Assessment.query.get_or_404(assessment_id)
    
    # Check if the current user is the owner of the assessment
    if assessment.user_id != current_user.id:
        flash('You do not have permission to access this assessment.', 'danger')
        return redirect(url_for('assessment.index'))
    
    # Check if both images are uploaded
    if not assessment.pre_image_path or not assessment.post_image_path:
        flash('Please upload both pre and post typhoon images first.', 'warning')
        return redirect(url_for('assessment.upload_images', assessment_id=assessment.id))
    
    try:
        # Get full paths to the images
        pre_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], assessment.pre_image_path)
        post_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], assessment.post_image_path)
        
        # Process images (resize, normalize, etc.)
        processed_pre, processed_post = process_images(pre_image_path, post_image_path)
        
        # Perform semantic segmentation
        segmented_pre, segmented_post = perform_segmentation(processed_pre, processed_post)
        
        # Calculate damage
        forest_area_before, forest_area_after, damage_percentage = calculate_damage(segmented_pre, segmented_post)
        
        # Save segmented image
        segmented_filename = f"segmented_{uuid.uuid4()}.png"
        segmented_path = os.path.join(current_app.config['UPLOAD_FOLDER'], segmented_filename)
        
        # Save the segmented image
        save_segmented_image(segmented_post, segmented_path)
        
        # Update assessment with results
        assessment.segmented_image_path = segmented_filename
        assessment.forest_area_before = forest_area_before
        assessment.forest_area_after = forest_area_after
        assessment.damage_percentage = damage_percentage
        assessment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Assessment processing completed successfully!', 'success')
        return redirect(url_for('assessment.view', assessment_id=assessment.id))
    
    except Exception as e:
        flash(f'Error processing images: {str(e)}', 'danger')
        return redirect(url_for('assessment.upload_images', assessment_id=assessment.id))

@assessment_bp.route('/<int:assessment_id>')
@login_required
def view(assessment_id):
    """View assessment details"""
    assessment = Assessment.query.get_or_404(assessment_id)
    
    # Check if the current user is the owner of the assessment
    if assessment.user_id != current_user.id:
        flash('You do not have permission to access this assessment.', 'danger')
        return redirect(url_for('assessment.index'))
    
    return render_template('assessment/view.html', title='Assessment Details', assessment=assessment)

@assessment_bp.route('/<int:assessment_id>/delete', methods=['POST'])
@login_required
def delete(assessment_id):
    """Delete an assessment"""
    assessment = Assessment.query.get_or_404(assessment_id)
    
    # Check if the current user is the owner of the assessment
    if assessment.user_id != current_user.id:
        flash('You do not have permission to delete this assessment.', 'danger')
        return redirect(url_for('assessment.index'))
    
    # Delete associated image files
    if assessment.pre_image_path:
        pre_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], assessment.pre_image_path)
        if os.path.exists(pre_image_path):
            os.remove(pre_image_path)
    
    if assessment.post_image_path:
        post_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], assessment.post_image_path)
        if os.path.exists(post_image_path):
            os.remove(post_image_path)
    
    if assessment.segmented_image_path:
        segmented_path = os.path.join(current_app.config['UPLOAD_FOLDER'], assessment.segmented_image_path)
        if os.path.exists(segmented_path):
            os.remove(segmented_path)
    
    # Delete the assessment from the database
    db.session.delete(assessment)
    db.session.commit()
    
    flash('Assessment deleted successfully!', 'success')
    return redirect(url_for('assessment.index')) 