const fs = require('fs');
const c = fs.readFileSync('src/pages/DoctorDashboard.tsx', 'utf8');
const p = c.indexOf('const handleUpload');
const p2 = c.indexOf('catch', p);
console.log(c.substring(p, p2));
