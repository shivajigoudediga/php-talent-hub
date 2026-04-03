const API_URL = '/api';

// ─────────────────────────────────────────────
//  REGISTER
// ─────────────────────────────────────────────
const registerForm = document.getElementById('register-form');
if (registerForm) {

    // Pre-select role if URL has ?role=recruiter
    const urlRole = new URLSearchParams(window.location.search).get('role');
    if (urlRole) {
        const roleSelect = document.getElementById('role');
        if (roleSelect) roleSelect.value = urlRole;
    }

    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const btn = document.getElementById('register-btn');
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Creating Account…';

        const name     = document.getElementById('name').value.trim();
        const email    = document.getElementById('email').value.trim();
        const phone    = document.getElementById('phone').value.trim();
        const role     = document.getElementById('role').value;
        const password = document.getElementById('password').value;

        try {
            const res  = await fetch(`${API_URL}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, phone, role, password })
            });
            const data = await res.json();

            if (res.ok) {
                // Store pending registration info for after OTP
                localStorage.setItem('pending_email', email);
                localStorage.setItem('pending_role',  role);
                localStorage.setItem('pending_name',  name);

                // Show OTP modal
                document.getElementById('otp-modal').classList.remove('hidden');
            } else {
                alert(data.message || 'Registration failed. Please try again.');
            }
        } catch (err) {
            alert('Connection error. Is the server running?');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<span>Create Account</span><i class="fas fa-arrow-right ml-2 text-sm"></i>';
        }
    });

    // ── Verify OTP ──────────────────────────────
    document.getElementById('verify-otp-btn').addEventListener('click', async () => {
        const otp   = document.getElementById('otp-input').value.trim();
        const email = localStorage.getItem('pending_email');

        if (!otp || otp.length < 4) {
            alert('Please enter the OTP sent to your email.');
            return;
        }

        const btn = document.getElementById('verify-otp-btn');
        btn.disabled = true;
        btn.textContent = 'Verifying…';

        try {
            const res  = await fetch(`${API_URL}/auth/verify-otp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, otp })
            });
            const data = await res.json();

            if (res.ok) {
                // ✅ FIX: backend returns "access_token" not "token"
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('role',  data.role  || localStorage.getItem('pending_role'));
                localStorage.setItem('name',  data.name  || localStorage.getItem('pending_name'));
                localStorage.setItem('email', data.email || email);
                localStorage.setItem('is_profile_complete', 'false'); // new user = incomplete

                // Clean up pending keys
                localStorage.removeItem('pending_email');
                localStorage.removeItem('pending_role');
                localStorage.removeItem('pending_name');

                // ✅ Redirect based on role
                redirectToDashboard(localStorage.getItem('role'));
            } else {
                alert(data.message || 'Invalid OTP. Please try again.');
            }
        } catch (err) {
            alert('Connection error. Is the server running?');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Verify & Continue';
        }
    });

    // ── Resend OTP ──────────────────────────────
    document.getElementById('resend-otp-btn').addEventListener('click', async () => {
        const email = localStorage.getItem('pending_email');
        if (!email) return;

        try {
            const res  = await fetch(`${API_URL}/auth/resend-otp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            const data = await res.json();
            alert(data.message || 'OTP resent!');
        } catch (err) {
            alert('Failed to resend OTP.');
        }
    });
}


// ─────────────────────────────────────────────
//  LOGIN
// ─────────────────────────────────────────────
const loginForm = document.getElementById('login-form');
if (loginForm) {

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const btn = document.getElementById('login-btn');
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Logging in…';

        const email    = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;

        try {
            const res  = await fetch(`${API_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await res.json();

            if (res.ok) {
                // ✅ Save ALL important fields to localStorage
                localStorage.setItem('token',               data.access_token);
                localStorage.setItem('role',                data.role);
                localStorage.setItem('name',                data.name);
                localStorage.setItem('email',               data.email || email);
                localStorage.setItem('user_id',             data.user_id);
                localStorage.setItem('is_profile_complete', data.is_profile_complete);

                // ✅ Redirect based on role + profile completion
                redirectToDashboard(data.role, data.is_profile_complete);
            } else {
                alert(data.message || 'Login failed. Check your credentials.');
            }
        } catch (err) {
            alert('Connection error. Is the server running?');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<span>Login</span><i class="fas fa-arrow-right ml-2 text-sm"></i>';
        }
    });
}


// ─────────────────────────────────────────────
//  HELPER — redirect based on role + profile
// ─────────────────────────────────────────────
function redirectToDashboard(role, isProfileComplete) {
    const BASE = '';
    if (role === 'developer') {
        if (isProfileComplete === false || isProfileComplete === 'false' || !isProfileComplete) {
            window.location.href = BASE + '/profile-complete.html';
        } else {
            window.location.href = BASE + '/developer-dashboard.html';
        }
    } else if (role === 'recruiter') {
        window.location.href = BASE + '/recruiter-dashboard.html';
    } else {
        alert('Unknown role: ' + role + '. Please contact support.');
        window.location.href = BASE + '/login.html';
    }
}