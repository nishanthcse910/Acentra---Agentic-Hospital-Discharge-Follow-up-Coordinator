from docx import Document
d=Document()
d.add_paragraph('Discharge Summary: Patient MRN-9999Z')
d.save('test_documents/unknown_mrn.docx')
