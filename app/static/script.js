/* =============================================
   CineMatch — script.js   (FIXED)
   =============================================
   Fix 1: toggleWishlist no longer crashes when
           .wishlist-button is absent from the page.
   Fix 2: showFlashMessage no longer assumes
           #flash-messages exists on every page.
   ============================================= */

/* ── Login-page tab switching ───────────────── */
document.addEventListener('DOMContentLoaded', function () {

    /* Tab links on login page */
    var toReg = document.getElementById('switch-to-register');
    var toLog = document.getElementById('switch-to-login');

    if (toReg) {
        toReg.addEventListener('click', function (e) {
            e.preventDefault();
            document.getElementById('login-form').classList.remove('active');
            document.getElementById('register-form').classList.add('active');
        });
    }

    if (toLog) {
        toLog.addEventListener('click', function (e) {
            e.preventDefault();
            document.getElementById('register-form').classList.remove('active');
            document.getElementById('login-form').classList.add('active');
        });
    }

    /* Auto-hide flash messages */
    _autoHide('flash-messages');
    _autoHide('flash-messages-register');
    _autoHide('flash-message');
});

function _autoHide(id) {
    var el = document.getElementById(id);
    if (!el || !el.innerHTML.trim()) return;
    setTimeout(function () {
        el.style.transition = 'opacity 0.5s';
        el.style.opacity = '0';
        setTimeout(function () { el.innerHTML = ''; el.style.opacity = '1'; }, 520);
    }, 3000);
}

/* ── Tab switcher (used by login index.html) ── */
function switchTab(tab) {
    var loginForm    = document.getElementById('login-form');
    var registerForm = document.getElementById('register-form');
    var tabLogin     = document.getElementById('tab-login');
    var tabRegister  = document.getElementById('tab-register');
    var slider       = document.getElementById('tab-slider');

    if (tab === 'login') {
        loginForm    && loginForm.classList.add('active');
        registerForm && registerForm.classList.remove('active');
        tabLogin     && tabLogin.classList.add('active');
        tabRegister  && tabRegister.classList.remove('active');
        slider       && slider.classList.remove('slide-right');
    } else {
        registerForm && registerForm.classList.add('active');
        loginForm    && loginForm.classList.remove('active');
        tabRegister  && tabRegister.classList.add('active');
        tabLogin     && tabLogin.classList.remove('active');
        slider       && slider.classList.add('slide-right');
    }
}

/* ── Password validation ─────────────────────── */
function validatePassword(form) {
    if (form.password.value.length < 6) {
        showFlashMessage('Password must be at least 6 characters.', 'error');
        return false;
    }
    return true;
}

/* ══════════════════════════════════════════════
   toggleWishlist — FIXED
   ── Removed the crash caused by assuming
      .wishlist-button always exists on the page.
   ── Now safely checks for the button first and
      toggles its text only when present.
   ══════════════════════════════════════════════ */
function toggleWishlist(movieId) {
    /* CSRF token — required by Flask-WTF */
    var csrfInput = document.querySelector('input[name="csrf_token"]');
    if (!csrfInput) {
        showFlashMessage('Security token missing. Please refresh the page.', 'error');
        return;
    }
    var csrfToken = csrfInput.value;

    fetch('/toggle_wishlist/' + movieId, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(function (response) {
        if (response.ok) return response.json();
        throw new Error('Server returned ' + response.status);
    })
    .then(function (data) {
        if (data.status === 'success') {
            showFlashMessage('Wishlist updated successfully!', 'success');

            /* ── FIX 1 ──────────────────────────────────────────
               Only try to update the button text when the button
               actually exists on this page (movie_details.html).
               Previously this line crashed with:
                 "Cannot read properties of null (reading 'textContent')"
               because .wishlist-button is absent on home/search pages.
            ───────────────────────────────────────────────────── */
            var btn = document.querySelector('.wishlist-button');
            if (btn) {
                if (btn.textContent.trim().includes('Add')) {
                    btn.textContent = '♥  Remove from Wishlist';
                    btn.classList.add('in-wishlist');
                } else {
                    btn.textContent = '♡  Add to Wishlist';
                    btn.classList.remove('in-wishlist');
                }
            }
        } else {
            showFlashMessage('An unexpected error occurred.', 'error');
        }
    })
    .catch(function (error) {
        console.error('Wishlist error:', error);
        showFlashMessage('An error occurred: ' + error.message, 'error');
    });
}

/* ── showFlashMessage ────────────────────────── */
function showFlashMessage(message, type) {
    /* Remove any existing floating message */
    var old = document.getElementById('_cm_toast');
    if (old) old.remove();

    var el = document.createElement('div');
    el.id  = '_cm_toast';
    el.textContent = message;

    var bg = (type === 'success')
        ? 'rgba(30,100,50,0.96)'
        : 'rgba(140,40,40,0.96)';

    el.style.cssText = [
        'position:fixed',
        'top:88px',          /* below the navbar */
        'left:50%',
        'transform:translateX(-50%)',
        'background:' + bg,
        'color:#f5ead8',
        'padding:0.75rem 2rem',
        'border-radius:3px',
        'font-family:Jost,system-ui,sans-serif',
        'font-size:0.82rem',
        'font-weight:400',
        'letter-spacing:0.05em',
        'z-index:9999',
        'box-shadow:0 8px 32px rgba(0,0,0,0.6)',
        'border:1px solid rgba(201,168,76,0.25)',
        'transition:opacity 0.4s ease',
        'white-space:nowrap'
    ].join(';');

    document.body.appendChild(el);

    setTimeout(function () {
        el.style.opacity = '0';
        setTimeout(function () { el.remove(); }, 430);
    }, 3000);
}

/* ── Genre helpers (unchanged) ──────────────── */
function toggleGenreDropdown() {
    var d = document.getElementById('genre-dropdown');
    if (d) d.style.display = d.style.display === 'none' ? 'block' : 'none';
}

function updateGenreForm() {
    var s = document.getElementById('genre-select');
    var f = document.getElementById('genre-form');
    if (s && f) f.action = '/movies_by_genre/' + s.value;
}

function searchMovie() {
    /* extend with your search logic if needed */
}