// Public API address only. Database credentials belong exclusively in Render.
window.SKILLAJU_API_BASE = /^(localhost|127\.0\.0\.1)$/.test(location.hostname)
  ? 'http://127.0.0.1:8000'
  : 'https://skillaju-sql-practice-lab.onrender.com';
