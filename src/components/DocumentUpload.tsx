import React, { useState, useEffect } from 'react';
import { UploadCloud, FileText, CheckCircle2, XCircle, UserPlus, AlertCircle } from 'lucide-react';
import { api } from '../api';

export default function DocumentUpload() {
    const [uploadFile, setUploadFile] = useState<File | null>(null);
    const [uploadResult, setUploadResult] = useState<any>(null);
    const [extractedData, setExtractedData] = useState<any>(null);
    const [toastMessage, setToastMessage] = useState<string | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const [showRegistration, setShowRegistration] = useState(false);
    const [regMrn, setRegMrn] = useState('');
    const [regName, setRegName] = useState('');
    const [isRegistering, setIsRegistering] = useState(false);

    const handleRegisterAndAssign = async () => {
        try {
            setIsRegistering(true);
            setToastMessage("Registering patient...");
            await api.registerPatient(regMrn, regName);
            setToastMessage("Patient registered. Assigning document...");
            const res = await api.assignPatientToDocument(uploadResult.documentId, regMrn);
            setUploadResult(res);
            setShowRegistration(false);
            setToastMessage("Document processed and attached.");
        } catch(e: any) {
            setToastMessage(e.message || "Registration failed.");
        } finally {
            setIsRegistering(false);
        }
    };

    useEffect(() => {
        if (toastMessage) {
            const timer = setTimeout(() => setToastMessage(null), 3000);
            return () => clearTimeout(timer);
        }
    }, [toastMessage]);


    useEffect(() => {
        if (uploadResult && uploadResult.needsReview) {
            let extracted = "";
            if (uploadResult.extractedMrns && uploadResult.extractedMrns.length > 0) {
                extracted = uploadResult.extractedMrns[0];
            } else if (uploadResult.extractedText) {
                extracted = uploadResult.extractedText;
            }
            setRegMrn(extracted);
            setRegName("Unknown Patient");
        }
    }, [uploadResult]);

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
                    <div className="mt-6 bg-amber-50/80 border border-amber-300 rounded-xl p-5 flex flex-col gap-4">
                        <div className="flex items-start gap-3">
                            <div className="w-6 h-6 text-amber-600 mt-0.5 shrink-0"><AlertCircle /></div>
                            <div>
                                <strong className="text-amber-900 block font-bold text-lg">Action Required</strong>
                                <p className="text-sm text-amber-800 mt-0.5">
                                    {uploadResult.reason || "Patient identifier could not be confidently matched."}
                                </p>
                            </div>
                        </div>

                        {!showRegistration ? (
                            <div className="pl-9 flex gap-3">
                                <button onClick={() => setShowRegistration(true)} className="bg-amber-100 hover:bg-amber-200 text-amber-900 border border-amber-300 px-4 py-2 rounded-lg font-semibold text-sm transition-colors flex items-center gap-2">
                                    <UserPlus className="w-4 h-4" /> Patient Not Found — Register Patient
                                </button>
                            </div>
                        ) : (
                            <div className="pl-9 mt-2 bg-white rounded-xl border border-amber-200 p-4 shadow-sm animate-in fade-in slide-in-from-top-2">
                                <h4 className="font-semibold text-slate-800 mb-3 border-b border-slate-100 pb-2">Manual Registration</h4>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1">Medical Record Number (MRN)</label>
                                        <input type="text" value={regMrn} onChange={e => setRegMrn(e.target.value)} className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:border-teal-500 focus:ring-1 focus:ring-teal-500 outline-none" placeholder="MRN-XXXX" />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1">Patient Full Name</label>
                                        <input type="text" value={regName} onChange={e => setRegName(e.target.value)} className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:border-teal-500 focus:ring-1 focus:ring-teal-500 outline-none" placeholder="John Doe" />
                                    </div>
                                </div>
                                <div className="mt-4 flex justify-end gap-2">
                                    <button onClick={() => setShowRegistration(false)} className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-900">Cancel</button>
                                    <button onClick={handleRegisterAndAssign} disabled={isRegistering || regMrn.length < 4 || regName.length < 2} className="px-4 py-2 text-sm font-bold bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white rounded-lg transition-colors">
                                        {isRegistering ? "Saving..." : "Register & Link Document"}
                                    </button>
                                </div>
                            </div>
                        )}
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
