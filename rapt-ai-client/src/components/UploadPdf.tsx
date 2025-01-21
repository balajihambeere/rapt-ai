'use client';
import React, { useState } from 'react';
import { useUploadPdfMutation } from '../lib/apiSlice';

const UploadPdf: React.FC = () => {
    const [file, setFile] = useState<File | null>(null);
    const [uploadPdf, { isLoading, isError, isSuccess }] = useUploadPdfMutation();

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = event.target.files?.[0];
        if (selectedFile && selectedFile.type === 'application/pdf') {
            setFile(selectedFile);
        } else {
            alert('Please select a valid PDF file.');
        }
    };

    const handleUpload = async () => {
        if (file) {
            const formData = new FormData();
            formData.append('file', file);

            try {
                await uploadPdf(formData).unwrap();
                alert('File uploaded successfully!');
            } catch (error) {
                console.error('Upload failed:', error);
                alert('File upload failed!');
            }
        } else {
            alert('Please select a file first.');
        }
    };

    return (
        <div>
            <h1>Upload PDF</h1>
            <input type="file" accept="application/pdf" onChange={handleFileChange} />
            <button onClick={handleUpload} disabled={isLoading}>
                {isLoading ? 'Uploading...' : 'Upload'}
            </button>
            {isError && <p style={{ color: 'red' }}>An error occurred while uploading.</p>}
            {isSuccess && <p style={{ color: 'green' }}>File uploaded successfully!</p>}
        </div>
    );
};

export default UploadPdf;
