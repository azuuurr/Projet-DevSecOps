from flask_wtf import FlaskForm
from wtforms import DateField, DecimalField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class EvaluationForm(FlaskForm):
    title = StringField(
        "Titre de l'évaluation",
        validators=[DataRequired(), Length(max=200)],
    )
    date = DateField(
        "Date",
        validators=[DataRequired()],
    )
    coefficient = DecimalField(
        "Coefficient",
        default=1.0,
        validators=[DataRequired(), NumberRange(min=0.1, max=10.0)],
    )
    submit = SubmitField("Enregistrer")


class GradeForm(FlaskForm):
    score = DecimalField(
        "Note",
        validators=[DataRequired(), NumberRange(min=0, max=20)],
    )
    comment = TextAreaField(
        "Commentaire",
        validators=[Optional(), Length(max=500)],
    )
    submit = SubmitField("Enregistrer")
