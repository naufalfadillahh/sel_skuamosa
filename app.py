# Impor library yang diperlukan
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
import numpy as np
# Baris ini sekarang akan berfungsi karena diinstal di dalam venv
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# --- Konfigurasi ---
# Konfigurasi folder untuk menyimpan file yang diunggah
UPLOAD_FOLDER = 'static/uploads'
# Membuat folder jika belum ada
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Definisikan ekstensi file gambar yang diizinkan
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


# --- Memuat Model ---
# Memuat model AI yang telah dilatih
# Pastikan path 'static/models/mulut_model.h5' sudah benar
try:
    model = load_model('static/models/mulut_model.h5')
    print(">>> Model berhasil dimuat.")
except Exception as e:
    print(f">>> FATAL ERROR saat memuat model: {e}")
    model = None # Menangani kasus jika model gagal dimuat


# --- Fungsi Bantuan ---
# Fungsi untuk memeriksa apakah ekstensi file diizinkan
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Fungsi untuk memproses gambar sebelum dimasukkan ke model
def preprocess_image(img_path, target_size=(128, 128)):
    # Ukuran diubah menjadi (128, 128) agar sesuai dengan input model
    img = image.load_img(img_path, target_size=target_size)
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0) # Menambah dimensi untuk batch
    img_array /= 255.0 # Normalisasi gambar
    return img_array


# --- Routes Aplikasi ---
# Route untuk halaman utama
@app.route('/')
def home():
    return render_template('index.html')

# Route untuk menerima gambar dan melakukan prediksi
@app.route('/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({'error': 'Model AI tidak dapat dimuat.'}), 500

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
            # ======================================================
            # === LOGIKA PREDIKSI YANG JAUH LEBIH SEMPURNA (DIMULAI) ===
            # ======================================================

            # a. Persiapkan gambar untuk model
            processed_image = preprocess_image(filepath)

            # b. Dapatkan skor prediksi dari model
            prediction_scores = model.predict(processed_image)
            
            # c. Ambil nilai skor mentah dari hasil prediksi
            #    Hasilnya biasanya berbentuk array seperti [[0.98]], jadi kita ambil isinya.
            raw_score = prediction_scores[0][0]

            # d. (SANGAT PENTING) Cetak skor mentah ini ke terminal Anda untuk debugging.
            #    Ini akan membantu Anda memahami apa yang sebenarnya dihasilkan model.
            print(f">>> SKOR MENTAH DARI MODEL: {raw_score:.4f}")

            # e. Definisikan ambang batas dan nama kelas
            CONFIDENCE_THRESHOLD = 0.5
            CLASS_NORMAL = "Sel Skuamosa Normal"
            CLASS_CANCER = "Sel Skuamosa Karsinoma"
            
            # f. Logika Inti: Tentukan hasil berdasarkan skor.
            #    ASUMSI UTAMA:
            #    - Skor TINGGI ( > 0.5) berarti kelas "Normal".
            #    - Skor RENDAH ( < 0.5) berarti kelas "Kanker".
            #
            #    ==> Jika ternyata model Anda kebalik (skor tinggi = kanker),
            #        cukup tukar posisi `CLASS_NORMAL` dan `CLASS_CANCER` di bawah ini.
            if raw_score > CONFIDENCE_THRESHOLD:
                final_result = CLASS_NORMAL
            else:
                final_result = CLASS_CANCER

            # g. Cetak hasil interpretasi di terminal untuk verifikasi.
            print(f">>> Hasil Interpretasi: '{final_result}'")
            
            # h. Kirim hasil final ke frontend
            return jsonify({
                'result': final_result,
                'image_url': f'/{filepath}'
            })
            
            # ====================================================
            # === LOGIKA PREDIKSI YANG DISEMPURNAKAN (SELESAI) ===
            # ====================================================

        except Exception as e:
            error_message = f"Terjadi kesalahan internal saat memproses gambar. Detail: {str(e)}"
            print(f">>> ERROR PREDIKSI: {error_message}")
            return jsonify({'error': error_message}), 500
    
    return jsonify({'error': 'Tipe file tidak valid. Harap unggah file PNG, JPG, atau JPEG.'}), 400

# Menjalankan aplikasi jika file ini dieksekusi secara langsung
if __name__ == '__main__':
    app.run(debug=True)