import re

with open('src/pages/DoctorDashboard.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

# Remove the AI Reminder mock block and adjust the grid
text = text.replace('<div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">', '<div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">')

ai_mock_pattern = r'\{\/\* SECTION 11: AI REMINDER ACTIVITY PANEL \*\/\}[\s\S]*?Safety Boundary: Never provides clinical advice\.\<\/span\>\n            \<\/div\>\n          \<\/div\>'
text = re.sub(ai_mock_pattern, '', text)

with open('src/pages/DoctorDashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(text)

print("Removed AI Reminder Mock Block.")
