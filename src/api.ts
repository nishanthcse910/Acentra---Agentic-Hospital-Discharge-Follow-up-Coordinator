const getHeaders = () => {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
};

export const api = {
    getExtraction: async (docId: number) => {
        const token = localStorage.getItem('token');
        const response = await fetch("http://localhost:8000/api/doctor/extraction/" + docId, {
            headers: {
                'Content-Type': 'application/json',
                ...(token ? { 'Authorization': `Bearer ${token}` } : {})
            }
        });
        if (!response.ok) throw new Error("Failed extraction");
        return response.json();
    },
    // Doctor Ops
    getDoctorStats: async () => {
        const res = await fetch('http://localhost:8000/api/doctor/stats', { headers: getHeaders() });
        return res.json();
    },
    getDoctorPatients: async () => {
        const res = await fetch('http://localhost:8000/api/doctor/patients', { headers: getHeaders() });
        return res.json();
    },
    getNeedsReview: async () => {
        const res = await fetch('http://localhost:8000/api/doctor/reviews', { headers: getHeaders() });
        return res.json();
    },
    getOverdue: async () => {
        const res = await fetch('http://localhost:8000/api/doctor/overdue', { headers: getHeaders() });
        return res.json();
    },
    uploadDoc: async (file: File) => {
        const token = localStorage.getItem('token');
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch("http://localhost:8000/api/doctor/upload", {
            method: 'POST',
            headers: {
                ...(token ? { 'Authorization': 'Bearer ' + token } : {})
            },
            body: formData
        });
        if (!response.ok) {
            const errBody = await response.text();
            throw new Error(`Upload API failed: ${response.status} - ${errBody}`);
        }
        return response.json();
    },

    // Patient Ops
    getPatientMe: async () => {
        const res = await fetch('http://localhost:8000/api/patient/me', { headers: getHeaders() });
        return res.json();
    },
    getPatientTasks: async () => {
        const res = await fetch('http://localhost:8000/api/patient/tasks', { headers: getHeaders() });
        return res.json();
    },
    getPatientTimeline: async () => {
        const res = await fetch('http://localhost:8000/api/patient/timeline', { headers: getHeaders() });
        return res.json();
    }
};
