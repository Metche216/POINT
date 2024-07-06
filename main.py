from flask import Flask, render_template, redirect, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, ForeignKey, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired, URL


app = Flask(__name__)


# CREATE DATABASE
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

db = SQLAlchemy(model_class=Base)
db.init_app(app)

# CONFIGURE TABLE
class Tratamiento(Base):
    __tablename__ = 'tratamientos'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    precio: Mapped[float] = mapped_column(Float, nullable=False)
    foto_tto: Mapped[str] = mapped_column(String(250), nullable=False)
    presupuestos = relationship('Presupuesto', back_populates='treatment')

class Patient(Base):
    __tablename__ = 'patients'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    presupuestos = relationship('Presupuesto', back_populates='patient')

class Presupuesto(Base):
    __tablename__ = 'presupuestos'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey('patients.id'), nullable=False)
    treatment_id: Mapped[int] = mapped_column(ForeignKey('tratamientos.id'), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    patient = relationship('Patient', back_populates='presupuestos')
    treatment = relationship('Tratamiento', back_populates='presupuestos')

    
with app.app_context():
    db.create_all()
    
# FORM NUEVO TRATAMIENTO
class NuevoTtoForm(FlaskForm):
    nombre = StringField(label='Nombre', validators=[DataRequired()])
    descripcion = StringField(label='Descripcion', validators=[DataRequired()])
    precio = IntegerField(label='Precio', validators=[DataRequired()])
    foto_tto = StringField(label='Link de la imagen', validators=[URL()])
    submit = SubmitField(label='Agregar')
    
    


@app.route("/")
def home():
    return render_template("index.html")

@app.route('/tratamientos')
def tratamientos():
    todos_los_ttos = db.session.execute(db.select(Tratamiento)).scalars().all()
    return render_template('tratamientos.html', ttos=todos_los_ttos)

@app.route("/nuevo_tratamiento", methods=["GET", "POST"])
def nuevo_tto():
    if request.method == "POST":
        with app.app_context():
            nuevo_tto = Tratamiento(
                nombre=request.form.get('nombre'),
                descripcion=request.form.get('descripcion'),
                precio=request.form.get('precio'),
                foto_tto=request.form.get('foto_tto')
            )
                        
            db.session.add(nuevo_tto)
            db.session.commit()
            
            return redirect('tratamientos')
        
    else:
        nuevo_form = NuevoTtoForm()
   
    return render_template('nuevo_tto.html', form=nuevo_form)



@app.route("/editar_tratamiento/<int:id>", methods=["GET", "POST"])
def editar_tto(id):
    
    tto_a_editar = db.get_or_404(Tratamiento, id)
    print(tto_a_editar)
    form = NuevoTtoForm()
    context={"tratamiento":tto_a_editar, "form":form}
    if request.method == "GET":
        return render_template('editar_tratamiento.html', **context)
    elif request.method == "POST":
        tto_a_editar.nombre = request.form.get('nombre')
        tto_a_editar.descripcion = request.form.get('descripcion')
        tto_a_editar.precio = request.form.get('precio')
        db.session.commit()
        return redirect('/tratamientos')

@app.route('/checkout', methods=['POST'])
def checkout():
    data = request.get_json()
    cart = data['cart']
    patient_id = data['patientId']
    
    for item in cart:
        new_treatment = Presupuesto(
            patient_id=patient_id,
            treatment_id=item['treatmentId'],
            quantity=item['quantity']
        )
        db.session.add(new_treatment)
    
    db.session.commit()

    budget_id = db.session.query(Presupuesto.id).filter_by(patient_id=patient_id).first()[0]

    return jsonify({'budget_id': budget_id})



if __name__ == "__main__":
    app.run(debug=True, port=5000)