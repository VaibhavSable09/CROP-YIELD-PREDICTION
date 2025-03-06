import os
import logging
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, login_manager
from models import User, Prediction
from forms import RegistrationForm, LoginForm
from utils import load_models, predict_yield, get_crop_info, get_fertilizer_info, get_pesticide_info

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "your-secret-key-here")

# Database configuration - MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://root:rOOT@localhost/cropyield"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

# Load ML models and encoders
try:
    rf_model, xgb_model, scaler = load_models()
    logger.info("✅ Models loaded successfully")
except Exception as e:
    logger.error(f"❌ Error loading models: {e}")
    rf_model = xgb_model = scaler = None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            full_name=form.full_name.data,
            contact=form.contact.data
        )
        user.set_password(form.password.data)

        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Email may already be registered.', 'danger')
            logger.error(f"Registration error: {e}")

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        flash('Invalid email or password', 'danger')

    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    if request.method == 'POST':
        try:
            # Get form data
            data = {
                'crop': request.form['crop'],
                'region': request.form['region'],
                'soil_ph': float(request.form['soil_ph']),
                'nitrogen': int(request.form['nitrogen']),
                'phosphorus': int(request.form['phosphorus']),
                'potassium': int(request.form['potassium']),
                'temperature': float(request.form['temperature']),
                'humidity': float(request.form['humidity']),
                'rainfall': float(request.form['rainfall'])
            }

            # Validate input ranges
            if not (0 <= data['soil_ph'] <= 14):
                flash('Soil pH must be between 0 and 14', 'danger')
                return render_template('predict.html')

            if not (0 <= data['humidity'] <= 100):
                flash('Humidity must be between 0 and 100%', 'danger')
                return render_template('predict.html')

            # Get predictions
            prediction_result = predict_yield(data, rf_model, xgb_model, scaler)

            # Save prediction to database
            prediction = Prediction(
                user_id=current_user.id,
                **data,
                predicted_yield=prediction_result['yield']
            )
            db.session.add(prediction)
            db.session.commit()

            # Get additional information
            crop_info = get_crop_info(data['crop'])
            fertilizer_info = get_fertilizer_info(data['crop'])
            pesticide_info = get_pesticide_info(data['crop'])

            return render_template('results.html',
                                prediction=prediction_result,
                                crop_info=crop_info,
                                fertilizer_info=fertilizer_info,
                                pesticide_info=pesticide_info,
                                input_data=data)

        except ValueError as e:
            flash('Please enter valid numerical values for all fields', 'danger')
            return render_template('predict.html')
        except Exception as e:
            logger.error(f"❌ Prediction error: {e}")
            flash('An error occurred while processing your request. Please try again.', 'danger')
            return render_template('predict.html')

    # Get user's prediction history
    predictions = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.timestamp.desc()).limit(5).all()
    return render_template('predict.html', predictions=predictions)

# Create all database tables
with app.app_context():
    try:
        db.create_all()
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Error creating database tables: {e}")

if __name__ == '__main__':
    # Ensure all required directories exist
    for directory in ['static/images', 'MODEL', 'instance']:
        os.makedirs(directory, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)