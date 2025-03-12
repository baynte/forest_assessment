from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required
from app.models.assessment import Assessment

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page route"""
    return render_template('index.html', title='Home')

@main_bp.route('/about')
def about():
    """About page route"""
    return render_template('about.html', title='About')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard route - displays user's assessment statistics"""
    # Get all assessments for the current user
    assessments = Assessment.query.filter_by(user_id=current_user.id).all()
    
    # Get completed assessments (those with damage_percentage calculated)
    completed_assessments = [a for a in assessments if a.damage_percentage is not None]
    
    # Get pending assessments (those without damage_percentage calculated)
    pending_assessments = [a for a in assessments if a.damage_percentage is None]
    
    # Get recent assessments (last 5)
    recent_assessments = Assessment.query.filter_by(user_id=current_user.id).order_by(
        Assessment.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                          title='Dashboard',
                          assessments=assessments,
                          completed_assessments=completed_assessments,
                          pending_assessments=pending_assessments,
                          recent_assessments=recent_assessments) 