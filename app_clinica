import os
from datetime import datetime, timezone

import click
from flask import Flask, abort, flash, redirect, render_template, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy import select
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length

db = SQLAlchemy()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address, default_limits=[])


class Clinic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(240), nullable=False)
    opening_hours = db.Column(db.String(160), nullable=False)


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500), nullable=False, default="")
    active = db.Column(db.Boolean, nullable=False, default=True)


class QuickReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(500), nullable=False)


class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="scrypt")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class LoginForm(FlaskForm):
    username = StringField("Usuário", validators=[DataRequired(), Length(max=80)])
    password = PasswordField("Senha", validators=[DataRequired(), Length(max=200)])
    submit = SubmitField("Entrar")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Admin, int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    flash("Entre na área administrativa para continuar.", "info")
    return redirect(url_for("login"))


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-change-this-key"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///clinica.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "0") == "1",
        WTF_CSRF_TIME_LIMIT=3600,
        CLINIC_WHATSAPP=os.getenv("CLINIC_WHATSAPP", ""),
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self'; img-src 'self' data:; form-action 'self'; frame-ancestors 'none'",
        )
        return response

    @app.get("/")
    def home():
        clinic = db.session.execute(select(Clinic).order_by(Clinic.id)).scalars().first()
        return render_template("home.html", clinic=clinic)

    @app.get("/servicos")
    def services():
        service_list = db.session.execute(
            select(Service).where(Service.active.is_(True)).order_by(Service.name)
        ).scalars().all()
        return render_template(
            "services.html", services=service_list, whatsapp=app.config["CLINIC_WHATSAPP"]
        )

    @app.route("/admin/entrar", methods=["GET", "POST"])
    @limiter.limit("5 per minute")
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("admin"))
        form = LoginForm()
        if form.validate_on_submit():
            admin = db.session.execute(
                select(Admin).where(Admin.username == form.username.data.strip())
            ).scalar_one_or_none()
            if admin and admin.check_password(form.password.data):
                login_user(admin, remember=False)
                flash("Acesso autorizado.", "success")
                return redirect(url_for("admin"))
            flash("Usuário ou senha não conferem.", "error")
        return render_template("login.html", form=form)

    @app.get("/admin")
    @login_required
    def admin():
        replies = db.session.execute(select(QuickReply).order_by(QuickReply.title)).scalars().all()
        return render_template("admin.html", replies=replies)

    @app.post("/admin/sair")
    @login_required
    def logout():
        logout_user()
        flash("Você saiu da área administrativa.", "info")
        return redirect(url_for("home"))

    @app.cli.command("init-db")
    def init_db_command():
        """Cria as tabelas do banco configurado."""
        db.create_all()
        click.echo("Tabelas criadas.")

    @app.cli.command("create-admin")
    @click.option("--username", prompt="Usuário administrador")
    @click.password_option()
    def create_admin_command(username, password):
        """Cria um administrador sem armazenar a senha em texto simples."""
        if len(password) < 12:
            raise click.ClickException("Use uma senha com pelo menos 12 caracteres.")
        if db.session.execute(select(Admin).where(Admin.username == username)).scalar_one_or_none():
            raise click.ClickException("Esse usuário já existe.")
        admin_user = Admin(username=username)
        admin_user.set_password(password)
        db.session.add(admin_user)
        db.session.commit()
        click.echo("Administrador criado.")

    @app.cli.command("seed-demo")
    def seed_demo_command():
        """Insere conteúdo fictício para visualizar o protótipo local."""
        if not db.session.execute(select(Clinic)).scalars().first():
            db.session.add(Clinic(
                name="Clínica de Estética Nathaly Farias",
                address="Rua das Acácias, 145 — Centro (endereço fictício)",
                opening_hours="Segunda a sexta, das 9h às 18h (horário demonstrativo)",
            ))
        if not db.session.execute(select(Service)).scalars().first():
            db.session.add_all([
                Service(name="Limpeza de pele", description="Descrição demonstrativa do serviço."),
                Service(name="Drenagem linfática", description="Descrição demonstrativa do serviço."),
            ])
        if not db.session.execute(select(QuickReply)).scalars().first():
            db.session.add(QuickReply(
                title="Informações iniciais",
                message="Olá! Obrigada pelo contato. Consulte nossos serviços e horários.",
            ))
        db.session.commit()
        click.echo("Conteúdo demonstrativo criado.")

    return app
