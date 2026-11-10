# Impor library yang diperlukan
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
import numpy as np
import logging
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler('app.log'),
    logging.StreamHandler()
])
logger = logging.getLogger(__name__)

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# --- Konfigurasi ---
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'jpg'}

# Global model (lazy loaded)
model = None

def load_model_if_needed():
    global model
    if model is None:
        model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static/models/mulut_model_5.h5'))
        logger.info(f'Trying to load model from: {model_path}')
        try:
            model = load_model(model_path)
            logger.info(">>> Model berhasil dimuat.")
        except Exception as e:
            logger.error(f'>>> FATAL ERROR saat memuat model: {e}')
            model = None
            raise

# --- Fungsi Bantuan ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_image(img_path, target_size=(224, 224)):
    img = image.load_img(img_path, target_size=target_size)
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array /= 255.0
    return img_array

# --- Routes Aplikasi ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        load_model_if_needed()
        if model is None:
            return jsonify({'error': 'Model AI tidak dapat dimuat. Check app.log for details.'}), 500
    except Exception as e:
        return jsonify({'error': f'Model load failed: {str(e)}'}), 500

    if 'file' not in request.files:
        return jsonify({'error': 'Request tidak berisi file.'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Tidak ada file yang dipilih.'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            processed_image = preprocess_image(filepath)
            prediction_scores = model.predict(processed_image)
            raw_score = prediction_scores[0][0]
            logger.info(f'>>> SKOR MENTAH DARI MODEL: {raw_score:.4f}')

            CONFIDENCE_THRESHOLD = 0.5
            CLASS_NORMAL = "Sel Skuamosa Normal"
            CLASS_CANCER = "Sel Skuamosa Karsinoma"
            
            final_result = CLASS_CANCER if raw_score > CONFIDENCE_THRESHOLD else CLASS_NORMAL
            logger.info(f'Model input shape: {model.input_shape}')
            logger.info(f'Raw score (prob karsinoma?): {raw_score:.4f}')
            logger.info(f'>>> Hasil Interpretasi: {final_result} (threshold=0.5)')
            
            return jsonify({
                'result': final_result,
                'image_url': f'/{filepath}',
                'raw_score': float(raw_score)
            })
        except Exception as e:
            error_message = f'Terjadi kesalahan internal saat memproses gambar. Detail: {str(e)}'
            logger.error(error_message)
            return jsonify({'error': error_message}), 500
    
    return jsonify({'error': 'Tipe file tidak valid. Harap unggah JPG.'}), 400

if __name__ == '__main__':
    logger.info('Starting Flask app...')
    app.run(debug=True)