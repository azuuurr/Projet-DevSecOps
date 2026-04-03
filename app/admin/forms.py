from flask_wtf import FlaskForm
from wtforms import (
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
    TimeField,
)
from wtforms.validators import DataRequired, Email, Length, Optional


class UserForm(FlaskForm):
    username = StringField(
        "Nom d'utilisateur",
        validators=[DataRequired(), Length(min=3, max=80)],
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email(), Length(max=120)],
    )
    password = PasswordField(
        "Mot de passe",
        validators=[Optional(), Length(min=6, max=128)],
    )
    first_name = StringField(
        "Prénom",
        validators=[DataRequired(), Length(max=80)],
    )
    last_name = StringField(
        "Nom",
        validators=[DataRequired(), Length(max=80)],
    )
    role = SelectField(
        "Rôle",
        choices=[("admin", "Administrateur"), ("professor", "Professeur"), ("student", "Étudiant")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Enregistrer")


class ClassForm(FlaskForm):
    name = StringField(
        "Nom de la classe",
        validators=[DataRequired(), Length(max=100)],
    )
    description = TextAreaField(
        "Description",
        validators=[Optional(), Length(max=500)],
    )
    submit = SubmitField("Enregistrer")


class AssignStudentsForm(FlaskForm):
    students = SelectMultipleField(
        "Étudiants",
        coerce=int,
        validators=[],
    )
    submit = SubmitField("Attribuer")


class AssignProfessorsForm(FlaskForm):
    professors = SelectMultipleField(
        "Professeurs",
        coerce=int,
        validators=[],
    )
    submit = SubmitField("Attribuer")


class ScheduleForm(FlaskForm):
    subject_id = SelectField(
        "Matière",
        coerce=int,
        validators=[DataRequired()],
    )
    day_of_week = SelectField(
        "Jour",
        choices=[
            ("Lundi", "Lundi"),
            ("Mardi", "Mardi"),
            ("Mercredi", "Mercredi"),
            ("Jeudi", "Jeudi"),
            ("Vendredi", "Vendredi"),
        ],
        validators=[DataRequired()],
    )
    start_time = TimeField("Heure de début", validators=[DataRequired()])
    end_time = TimeField("Heure de fin", validators=[DataRequired()])
    room = StringField("Salle", validators=[Optional(), Length(max=50)])
    submit = SubmitField("Enregistrer")


class SubjectForm(FlaskForm):
    name = StringField(
        "Nom de la matière",
        validators=[DataRequired(), Length(max=100)],
    )
    professor_id = SelectField(
        "Professeur",
        coerce=int,
        validators=[DataRequired()],
    )
    submit = SubmitField("Enregistrer")
