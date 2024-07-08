from flask import Flask, render_template, redirect, request, session, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, ForeignKey, Float, Boolean,DateTime
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired, URL, Length
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)


# CREATE DATABASE
class Base(DeclarativeBase):
    pass

UPLOAD_FOLDER = 'static/uploads'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///point.db'
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(model_class=Base)
db.init_app(app)

# CONFIGURE TABLE
class Tratamiento(db.Model):
    __tablename__ = 'tratamientos'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    precio: Mapped[int] = mapped_column(Integer, nullable=False)
    foto_tto: Mapped[str] = mapped_column(String(250), nullable=False)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)

class Patient(Base):
    __tablename__ = 'patients'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    photo_url: Mapped[str] = mapped_column(String(250), default='/static/images/profile.jpg')
    presupuestos = relationship('Presupuesto', back_populates='patient')

class Presupuesto(Base):
    __tablename__ = 'presupuestos'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey('patients.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    treatments = relationship('PresupuestoTratamiento', back_populates='presupuesto', cascade="all, delete-orphan")
    patient = relationship('Patient', back_populates='presupuestos')

class PresupuestoTratamiento(Base):
    __tablename__ = 'presupuesto_tratamientos'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    presupuesto_id: Mapped[int] = mapped_column(ForeignKey('presupuestos.id'), nullable=False)
    treatment_id: Mapped[int] = mapped_column(ForeignKey('tratamientos.id'), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    presupuesto = relationship('Presupuesto', back_populates='treatments')
    treatment = relationship('Tratamiento')

 
with app.app_context():
    db.create_all()
    
# FORM NUEVO TRATAMIENTO
class NuevoTtoForm(FlaskForm):
    nombre = StringField(label='Nombre', validators=[DataRequired()])
    descripcion = StringField(label='Descripcion', validators=[DataRequired()])
    precio = IntegerField(label='Precio', validators=[DataRequired()])
    foto_tto = StringField(label='Link de la imagen', validators=[URL()])
    submit = SubmitField(label='Agregar')
    
class NuevoPacienteForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('Teléfono', validators=[DataRequired(), Length(min=7, max=20)])
    submit = SubmitField('Agregar Paciente')


#Helpers
def save_photo(file):
    filename = secure_filename(file.filename)
    file_path = os.path.join('static', 'uploads', filename)
    file.save(file_path)
    return file_path.replace('\\', '/').replace('static/','')


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/pacientes")
def pacientes():
    pacientes = db.session.query(Patient).all()
    return render_template('pacientes.html', pacientes=pacientes)

@app.route("/paciente/<int:id>")
def paciente(id):
    paciente = db.session.get(Patient, id)
    presupuestos = db.session.query(Presupuesto).filter_by(patient_id=id).all()
    formatted_presupuestos = []
    
    
    for presupuesto in presupuestos:
        total = sum(treatment.quantity * treatment.treatment.precio for treatment in presupuesto.treatments)
        
        formatted_presupuesto = {
            "id": presupuesto.id,
            "formatted_date": presupuesto.created_at.strftime("%d-%m-%Y"),
            "treatments": presupuesto.treatments,
            "total":total,
        }
        formatted_presupuestos.append(formatted_presupuesto)

    return render_template("paciente.html", paciente=paciente, presupuestos=formatted_presupuestos)


@app.route("/nuevo_paciente", methods=["GET", "POST"])
def nuevo_paciente():
    form = NuevoPacienteForm()
    if form.validate_on_submit():
        nuevo_paciente = Patient(name=form.name.data, phone=form.phone.data)
        db.session.add(nuevo_paciente)
        db.session.commit()
        return redirect('pacientes')
    return render_template('nuevo_paciente.html', form=form)

@app.route("/editar_paciente/<int:id>", methods=["GET", "POST"])
def editar_paciente(id):
    patient = db.session.get(Patient, id)
    if patient:
        patient.name = request.form.get('name')
        patient.phone = request.form.get('phone')
        photo = request.files.get('photo')
        if photo:
            patient.photo_url = save_photo(photo)
        db.session.commit()
    return redirect(url_for('paciente', id=id))

@app.route('/tratamientos')
def tratamientos():
    todos_los_ttos = db.session.query(Tratamiento).filter_by(deleted=False).all()
    return render_template('tratamientos.html', ttos=todos_los_ttos)


@app.route("/presupuesto/<int:id>")
def presupuesto(id):
    paciente = db.get_or_404(Patient,id)
    todos_los_ttos = db.session.query(Tratamiento).filter_by(deleted=False).all()
    return render_template('presupuesto.html', ttos=todos_los_ttos, paciente=paciente)

@app.route("/emitir_presupuesto")
def emitir_presupuesto():
    return render_template('emision.html')

@app.route("/eliminar_presupuesto/<int:id>", methods=["POST"])
def eliminar_presupuesto(id):
    presupuesto_a_eliminar = db.session.get(Presupuesto, id)
    if presupuesto_a_eliminar:
        patient_id = presupuesto_a_eliminar.patient_id
        db.session.delete(presupuesto_a_eliminar)
        db.session.commit()
    return redirect(url_for('paciente', id=patient_id))

@app.route("/nuevo_tratamiento", methods=["GET", "POST"])
def nuevo_tto():
    nuevo_form = NuevoTtoForm()
    if nuevo_form.validate_on_submit():
        with app.app_context():
            nuevo_tto = Tratamiento(
                nombre=nuevo_form.nombre.data,
                descripcion=nuevo_form.descripcion.data,
                precio=nuevo_form.precio.data,
                foto_tto=nuevo_form.foto_tto.data
            )
                        
            db.session.add(nuevo_tto)
            db.session.commit()
            
            return redirect('tratamientos')
        
    return render_template('nuevo_tto.html', form=nuevo_form)



@app.route("/editar_tratamiento/<int:id>", methods=["GET", "POST"])
def editar_tto(id):
    
    tto_a_editar = db.get_or_404(Tratamiento, id)
    form = NuevoTtoForm()
    context={"tratamiento":tto_a_editar, "form":form}
    if request.method == "GET":
        return render_template('editar_tratamiento.html', **context)
    elif request.method == "POST":
        tto_a_editar.nombre = request.form.get('nombre')
        tto_a_editar.descripcion = request.form.get('descripcion')
        tto_a_editar.foto_tto = request.form.get('foto_tto')
        tto_a_editar.precio = request.form.get('precio')
        db.session.commit()
        return redirect('/tratamientos')

@app.route("/eliminar_tratamiento/<int:id>", methods=["POST"])
def eliminar_tto(id):
    tto_a_eliminar = db.get_or_404(Tratamiento, id)
    tto_a_eliminar.deleted = True
    db.session.commit()
    return redirect('/tratamientos')

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/checkout", methods=["POST"])
def checkout():
    data = request.get_json()
    patient_id = data['patientId']
    cart = data['cart']

    new_presupuesto = Presupuesto(patient_id=patient_id)
    db.session.add(new_presupuesto)
    db.session.commit()

    for item in cart:
        new_presupuesto_treatment = PresupuestoTratamiento(
            presupuesto_id=new_presupuesto.id,
            treatment_id=item['treatmentId'],
            quantity=item['quantity']
        )
        db.session.add(new_presupuesto_treatment)
    db.session.commit()
    # Generate the URL for the patient's page
    redirect_url = url_for('paciente', id=patient_id)
    
    return {"message": "Presupuesto creado con éxito", "redirect_url": redirect_url}




if __name__ == "__main__":
    app.run(debug=True, port=5216)