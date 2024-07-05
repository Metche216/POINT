from flask import Flask, render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
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
class Tratamiento(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    precio: Mapped[int] = mapped_column(String(250), nullable=False)
    foto_tto: Mapped[str] = mapped_column(String(250), nullable=False)

    
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
    else:
        return redirect('tratamientos')

if __name__ == "__main__":
    app.run(debug=True, port=5000)