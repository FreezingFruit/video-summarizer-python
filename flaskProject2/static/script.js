document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData();
    const fileInput = document.getElementById('file');
    formData.append('file', fileInput.files[0]);

    const response = await fetch('/upload', {
        method: 'POST',
        body: formData,
    });

    const result = await response.json();

    if (result.error) {
        alert(result.error);
    } else {
        const summaryDiv = document.getElementById('summary');
        summaryDiv.textContent = result.summary;
    }
});
