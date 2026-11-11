document.addEventListener('DOMContentLoaded', () => {
    const $ = (id) => document.getElementById(id);

    const uploadArea = $('upload-area');
    const fileInput = $('file-input');
    const placeholder = $('upload-placeholder');
    const previewBox = $('upload-preview-container');
    const previewImg = $('upload-preview-image');
    const fileName = $('file-name');

    const states = {
        initial: $('initial-state'),
        loading: $('loading-state'),
        report: $('report-state'),
        error: $('error-state'),
    };

    const MAX_SIZE = 5 * 1024 * 1024;
    const THRESHOLD = 0.5;
    const fmt = (n) => n.toFixed(2).replace('.', ',');
    let lastFile = null;
    let busy = false;

    const show = (name) => {
        Object.entries(states).forEach(([k, el]) => el.classList.toggle('hidden', k !== name));
    };

    const showError = (message) => {
        $('error-text').textContent = message;
        show('error');
    };

    // ---------- Pilih file ----------
    const openPicker = () => { if (!busy) fileInput.click(); };

    uploadArea.addEventListener('click', (e) => {
        if (uploadArea.classList.contains('has-image') && !e.target.closest('#change-image-button')) return;
        openPicker();
    });
    uploadArea.addEventListener('keydown', (e) => {
        if (e.target === uploadArea && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); openPicker(); }
    });
    fileInput.addEventListener('change', (e) => handleFile(e.target.files[0]));

    uploadArea.addEventListener('dragover', (e) => { e.preventDefault(); uploadArea.classList.add('dragover'); });
    uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        handleFile(e.dataTransfer.files[0]);
    });

    // ---------- Contoh citra ----------
    document.querySelectorAll('.sample').forEach((btn) => {
        btn.addEventListener('click', async () => {
            if (busy) return;
            try {
                const res = await fetch(btn.dataset.src);
                if (!res.ok) throw new Error();
                const blob = await res.blob();
                handleFile(new File([blob], btn.dataset.name, { type: 'image/jpeg' }));
            } catch {
                showError('Citra contoh gagal dimuat. Coba lagi.');
            }
        });
    });

    // ---------- Proses ----------
    const handleFile = (file) => {
        if (!file || busy) return;
        const isJpg = /\.(jpe?g)$/i.test(file.name) && (file.type === 'image/jpeg' || file.type === '');
        if (!isJpg) { showError('Format tidak didukung. Unggah citra berformat JPG atau JPEG.'); fileInput.value = ''; return; }
        if (file.size > MAX_SIZE) { showError('Ukuran file melebihi 5 MB.'); fileInput.value = ''; return; }

        lastFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
            fileName.textContent = file.name;
            placeholder.classList.add('hidden');
            previewBox.classList.remove('hidden');
            uploadArea.classList.add('has-image');
        };
        reader.readAsDataURL(file);

        predict(file);
    };

    const predict = async (file) => {
        busy = true;
        show('loading');
        const formData = new FormData();
        formData.append('file', file);
        try {
            const response = await fetch('/predict', { method: 'POST', body: formData });
            let data = {};
            try { data = await response.json(); } catch { /* respons bukan JSON */ }
            if (!response.ok) throw new Error(data.error || 'Terjadi kesalahan pada server.');
            displayResult(data);
        } catch (err) {
            showError(err.message || 'Tidak dapat terhubung ke server.');
        } finally {
            busy = false;
            fileInput.value = '';
        }
    };

    const displayResult = ({ result, raw_score: raw }) => {
        const score = typeof raw === 'number' ? raw : null;
        const isCancer = score !== null ? score > THRESHOLD : /karsinoma/i.test(result || '');

        $('verdict').className = 'verdict ' + (isCancer ? 'kanker' : 'normal');
        $('result-text').textContent = result || (isCancer ? 'Sel Skuamosa Karsinoma' : 'Sel Skuamosa Normal');

        $('score-block').classList.toggle('hidden', score === null);
        if (score !== null) {
            $('score-value').textContent = fmt(score);
            const fill = $('meter-fill');
            fill.style.width = '0%';
            requestAnimationFrame(() => requestAnimationFrame(() => { fill.style.width = Math.max(2, score * 100) + '%'; }));
        }

        $('recommendation-text').textContent = isCancer
            ? 'Citra menunjukkan ciri karsinoma sel skuamosa. Disarankan segera berkonsultasi dengan dokter spesialis untuk pemeriksaan lanjutan dan validasi histopatologi.'
            : 'Tidak terdeteksi ciri karsinoma pada citra ini. Tetap lakukan pemeriksaan rutin dan konsultasikan ke dokter bila ada keluhan pada rongga mulut.';

        show('report');
        if (window.innerWidth < 900) document.querySelector('.result-panel').scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    // ---------- Reset ----------
    const resetUI = () => {
        fileInput.value = '';
        lastFile = null;
        previewImg.removeAttribute('src');
        fileName.textContent = '';
        placeholder.classList.remove('hidden');
        previewBox.classList.add('hidden');
        uploadArea.classList.remove('has-image');
        show('initial');
    };

    $('new-analysis-button').addEventListener('click', resetUI);
    $('retry-button').addEventListener('click', () => { if (lastFile) predict(lastFile); else resetUI(); });
});
