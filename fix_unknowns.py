import json

with open('backend/main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace generic "UNKNOWN" patientName with "Not established" or extract from issue if possible.
# Wait, let's fix backend/main.py doctor_reviews
old_doctor_reviews = """    return [{
        "id": i.id,
        "patientId": i.patient_id,
        "patientName": i.patient.name if i.patient else "UNKNOWN",
        "category": i.category,
        "issue": i.issue,
        "extractedText": i.extracted_text,
        "flagReason": i.flag_reason,
        "source": i.source,
        "page": i.page
    } for i in issues]"""

new_doctor_reviews = """    out = []
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
    return out"""

text = text.replace(old_doctor_reviews, new_doctor_reviews)
with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(text)

# Also fix extraction_service.py to store full JSON in extracted_text instead of string slicing
with open('backend/extraction_service.py', 'r', encoding='utf-8') as f:
    ext_text = f.read()

old_extracted_text = 'extracted_text=str(raw_json)[:200],'
new_extracted_text = 'extracted_text=json.dumps(raw_json) if raw_json else "{}",'
ext_text = ext_text.replace(old_extracted_text, new_extracted_text)

with open('backend/extraction_service.py', 'w', encoding='utf-8') as f:
    f.write(ext_text)

print("Replaced UNKNOWN mapping in reviews.")
