import re

# 1. Update backend/main.py
with open('backend/main.py', 'r', encoding='utf-8') as f:
    be = f.read()

new_route = """
@app.post("/api/doctor/reviews/{issue_id}/resolve")
def resolve_review_issue(issue_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != 'doctor': raise HTTPException(status_code=403)
    
    issue = db.query(models.NeedsReviewIssue).filter(models.NeedsReviewIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
        
    issue.status = "resolved"
    
    # If the issue belongs to a document, mark the doc as processed if no other active issues exist
    if issue.document_id:
        doc = db.query(models.DischargeDocument).filter(models.DischargeDocument.id == issue.document_id).first()
        if doc:
            other_active = db.query(models.NeedsReviewIssue).filter(
                models.NeedsReviewIssue.document_id == doc.id,
                models.NeedsReviewIssue.status == 'active',
                models.NeedsReviewIssue.id != issue_id
            ).count()
            if other_active == 0:
                doc.needs_review = False
                doc.status = "processed"
                
                # We can also dynamically generate FollowUp tasks upon resolution if patient exists
                if doc.patient_id:
                    ext = db.query(models.DischargeExtraction).filter(models.DischargeExtraction.document_id == doc.id).first()
                    if ext and ext.structured_data:
                        import json
                        data = json.loads(ext.structured_data)
                        if data.get('follow_ups'):
                            import datetime
                            import uuid
                            for f in data['follow_ups']:
                                new_id = str(uuid.uuid4())[:8]
                                task = models.FollowUpTask(
                                    id=f"TASK_{new_id}",
                                    patient_id=doc.patient_id,
                                    title=f"Follow up: {f.get('specialty', 'Care Team')}",
                                    due_date=f.get('appointment_date', 'Review setup required'),
                                    status="pending",
                                    task_type="appointment",
                                    specialty=f.get('specialty', 'General'),
                                    attending=None,
                                    source=doc.original_filename
                                )
                                db.add(task)
                                
                                tl = models.TimelineEvent(
                                    id=f"TL_TSK_{new_id}",
                                    patient_id=doc.patient_id,
                                    date_str=datetime.datetime.utcnow().strftime("%d %b"),
                                    title="Task Approved by Clinical Review",
                                    description=f"Action item confirmed: {task.title}",
                                    status="completed",
                                    event_type="communication"
                                )
                                db.add(tl)
                                
    db.commit()
    return {"message": "Issue resolved and associated tasks auto-generated."}
"""

be = be.replace('# ======================= PATIENT DASHBOARD ENDPOINTS =======================', new_route + '\n# ======================= PATIENT DASHBOARD ENDPOINTS =======================')
with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(be)

# 2. Update src/api.ts
with open('src/api.ts', 'r', encoding='utf-8') as f:
    fe = f.read()

new_fe_route = """    resolveReviewIssue: async (issueId: string) => {
        const token = localStorage.getItem('token');
        const response = await fetch(`http://localhost:8000/api/doctor/reviews/${issueId}/resolve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(token ? { 'Authorization': 'Bearer ' + token } : {})
            }
        });
        if (!response.ok) throw new Error("Failed to resolve issue");
        return response.json();
    },
"""
fe = fe.replace('// Patient Ops', new_fe_route + '    // Patient Ops')
with open('src/api.ts', 'w', encoding='utf-8') as f:
    f.write(fe)

# 3. Update DoctorDashboard to call true API
with open('src/pages/DoctorDashboard.tsx', 'r', encoding='utf-8') as f:
    dash = f.read()

fake_resolve = """  const handleResolveReviewItem = (id: string, issue: string) => {
    setReviewQueue((prev) => prev.filter((item) => item.id !== id));
    setSelectedReviewItem(null);
    setToastMessage(`Clinician approved: "${issue}" resolved & updated`);
    setTimeout(() => setToastMessage(null), 3500);
  };"""

true_resolve = """  const handleResolveReviewItem = async (id: string, issue: string) => {
    try {
      await api.resolveReviewIssue(id);
      setSelectedReviewItem(null);
      setToastMessage(`Clinician approved: "${issue}" resolved & updated`);
      setTimeout(() => setToastMessage(null), 3500);
      loadData(); // Force live refresh across UI
    } catch (e: any) {
      setToastMessage("Failed to resolve review issue natively.");
    }
  };"""

dash = dash.replace(fake_resolve, true_resolve)

with open('src/pages/DoctorDashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(dash)

print("Implemented real Review Resolution logic with task extraction!")
