import re

with open('src/pages/DoctorDashboard.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Pull `loadData` outside of useEffect
match = re.search(r'  useEffect\(\(\) => \{\n    async function loadData\(\) \{([\s\S]*?)\}\n    loadData\(\);\n  \}, \[\]\);', text)
if match:
    # Extract the inner body of the useEffect
    load_function = f"  const loadData = async () => {{{match.group(1)}}};\n\n  useEffect(() => {{\n    loadData();\n  }}, []);\n"
    text = text.replace(match.group(0), load_function)

# 2. Add 'UserPlus' to lucide imports if not exists
if 'UserPlus' not in text:
    text = text.replace("import { Activity,", "import { Activity, UserPlus,")

# 3. Add manual Add Patient state and UI
state_vars = """
  // Patient Registration UI
  const [showAddPatient, setShowAddPatient] = useState(false);
  const [newPatientMrn, setNewPatientMrn] = useState('');
  const [newPatientName, setNewPatientName] = useState('');
  const [isAddingPatient, setIsAddingPatient] = useState(false);

  const handleManualAddPatient = async () => {
    try {
      setIsAddingPatient(true);
      await api.registerPatient(newPatientMrn, newPatientName);
      setToastMessage("Patient registered successfully.");
      setShowAddPatient(false);
      setNewPatientMrn('');
      setNewPatientName('');
      loadData(); // REFRESH STATE!
    } catch(e: any) {
      setToastMessage(e.message || "Failed to register patient.");
    } finally {
      setIsAddingPatient(false);
    }
  };
"""
text = text.replace("  // Filter & Search states", state_vars + "\n  // Filter & Search states")


# 4. Insert Add Patient Button in Patients Tab
search_filters = """{/* Search & Filters */}
            <div className="flex flex-wrap items-center gap-2.5">
              <button 
                onClick={() => setShowAddPatient(true)}
                className="bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-colors"
              >
                <UserPlus className="w-4 h-4" /> Add Patient
              </button>"""
text = text.replace('{/* Search & Filters */}\n            <div className="flex flex-wrap items-center gap-2.5">', search_filters)


# 5. Insert Add Patient Modal at the bottom
add_patient_modal = """
      {/* Add Patient Modal */}
      <AnimatePresence>
        {showAddPatient && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl border border-slate-200 relative"
            >
              <button
                onClick={() => setShowAddPatient(false)}
                className="absolute top-4 right-4 p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
              
              <h2 className="text-xl font-bold text-slate-900 mb-4">Register New Patient</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1">Medical Record Number (MRN)</label>
                  <input type="text" value={newPatientMrn} onChange={e => setNewPatientMrn(e.target.value)} className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:border-teal-500 outline-none" placeholder="MRN-XXXX" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1">Patient Full Name</label>
                  <input type="text" value={newPatientName} onChange={e => setNewPatientName(e.target.value)} className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:border-teal-500 outline-none" placeholder="John Doe" />
                </div>
              </div>
              
              <div className="mt-6 flex justify-end gap-3">
                <button onClick={() => setShowAddPatient(false)} className="px-4 py-2 font-medium text-slate-500 hover:text-slate-700 rounded-lg hover:bg-slate-50">Cancel</button>
                <button 
                  onClick={handleManualAddPatient} 
                  disabled={isAddingPatient || !newPatientMrn || !newPatientName}
                  className="px-5 py-2 font-bold bg-teal-600 hover:bg-teal-700 text-white rounded-lg disabled:opacity-50"
                >
                  {isAddingPatient ? "Registering..." : "Register Patient"}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
"""

text = text.replace("      </div>\n    </div>\n  );\n}", add_patient_modal + "\n      </div>\n    </div>\n  );\n}")

with open('src/pages/DoctorDashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(text)

print("Phase 2: Add Patient UI implemented.")
