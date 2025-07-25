document.addEventListener('DOMContentLoaded', () => {
    // Referensi elemen panel unggah
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const uploadPlaceholder = document.getElementById('upload-placeholder');
    const uploadPreviewContainer = document.getElementById('upload-preview-container');
    const uploadPreviewImage = document.getElementById('upload-preview-image');
    const changeImageButton = document.getElementById('change-image-button');

    // Referensi elemen panel hasil
    const resultArea = document.getElementById('result-area');
    const initialState = document.getElementById('initial-state');
    const loadingState = document.getElementById('loading-state');
    const reportState = document.getElementById('report-state');
    const resultText = document.getElementById('result-text');
    const newAnalysisButton = document.getElementById('new-analysis-button');

    // Fungsi untuk menampilkan status tertentu di panel hasil
    const showResultState = (state) => {
        initialState.classList.add('hidden');
        loadingState.classList.add('hidden');
        reportState.classList.add('hidden');
        if (state === 'loading') {
            loadingState.classList.remove('hidden');
        } else if (state === 'report') {
            reportState.classList.remove('hidden');
        } else { // 'initial'
            initialState.classList.remove('hidden');
        }
    };

    // --- LOGIKA UNGGAH ---
    uploadArea.addEventListener('click', (e) => {
        // Hanya trigger klik file input jika placeholder yang diklik
        if (e.target.closest('#upload-placeholder') || e.target.closest('#change-image-button')) {
            fileInput.click();
        }
    });

    fileInput.addEventListener('change', (e) => handleFile(e.target.files[0]));

    // Logika Drag and Drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        handleFile(e.dataTransfer.files[0]);
    });
    
    // --- FUNGSI UTAMA UNTUK MENANGANI FILE ---
    const handleFile = (file) => {
        if (!file) return;

        // Validasi tipe file
        const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg'];
        if (!allowedTypes.includes(file.type)) {
            alert('Tipe file tidak valid. Harap unggah file PNG, JPG, atau JPEG.');
            return;
        }

        // Tampilkan pratinjau gambar di panel kiri
        const reader = new FileReader();
        reader.onload = (e) => {
            uploadPreviewImage.src = e.target.result;
            uploadPlaceholder.classList.add('hidden');
            uploadPreviewContainer.classList.remove('hidden');
        };
        reader.readAsDataURL(file);

        // Tampilkan status loading di panel kanan dan mulai prediksi
        showResultState('loading');
        uploadAndPredict(file);
    };

    // --- FUNGSI UNTUK MENGIRIM FILE & PREDIKSI ---
    const uploadAndPredict = async (file) => {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/predict', { method: 'POST', body: formData });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Terjadi kesalahan pada server.');
            
            // Tampilkan hasil setelah prediksi selesai
            displayResult(data.result);
        } catch (error) {
            displayResult(error.message, true);
        }
    };

    // --- FUNGSI UNTUK MENAMPILKAN HASIL ---
    const displayResult = (result, isError = false) => {
        resultText.textContent = result;
        resultText.className = 'result-text-placeholder'; // Reset class
        if (isError) {
            resultText.classList.add('kanker');
        } else if (result.toLowerCase().includes('kanker')) {
            resultText.classList.add('kanker');
        } else {
            resultText.classList.add('normal');
        }
        showResultState('report');
    };

    // --- FUNGSI UNTUK MERESET SEMUA UI ---
    const resetUI = () => {
        // Reset panel unggah
        fileInput.value = '';
        uploadPlaceholder.classList.remove('hidden');
        uploadPreviewContainer.classList.add('hidden');
        uploadPreviewImage.src = '#';
        
        // Reset panel hasil
        showResultState('initial');
    };

    newAnalysisButton.addEventListener('click', resetUI);
});
