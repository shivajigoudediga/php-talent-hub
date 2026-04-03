// main.js — shared utilities for PHP Talent Hub

const API_URL = 'http://127.0.0.1:5000/api';

/** Read token / user info from localStorage */
function getSession() {
    return {
        token: localStorage.getItem('token'),
        role:  localStorage.getItem('role'),
        name:  localStorage.getItem('name'),
        email: localStorage.getItem('email'),
    };
}

/** Clear session and go to login */
function logout() {
    localStorage.clear();
    window.location.href = 'login.html';
}

/** Update navbar with logged-in user info (used on index + job-listings) */
(function updateNav() {
    const { token, role, name } = getSession();
    const userNav = document.getElementById('user-nav');
    if (!userNav) return;

    if (token && name) {
        const dashboardUrl = role === 'developer'
            ? 'developer-dashboard.html'
            : 'recruiter-dashboard.html';
        userNav.innerHTML = `
            <a href="${dashboardUrl}" class="text-indigo-600 font-bold hover:underline">Hi, ${name}</a>
            <button onclick="logout()" class="text-gray-600 font-medium hover:text-red-600 transition ml-4">Logout</button>
        `;
    }
})();