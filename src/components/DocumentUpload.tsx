import React, { useState, useEffect } from 'react';
import { UploadCloud, FileText, CheckCircle2, XCircle } from 'lucide-react';
import { api } from '../api';

export default function DocumentUpload() {
    const [uploadFile, setUploadFile] = useState<File | null>(null);
    const [uploadResult, setUploadResult] = useState<any>(null);
    const [extractedData, setExtractedData] = useState<any>(null);
    const [toastMessage, setToastMessage] = useState<string | null>(null);
    const [isUploading, setIsUploading] = useState(false);

    useEffect(() => {
        if (toastMessage) {
            const timer = setTimeout(() => setToastMessage(null), 3000);
            return () => clearTimeout(timer);
        }
    }, [toastMessage]);

    useEffect(() => {
        if (uploadResult && !uploadResult.needsReview && uploadResult.documentId) {
            api.getExtraction(uploadResult.documentId)
                .then(data => setExtractedData(data))
                .catch(e => console.error(e));
        } else {
            setExtractedData(null);
        }
    }, [uploadResult]);

    const handleUpload = async () => {
        if (!uploadFile) return;
        try {
            setIsUploading(true);
            setToastMessage("Uploading document...");
            const res = await api.uploadDoc(uploadFile);
            setUploadResult(res);
            setToastMessage("Document uploaded successfully.");
            setUploadFile(null);
        } catch (e: any) {
            setToastMessage(e.message || "Uploading failed.");
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 relative">
            {/* Toast Notification */}
            {toastMessage && (
                <div className="fixed bottom-4 right-4 bg-teal-600 text-white px-6 py-3 rounded-xl shadow-lg font-medium flex items-center gap-2 z-50 animate-in slide-in-from-bottom-8">
                    <CheckCircle2 className="w-5 h-5" />
                    {toastMessage}
                </div>
            )}

            <div>
                <h2 className="text-2xl font-semibold text-slate-800">Document Upload</h2>
                <p className="text-slate-500 mt-1">Upload discharge summaries for automated intelligence routing.</p>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
                <h3 className="text-sm font-semibold text-slate-800 uppercase tracking-wider mb-4">Select File</h3>
                <div className="border-2 border-dashed border-slate-200 rounded-xl p-8 flex flex-col items-center justify-center text-center transition-colors hover:border-teal-400 hover:bg-teal-50/50">
                    <input
                        type="file"
                        id="file-upload"
                        className="hidden"
                        accept=".pdf,.doc,.docx,.xls,.xlsx"
                        onChange={(e) => {
                            if (e.target.files && e.target.files[0]) {
                                setUploadFile(e.target.files[0]);
                            }
                        }}
                    />
                    <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center gap-3">
                        <div className="w-12 h-12 bg-teal-100 text-teal-600 rounded-full flex items-center justify-center">
                            <UploadCloud className="w-6 h-6" />
                        </div>
                        <div>
                            <span className="text-teal-600 font-medium">Click to upload</span> or drag and drop
                            <p className="text-xs text-slate-400 mt-1">Supported formats: PDF, DOCX, XLSX (Max 10MB)</p>
                        </div>
                    </label>
                </div>

                {uploadFile && (
                    <div className="mt-4 bg-slate-50 border border-slate-200 rounded-xl p-4 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center border border-slate-200 text-teal-600">
                                <FileText className="w-5 h-5" />
                            </div>
                            <div className="text-left">
                                <p className="font-medium text-slate-800 text-sm">{uploadFile.name}</p>
                                <p className="text-xs text-slate-500">{(uploadFile.size / 1024 / 1024).toFixed(2)} MB</p>
                            </div>
                        </div>
                        <button
                            onClick={() => setUploadFile(null)}
                            className="text-slate-400 hover:text-red-500 transition-colors p-2"
                        >
                            <XCircle className="w-5 h-5" />
                        </button>
                    </div>
                )}

                <div className="flex justify-end pt-4">
                    <button
                        onClick={handleUpload}
                        disabled={!uploadFile || isUploading}
                        className="bg-teal-600 hover:bg-teal-700 text-white px-6 py-2.5 rounded-xl font-medium transition-colors disabled:opacity-50"
                    >
                        {isUploading ? "Uploading..." : "Upload Document"}
                    </button>
                </div>

                {/* Upload Success Block */}
                {uploadResult && !uploadResult.needsReview && (
                    <div className="mt-6 bg-emerald-50/80 border border-emerald-200 rounded-xl p-4 flex items-start gap-3">
                        <CheckCircle2 className="w-5 h-5 text-emerald-600 mt-0.5" />
                        <div>
                            <strong className="text-emerald-900 block font-medium">Successfully Processed</strong>
                            <div className="text-xs text-emerald-800 font-medium pl-1 mt-1">
                                Document mapped to Patient: <strong>{uploadResult.patientName}</strong>
                            </div>
                        </div>
                    </div>
                )}

                {/* Upload Needs Review Block */}
                {uploadResult && uploadResult.needsReview && (
                    <div className="mt-6 bg-red-50/80 border border-red-300 rounded-xl p-4 flex flex-col gap-2">
                        <div className="flex items-start gap-3">
                            <div className="w-5 h-5 text-red-600 mt-0.5 shrink-0">⚠️</div>
                            <div>
                                <strong className="text-red-900 block font-medium">Needs Manual Correction</strong>
                                <p className="text-xs text-red-800 mt-0.5">
                                    The document intelligence module encountered an exception or mismatched data.
                                </p>
                            </div>
                        </div>
                        <div className="mt-2 text-xs bg-white/60 p-3 rounded-lg text-red-900 font-mono border border-red-200">
                            <strong className="block mb-1">Reason:</strong>
                            {uploadResult.reason || "Patient identifier could not be confidently matched."}
                        </div>
                    </div>
                )}

                {/* Extraction UI Block */}
                {extractedData && (
                    <div className="mt-6 border border-teal-200 rounded-xl overflow-hidden bg-white shadow-sm">
                        <div className="bg-teal-50 px-4 py-3 font-semibold text-teal-900 border-b border-teal-200 flex items-center gap-2">
                            <UploadCloud className="w-4 h-4 text-teal-600" /> Document Intelligence Extraction
                        </div>
                        <div className="p-4 space-y-4 text-sm text-slate-700">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                                    <strong className="text-slate-900 block text-xs uppercase tracking-wider mb-1">MRN</strong>
                                    {extractedData.patient_mrn || 'N/A'}
                                </div>
                                <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                                    <strong className="text-slate-900 block text-xs uppercase tracking-wider mb-1">Discharge Date</strong>
                                    {extractedData.discharge_date || 'N/A'}
                                </div>
                            </div>

                            {extractedData.follow_ups && extractedData.follow_ups.length > 0 && (
                                <div className="mt-4">
                                    <strong className="text-slate-900 block mb-2">Follow-ups:</strong>
                                    <ul className="grid gap-2">
                                        {extractedData.follow_ups.map((f: any, i: number) => (
                                            <li key={'f' + i} className="bg-white border border-slate-200 rounded-lg p-3 flex items-start gap-2 shadow-sm">
                                                <div className="w-2 h-2 mt-1.5 rounded-full bg-teal-400"></div>
                                                <div>
                                                    <span className="font-semibold text-teal-800">{f.specialty}</span>
                                                    <span className="text-slate-500 ml-2">({f.appointment_date})</span>
                                                    <p className="text-slate-600 mt-0.5">{f.instruction}</p>
                                                </div>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {extractedData.medication_instructions && extractedData.medication_instructions.length > 0 && (
                                <div className="mt-4">
                                    <strong className="text-slate-900 block mb-2">Medications:</strong>
                                    <ul className="grid gap-2">
                                        {extractedData.medication_instructions.map((m: any, i: number) => (
                                            <li key={'m' + i} className="bg-white border border-slate-200 rounded-lg p-3 flex items-start gap-2 shadow-sm">
                                                <div className="w-2 h-2 mt-1.5 rounded-full bg-indigo-400"></div>
                                                <div>
                                                    <span className="font-semibold text-indigo-800">{m.medication_name}</span>
                                                    <p className="text-slate-600 mt-0.5">{m.instruction}</p>
                                                </div>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {extractedData.source_evidence && extractedData.source_evidence.length > 0 && (
                                <div className="mt-6 pt-4 border-t border-slate-100">
                                    <strong className="text-slate-500 block mb-2 text-xs uppercase tracking-wider flex items-center gap-1">
                                        Source Evidence Snippet
                                    </strong>
                                    <div className="bg-slate-50 p-3 rounded-lg text-xs italic text-slate-600 border border-slate-200 whitespace-pre-wrap">
                                        "{extractedData.source_evidence[0]?.extracted_text}"
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
