import re

with open('src/pages/DoctorDashboard.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

old_ext = """                  <strong className="text-slate-700 block">Extracted Sentence from EHR Document:</strong>
                  <div className="mt-1 font-mono text-slate-800 bg-white p-2 rounded border border-slate-200">
                    "{selectedReviewItem.extractedText}"
                  </div>"""

new_ext = """                  <strong className="text-slate-700 block">Extracted Data Summary:</strong>
                  <div className="mt-1 text-slate-800 bg-white p-3 rounded border border-slate-200 max-h-48 overflow-y-auto">
                    {(() => {
                        try {
                            if(selectedReviewItem.extractedText && selectedReviewItem.extractedText.startsWith('{')){
                                const pt = JSON.parse(selectedReviewItem.extractedText);
                                return (
                                    <div className="space-y-2 text-xs font-mono">
                                        <div className="grid grid-cols-2 gap-2">
                                            <div><span className="font-bold text-slate-600">MRN:</span> {pt.patient_mrn || <span className="text-amber-600 italic">Not provided in document</span>}</div>
                                            <div><span className="font-bold text-slate-600">Patient:</span> {pt.patient_name || <span className="text-amber-600 italic">Requires verification</span>}</div>
                                            <div><span className="font-bold text-slate-600">Discharge:</span> {pt.discharge_date || <span className="text-amber-600 italic">Requires verification</span>}</div>
                                        </div>
                                        {pt.follow_ups && pt.follow_ups.length > 0 && (
                                            <div className="mt-2 border-t border-slate-100 pt-2">
                                                <span className="font-bold text-slate-600">Follow-ups:</span>
                                                <ul className="list-disc pl-4 mt-1">
                                                    {pt.follow_ups.map((f: any, i: number) => (
                                                        <li key={i}>{f.specialty} ({f.appointment_date || 'Requires verification'})</li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                        {(!pt.follow_ups || pt.follow_ups.length === 0) && (
                                            <div className="mt-2 text-slate-500 italic">No follow-ups extracted.</div>
                                        )}
                                    </div>
                                );
                            }
                        } catch(e) {}
                        return <span className="font-mono text-xs">\"{selectedReviewItem.extractedText}\"</span>;
                    })()}
                  </div>"""

text = text.replace(old_ext, new_ext)

with open('src/pages/DoctorDashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated Review Modal in DoctorDashboard.")
