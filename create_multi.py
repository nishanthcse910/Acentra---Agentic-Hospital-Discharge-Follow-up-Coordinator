from docx import Document
d=Document()
d.add_paragraph('Discharge Summary: MRN-9281C and MRN-1234A')
d.save('test_documents/multi_mrn.docx')
