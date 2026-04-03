const API_URL = '/api';
const BASE_URL = '';
let currentStep = 1;
const totalSteps = 4;

// ✅ FIX 1: correct key is 'token' not 'access_token'
const token = localStorage.getItem('token');

if (!token) {
    alert('Session expired. Please log in again.');
    window.location.href = BASE_URL + '/login.html';  // ✅ FIX 2: always port 5000
}

const nextBtn        = document.getElementById('next-btn');
const prevBtn        = document.getElementById('prev-btn');
const submitBtn      = document.getElementById('submit-btn');
const progressBar    = document.getElementById('progress-bar');
const currentStepNum = document.getElementById('current-step-num');

// ── Step Navigation ──────────────────────────
const updateStep = (step) => {
    document.querySelectorAll('.step-content').forEach(el => el.classList.add('hidden'));
    document.getElementById(`step-${step}`).classList.remove('hidden');

    currentStepNum.textContent = step;
    progressBar.style.width = `${(step / totalSteps) * 100}%`;

    prevBtn.classList.toggle('hidden', step === 1);
    nextBtn.classList.toggle('hidden', step === totalSteps);
    submitBtn.classList.toggle('hidden', step !== totalSteps);
};

nextBtn.addEventListener('click', () => {
    if (currentStep < totalSteps) {
        currentStep++;
        updateStep(currentStep);
    }
});

prevBtn.addEventListener('click', () => {
    if (currentStep > 1) {
        currentStep--;
        updateStep(currentStep);
    }
});

// ── Add / Remove Skills ──────────────────────
document.getElementById('add-skill-btn').addEventListener('click', () => {
    const container = document.getElementById('skills-container');
    const row = document.createElement('div');
    row.className = 'flex items-center space-x-4 skill-row';
    row.innerHTML = `
        <input type="text" placeholder="Skill (e.g. Laravel)"
            class="flex-1 px-4 py-3 rounded-lg border border-gray-300 outline-none focus:ring-2 focus:ring-indigo-500">
        <select class="w-40 px-4 py-3 rounded-lg border border-gray-300 outline-none bg-white focus:ring-2 focus:ring-indigo-500">
            <option value="Beginner">Beginner</option>
            <option value="Intermediate">Intermediate</option>
            <option value="Expert">Expert</option>
        </select>
        <button type="button" class="remove-skill text-red-400 hover:text-red-600 transition">
            <i class="fas fa-trash"></i>
        </button>
    `;
    container.appendChild(row);
});

document.addEventListener('click', (e) => {
    if (e.target.closest('.remove-skill')) {
        e.target.closest('.skill-row').remove();
    }
});

// ── Pre-fill existing profile data ───────────
async function prefillProfile() {
    try {
        const res = await fetch(`${API_URL}/developer/profile`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) return;
        const data = await res.json();

        if (data.basic) {
            setField('phone',    data.basic.phone);
            setField('location', data.basic.location);
        }

        if (data.professional) {
            setField('experience_years', data.professional.experience_years);
            setField('current_company',  data.professional.current_company);
            setField('current_salary',   data.professional.current_salary);
            setField('notice_period',    data.professional.notice_period);
            setField('github_link',      data.professional.github_link);
            setField('linkedin_link',    data.professional.linkedin_link);
            setField('portfolio_link',   data.professional.portfolio_link);
        }

        if (data.skills && data.skills.length > 0) {
            const container = document.getElementById('skills-container');
            container.innerHTML = '';
            data.skills.forEach(s => {
                const row = document.createElement('div');
                row.className = 'flex items-center space-x-4 skill-row';
                row.innerHTML = `
                    <input type="text" value="${s.skill_name}" placeholder="Skill"
                        class="flex-1 px-4 py-3 rounded-lg border border-gray-300 outline-none focus:ring-2 focus:ring-indigo-500">
                    <select class="w-40 px-4 py-3 rounded-lg border border-gray-300 outline-none bg-white focus:ring-2 focus:ring-indigo-500">
                        <option value="Beginner"     ${s.skill_level === 'Beginner'     ? 'selected' : ''}>Beginner</option>
                        <option value="Intermediate" ${s.skill_level === 'Intermediate' ? 'selected' : ''}>Intermediate</option>
                        <option value="Expert"       ${s.skill_level === 'Expert'       ? 'selected' : ''}>Expert</option>
                    </select>
                    <button type="button" class="remove-skill text-red-400 hover:text-red-600 transition">
                        <i class="fas fa-trash"></i>
                    </button>
                `;
                container.appendChild(row);
            });
        }

    } catch (err) {
        console.warn('Could not prefill profile:', err.message);
    }
}

function setField(name, value) {
    if (!value && value !== 0) return;
    const el = document.querySelector(`[name="${name}"]`);
    if (el) el.value = value;
}

prefillProfile();

// ── Resume Dropzone ──────────────────────────
const dropzone        = document.getElementById('resume-dropzone');
const resumeInput     = document.getElementById('resume-input');
const fileNameDisplay = document.getElementById('selected-file-name');

dropzone.addEventListener('click', () => resumeInput.click());
resumeInput.addEventListener('change', () => {
    if (resumeInput.files[0]) {
        fileNameDisplay.textContent = '✓ ' + resumeInput.files[0].name;
        fileNameDisplay.classList.add('text-green-600');
    }
});

// ── Submit ───────────────────────────────────
document.getElementById('profile-multi-step-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const btn = document.getElementById('submit-btn');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Saving...';
    btn.disabled = true;

    // Collect only non-empty form fields
    const formData = new FormData(e.target);
    const profileData = {};
    for (const [key, value] of formData.entries()) {
        if (value && value.trim() !== '') {
            profileData[key] = value.trim();
        }
    }

    // Collect skills — only rows with a skill name filled
    const skills = Array.from(document.querySelectorAll('.skill-row'))
        .map(row => ({
            name:  row.querySelector('input').value.trim(),
            level: row.querySelector('select').value
        }))
        .filter(s => s.name !== '');

    try {
        // 1. Save profile
        const profRes = await fetch(`${API_URL}/developer/profile`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(profileData)
        });
        const profResult = await profRes.json();
        if (!profRes.ok) throw new Error(profResult.message || 'Failed to save profile');

        // 2. Save skills
        if (skills.length > 0) {
            const skillRes = await fetch(`${API_URL}/developer/skills`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(skills)
            });
            const skillResult = await skillRes.json();
            if (!skillRes.ok) throw new Error(skillResult.message || 'Failed to save skills');
        }

        // 3. Upload resume
        const resumeFile = resumeInput.files[0];
        if (resumeFile) {
            const resumeFormData = new FormData();
            resumeFormData.append('resume', resumeFile);
            const resumeRes = await fetch(`${API_URL}/developer/resume`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: resumeFormData
            });
            const resumeResult = await resumeRes.json();
            if (!resumeRes.ok) throw new Error(resumeResult.message || 'Failed to upload resume');
        }

        // ✅ FIX 3: update profile complete flag and redirect to port 5000
        localStorage.setItem('is_profile_complete', 'true');
        alert('✅ Profile saved successfully!');
        window.location.href = BASE_URL + '/developer-dashboard.html';

    } catch (err) {
        console.error('Submission error:', err);
        alert('❌ Error: ' + err.message);
    } finally {
        btn.innerHTML = '<i class="fas fa-check mr-2"></i> Save Profile';
        btn.disabled = false;
    }
});