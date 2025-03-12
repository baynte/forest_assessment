from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, DateField, SubmitField
from wtforms.validators import DataRequired, Length

class AssessmentForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=100)])
    location = StringField('Location', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description')
    typhoon_name = StringField('Typhoon Name', validators=[Length(max=50)])
    typhoon_date = DateField('Typhoon Date', format='%Y-%m-%d')
    submit = SubmitField('Create Assessment')

class UploadImagesForm(FlaskForm):
    pre_image = FileField('Pre-Typhoon Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'tif', 'tiff'], 'Images only!')
    ])
    post_image = FileField('Post-Typhoon Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'tif', 'tiff'], 'Images only!')
    ])
    submit = SubmitField('Upload Images') 