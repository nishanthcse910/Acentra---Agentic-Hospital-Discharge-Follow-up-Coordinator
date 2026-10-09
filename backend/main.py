from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import os
import shutil
import datetime

import models
import document_parser
import extraction_service

from database import engine, get_db, Base
from auth import get_password_hash, verify_password, create_access_token, get_current_user
from pydantic import BaseModel

app = FastAPI(title="CareFlow AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(data={"sub": str(user.id)})
    
    patient_id = user.patient.id if user.patient else None
    
    return {
        "access_token": token, 
        "token_type": "bearer", 
        "role": user.role, 
        "name": user.name,
        "patient_id": patient_id
    }

@app.get("/api/auth/me")
def get_me(current_user: models.User = Depends(get_current_user)):
    patient_id = current_user.patient.id if current_user.patient else None
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "name": current_user.name,
        "patient_id": patient_id
    }

# ======================= DOCTOR DASHBOARD ENDPOINTS =======================

@app.get("/api/doctor/stats")
def doctor_stats(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != 'doctor':
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    total_patients = db.query(models.Patient).count()
    pending = db.query(models.FollowUpTask).filter(models.FollowUpTask.status.in_(['pending', 'in-progress'])).count()
    high_priority = db.query(models.Patient).filter(models.Patient.priority_level == 'high-priority').count()
    needs_review = db.query(models.NeedsReviewIssue).filter(models.NeedsReviewIssue.status == 'active').count()
    overdue = db.query(models.FollowUpTask).filter(models.FollowUpTask.status == 'overdue').count()
    
    return {
        "totalPatients": total_patients,
        "pendingFollowUps": pending,
        "highPriority": high_priority,
        "needsReview": needs_review,
        "overdue": overdue
    }

@app.get("/api/doctor/patients")
def doctor_patients(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != 'doctor':
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    patients = db.query(models.Patient).all()
    out = []
    for p in patients:
        tasks = [t for t in p.tasks if t.status != 'completed']
        next_task = tasks[0].title if tasks else "No pending tasks"
        due = tasks[0].due_date if tasks else "-"
        status = "pending" if tasks else "stable"
        
        out.append({
            "id": p.id,
            "patientId": p.id,
            "patientName": p.name,
            "name": p.name,
            "followUp": next_task,
            "dueDate": due,
            "status": status,
            "level": p.priority_level,
            "actionLabel": "Review Now" if p.priority_level == 'immediate-review' else "View",
            # Additional details
            "gender": p.gender,
            "primaryDiagnosis": p.primary_diagnosis,
            "admissionDate": p.admission_date,
            "dischargeDate": p.discharge_date,
            "attendingPhysician": p.attending_physician,
            "contactPhone": p.contact_phone,
            "preferredLanguage": p.preferred_language
        })
        
    # Sort: immediate > high > routine
    priority_map = {"immediate-review": 0, "high-priority": 1, "routine": 2}
    out.sort(key=lambda x: priority_map.get(x["level"], 3))
    return out

@app.get("/api/doctor/reviews")
def doctor_reviews(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != 'doctor': raise HTTPException(status_code=403)
    issues = db.query(models.NeedsReviewIssue).filter(models.NeedsReviewIssue.status == 'active').all()
    out = []
    for i in issues:
        patient_name = "Not provided in document"
        if i.patient:
            patient_name = i.patient.name
        else:
            # Check if name is in extracted JSON if it was an extraction issue
            if i.extracted_text and i.extracted_text.startswith('{'):
                try:
                    data = json.loads(i.extracted_text)
                    if data.get('patient_name'):
                        patient_name = data['patient_name']
                except:
                    pass

        out.append({
            "id": i.id,
            "patientId": i.patient_id,
            "patientName": patient_name,
            "category": i.category,
            "issue": i.issue,
            "extractedText": i.extracted_text,
            "flagReason": i.flag_reason,
            "source": i.source,
            "page": i.page
        })
    return out

@app.get("/api/doctor/overdue")
def doctor_overdue(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != 'doctor': raise HTTPException(status_code=403)
    tasks = db.query(models.FollowUpTask).filter(models.FollowUpTask.status == 'overdue').all()
    return [{
        "id": t.id,
        "patientName": t.patient.name,
        "daysOverdue": t.days_overdue or 1,
        "taskTitle": t.title,
        "dueDate": t.due_date,
        "attending": t.attending,
        "contactPhone": t.patient.contact_phone
    } for t in tasks]

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/api/doctor/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != 'doctor': raise HTTPException(status_code=403)
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    ext = file.filename.split('.')[-1].lower()
    if ext not in ['pdf', 'doc', 'docx', 'xls', 'xlsx']:
        raise HTTPException(status_code=400, detail="Unsupported file format")
        
    text = document_parser.extract_text(file_path, ext)
    mrns = document_parser.find_patient_mrns(text)
    
    needs_review = False
    review_reason = None
    matched_patient = None
    
    if len(mrns) == 0:
        needs_review = True
        review_reason = "Missing patient identifier. No MRN found in document."
    elif len(mrns) > 1:
        needs_review = True
        review_reason = f"Ambiguous/conflicting patient information. Found multiple identifiers: {', '.join(mrns)}."
    else:
        mrn = mrns[0]
        matched_patient = db.query(models.Patient).filter(func.upper(models.Patient.id) == mrn).first()
        if not matched_patient:
            needs_review = True
            review_reason = f"Unknown patient identifier: {mrn}."
            
    document = models.DischargeDocument(
        patient_id=matched_patient.id if matched_patient else None,
        original_filename=file.filename,
        file_path=file_path,
        status="needs-manual-review" if needs_review else "processed",
        needs_review=needs_review,
        review_reason=review_reason
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    if needs_review:
        issue = models.NeedsReviewIssue(
            id=f"NR_DOC_{document.id}",
            patient_id=None,
            document_id=document.id,
            category="patient-matching",
            issue="Document ingestion failed confident patient matching.",
            extracted_text=",".join(mrns) if mrns else "No MRN found",
            flag_reason=review_reason,
            source=file.filename,
            page=1,
            status="active"
        )
        db.add(issue)
        db.commit()
        return {"message": "Document uploaded and flagged for review.", "documentId": document.id, "needsReview": True, "reason": review_reason, "patientName": None, "extractedMrns": mrns}
    else:
        tl = models.TimelineEvent(
            id=f"TL_DOC_{document.id}",
            patient_id=matched_patient.id,
            date_str=datetime.datetime.utcnow().strftime("%d %b"),
            title="Discharge Document Uploaded & Extracted",
            description=f"File '{file.filename}' processed, mapped, and structured successfully.",
            status="completed",
            event_type="communication"
        )
        db.add(tl)
        db.commit()
        
        # --- PHASE 3 STEP 2 HOOK ---
        # Document successfully matches patient, now we attempt LLM extraction
        ext_record, ext_reasons = extraction_service.process_document_extraction(db, text, document, matched_patient)
        
        if document.needs_review:
             # It got flagged during extraction
             return {"message": "Document flagged during extraction review.", "documentId": document.id, "needsReview": True, "reason": document.review_reason, "patientName": matched_patient.name}
             
        return {"message": "success", "documentId": document.id, "needsReview": False, "patientName": matched_patient.name, "extractionId": ext_record.id}



class PatientRegisterRequest(BaseModel):
    id: str
    name: str

@app.post("/api/doctor/patients/register")
def register_patient(req: PatientRegisterRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != 'doctor': raise HTTPException(status_code=403)
    
    # Validation logic per requirements
    if not req.id or not req.id.startswith('MRN') or len(req.id) < 6:
        raise HTTPException(status_code=400, detail="Invalid MRN format.")
        
    existing = db.query(models.Patient).filter(models.Patient.id == req.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Patient with this MRN already exists.")
        
    new_patient = models.Patient(
        id=req.id,
        name=req.name,
        dob="01 Jan 1970",
        gender="Unknown",
        priority_level="routine"
    )
    db.add(new_patient)
    db.commit()
    
    return {"message": "Patient registered successfully", "patient": {"id": new_patient.id, "name": new_patient.name}}

class AssignPatientRequest(BaseModel):
    patient_id: str

@app.post("/api/doctor/documents/{document_id}/assign-patient")
def assign_document_patient(document_id: int, req: AssignPatientRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != 'doctor': raise HTTPException(status_code=403)
    
    doc = db.query(models.DischargeDocument).filter(models.DischargeDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if doc.patient_id:
        raise HTTPException(status_code=400, detail="Document is already assigned to a patient.")
        
    pt = db.query(models.Patient).filter(models.Patient.id == req.patient_id).first()
    if not pt:
        raise HTTPException(status_code=404, detail="Patient not found.")
        
    doc.patient_id = pt.id
    
    issue = db.query(models.NeedsReviewIssue).filter(models.NeedsReviewIssue.document_id == doc.id, models.NeedsReviewIssue.category == 'patient-matching').first()
    if issue:
        issue.status = "resolved"
        
    db.commit()
    
    # Resume processing
    import document_parser
    import extraction_service
    text_content = document_parser.extract_text(doc.file_path, doc.file_path.split('.')[-1])
    ext_record, ext_reasons = extraction_service.process_document_extraction(db, text_content, doc, pt)
    
    if ext_reasons:
        doc.needs_review = True
        doc.review_reason = ext_reasons
        doc.status = "needs-manual-review"
        db.commit()
        return {"message": "Assigned, but flagged during extraction.", "documentId": doc.id, "needsReview": True, "reason": ext_reasons, "patientName": pt.name}
    else:
        doc.needs_review = False
        doc.review_reason = None
        doc.status = "processed"
        
        # Add timeline event for resume processing success
        tl = models.TimelineEvent(
            id=f"TL_DOC_RESUME_{doc.id}",
            patient_id=pt.id,
            date_str="Today",
            title="Discharge Document Re-processed",
            description=f"Document successfully mapped to newly linked patient.",
            status="completed",
            event_type="communication"
        )
        db.add(tl)
        db.commit()
        
        return {"message": "Assigned and processed.", "documentId": doc.id, "needsReview": False, "patientName": pt.name, "extractionId": ext_record.id}


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

# ======================= PATIENT DASHBOARD ENDPOINTS =======================

@app.get("/api/patient/me")
def patient_profile(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != 'patient' or not current_user.patient:
        raise HTTPException(status_code=403, detail="Unauthorized")
    p = current_user.patient
    return {
        "id": p.id,
        "name": p.name,
        "dob": p.dob,
        "gender": p.gender,
        "primaryDiagnosis": p.primary_diagnosis,
        "admissionDate": p.admission_date,
        "dischargeDate": p.discharge_date,
        "attendingPhysician": p.attending_physician,
        "contactPhone": p.contact_phone,
        "preferredLanguage": p.preferred_language,
        "priority_level": p.priority_level
    }

@app.get("/api/patient/tasks")
def patient_tasks(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != 'patient' or not current_user.patient:
        raise HTTPException(status_code=403)
    tasks = db.query(models.FollowUpTask).filter(models.FollowUpTask.patient_id == current_user.patient.id).all()
    return [{
        "id": t.id,
        "title": t.title,
        "dueDate": t.due_date,
        "status": t.status,
        "type": t.task_type
    } for t in tasks]

@app.get("/api/patient/timeline")
def patient_timeline(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != 'patient' or not current_user.patient:
        raise HTTPException(status_code=403)
    events = db.query(models.TimelineEvent).filter(models.TimelineEvent.patient_id == current_user.patient.id).all()
    return [{
        "id": e.id,
        "date": e.date_str,
        "title": e.title,
        "description": e.description,
        "status": e.status,
        "type": e.event_type
    } for e in events]

@app.get("/api/doctor/extraction/{document_id}")
async def get_extraction(document_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != 'doctor': raise HTTPException(status_code=403)
    ext = db.query(models.DischargeExtraction).filter(models.DischargeExtraction.document_id == document_id).first()
    if not ext:
        raise HTTPException(status_code=404, detail="Extraction not found")
    import json
    return json.loads(ext.structured_data) if ext.structured_data else {}
