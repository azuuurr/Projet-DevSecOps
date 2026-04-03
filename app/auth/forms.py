from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField(
        "Nom d'utilisateur",
        validators=[DataRequired(), Length(min=3, max=80)],
    )
    password = PasswordField(
        "Mot de passe",
        validators=[DataRequired(), Length(min=6, max=128)],
    )
    submit = SubmitField("Se connecter")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(
        "Mot de passe actuel",
        validators=[DataRequired()],
    )
    new_password = PasswordField(
        "Nouveau mot de passe",
        validators=[DataRequired(), Length(min=6, max=128)],
    )
    confirm_password = PasswordField(
        "Confirmer le nouveau mot de passe",
        validators=[DataRequired(), Length(min=6, max=128)],
    )
    submit = SubmitField("Changer le mot de passe")
