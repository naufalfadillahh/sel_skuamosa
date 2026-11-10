# Klasifikasi Sel Karsinoma Skuamosa Rongga Mulut dengan CNN

Aplikasi web skripsi untuk mengklasifikasikan citra sel rongga mulut menjadi **sel skuamosa normal** atau **karsinoma sel skuamosa** menggunakan Convolutional Neural Network (CNN).

**Demo live:** https://sel-skuamosa-naufal.vercel.app

## Cara kerja

1. Pengguna mengunggah citra JPG.
2. Citra diubah ke 224×224 piksel dan dinormalisasi (dibagi 255).
3. Model CNN menghasilkan skor 0–1. Skor di atas 0,5 diklasifikasikan sebagai karsinoma.

Contoh citra untuk dicoba ada di `static/samples/`.

## Struktur

| File | Fungsi |
|---|---|
| `app.py` | Aplikasi Flask untuk dijalankan lokal dengan TensorFlow (`mulut_model_5.h5`) |
| `api/index.py` | Versi untuk Vercel: model yang sama dalam format TFLite (`mulut_model_5.tflite`, float16) dijalankan dengan LiteRT, karena TensorFlow melebihi batas ukuran Vercel |
| `static/models/` | Model Keras asli dan hasil konversi TFLite |
| `templates/`, `static/` | Antarmuka web |

Hasil konversi TFLite sudah dibandingkan dengan model Keras pada 26 citra contoh: seluruhnya menghasilkan kelas yang sama (selisih skor maksimum 0,023).

## Menjalankan lokal

```bash
pip install -r requirements.txt
python app.py
```
