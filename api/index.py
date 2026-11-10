"""Versi Vercel dari app.py.

TensorFlow terlalu besar untuk Vercel, jadi model mulut_model_5.h5 dikonversi ke
mulut_model_5.tflite (float16) dan dijalankan dengan LiteRT. Pra-pemrosesan dan
ambang batas sama persis dengan app.py: resize 224x224 (nearest, seperti
keras load_img), dibagi 255, skor > 0.5 = Karsinoma.
"""
import io
import os

import numpy as np
from ai_edge_litert.interpreter import Interpreter
from flask import Flask, jsonify, render_template, request
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(ROOT, "static", "models", "mulut_model_5.tflite")
ALLOWED_EXTENSIONS = {"jpg", "jpeg"}
CONFIDENCE_THRESHOLD = 0.5
CLASS_NORMAL = "Sel Skuamosa Normal"
CLASS_CANCER = "Sel Skuamosa Karsinoma"

app = Flask(
    __name__,
    template_folder=os.path.join(ROOT, "templates"),
    static_folder=os.path.join(ROOT, "static"),
)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

_interp = None


def get_interpreter():
    global _interp
    if _interp is None:
        _interp = Interpreter(model_path=MODEL_PATH)
        _interp.allocate_tensors()
    return _interp


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def preprocess(data):
    img = Image.open(io.BytesIO(data)).convert("RGB").resize((224, 224), Image.NEAREST)
    return (np.asarray(img, dtype=np.float32) / 255.0)[None, ...]


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "Request tidak berisi file."}), 400
    if file.filename == "":
        return jsonify({"error": "Tidak ada file yang dipilih."}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Tipe file tidak valid. Harap unggah JPG."}), 400
    try:
        interp = get_interpreter()
        inp = interp.get_input_details()[0]
        out = interp.get_output_details()[0]
        interp.set_tensor(inp["index"], preprocess(file.read()))
        interp.invoke()
        raw_score = float(interp.get_tensor(out["index"])[0][0])
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": f"Terjadi kesalahan internal saat memproses gambar. Detail: {e}"}), 500

    result = CLASS_CANCER if raw_score > CONFIDENCE_THRESHOLD else CLASS_NORMAL
    return jsonify({"result": result, "raw_score": raw_score})
