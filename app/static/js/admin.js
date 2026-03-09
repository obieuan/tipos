const USER_COLORS = [
    '#4A90D9', '#E07B4C', '#7BC47F', '#D4A843',
    '#9B6BB0', '#D96B7A', '#5BBCBF', '#8B8B5E'
];

let allUsers = [];

async function loadUsers() {
    const listEl = document.getElementById('users-list');
    try {
        const res = await fetch('/api/admin/users');
        allUsers = await res.json();
        renderUsers();
    } catch {
        listEl.innerHTML = '<p class="empty-text">Error al cargar usuarios.</p>';
    }
}

function renderUsers() {
    const listEl = document.getElementById('users-list');
    if (allUsers.length === 0) {
        listEl.innerHTML = '<p class="empty-text">No hay usuarios.</p>';
        return;
    }

    listEl.innerHTML = allUsers.map(function(u) {
        const inactive = u.is_active ? '' : ' inactive';
        const status = u.is_active ? '' : ' (Inactivo)';
        return '<div class="user-card' + inactive + '">' +
            '<div class="user-card-left">' +
                '<div class="user-card-color" style="background-color:' + u.color + '"></div>' +
                '<div>' +
                    '<div class="user-card-name">' + u.name + status + '</div>' +
                    '<div class="user-card-meta">' + u.username + ' · ' + (u.role === 'admin' ? 'Admin' : 'Usuario') + '</div>' +
                '</div>' +
            '</div>' +
            '<div class="user-card-actions">' +
                '<button class="btn btn-small" onclick="editUser(' + u.id + ')">Editar</button>' +
                '<button class="btn btn-small" onclick="openResetPin(' + u.id + ')">\u{1F511}</button>' +
                (u.is_active
                    ? '<button class="btn btn-small btn-danger" onclick="toggleActive(' + u.id + ',false)">Desactivar</button>'
                    : '<button class="btn btn-small btn-primary" onclick="toggleActive(' + u.id + ',true)">Activar</button>'
                ) +
            '</div>' +
        '</div>';
    }).join('');
}

// Color picker
function renderColorPicker(selectedColor) {
    const picker = document.getElementById('color-picker');
    const usedColors = allUsers.map(function(u) { return u.color; });

    picker.innerHTML = USER_COLORS.map(function(c) {
        const sel = c === selectedColor ? ' selected' : '';
        const used = usedColors.includes(c) ? ' (en uso)' : '';
        return '<div class="color-swatch' + sel + '" style="background-color:' + c + '" ' +
            'data-color="' + c + '" title="' + c + used + '"></div>';
    }).join('');

    picker.querySelectorAll('.color-swatch').forEach(function(swatch) {
        swatch.addEventListener('click', function() {
            picker.querySelectorAll('.color-swatch').forEach(function(s) { s.classList.remove('selected'); });
            swatch.classList.add('selected');
        });
    });
}

function getSelectedColor() {
    const selected = document.querySelector('.color-swatch.selected');
    return selected ? selected.dataset.color : USER_COLORS[0];
}

// Create user modal
const userOverlay = document.getElementById('user-modal-overlay');

document.getElementById('create-user-btn').addEventListener('click', function() {
    document.getElementById('user-modal-title').textContent = 'Crear Usuario';
    document.getElementById('edit-user-id').value = '';
    document.getElementById('user-name').value = '';
    document.getElementById('user-pin').value = '';
    document.getElementById('user-role').value = 'user';
    document.getElementById('pin-fields').style.display = '';
    document.getElementById('user-error').style.display = 'none';
    renderColorPicker(USER_COLORS[0]);
    userOverlay.classList.add('visible');
});

document.getElementById('user-modal-close').addEventListener('click', function() {
    userOverlay.classList.remove('visible');
});
userOverlay.addEventListener('click', function(e) {
    if (e.target === userOverlay) userOverlay.classList.remove('visible');
});

document.getElementById('save-user-btn').addEventListener('click', async function() {
    const editId = document.getElementById('edit-user-id').value;
    const username = document.getElementById('user-name').value.trim();
    const pin = document.getElementById('user-pin').value;
    const role = document.getElementById('user-role').value;
    const color = getSelectedColor();
    const errEl = document.getElementById('user-error');

    if (!username) {
        errEl.textContent = 'El nombre es requerido';
        errEl.style.display = 'block';
        return;
    }

    if (editId) {
        // Edit existing
        try {
            const res = await fetch('/api/admin/users/' + editId, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: username, role: role, color: color }),
            });
            if (res.ok) {
                userOverlay.classList.remove('visible');
                loadUsers();
            } else {
                const data = await res.json();
                errEl.textContent = data.error || 'Error al editar';
                errEl.style.display = 'block';
            }
        } catch {
            errEl.textContent = 'Error de conexión';
            errEl.style.display = 'block';
        }
    } else {
        // Create new
        if (!pin || pin.length !== 4) {
            errEl.textContent = 'El PIN debe ser de 4 dígitos';
            errEl.style.display = 'block';
            return;
        }

        try {
            const res = await fetch('/api/admin/users', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: username, pin: pin, role: role, color: color }),
            });
            if (res.ok) {
                userOverlay.classList.remove('visible');
                loadUsers();
            } else {
                const data = await res.json();
                errEl.textContent = data.error || 'Error al crear';
                errEl.style.display = 'block';
            }
        } catch {
            errEl.textContent = 'Error de conexión';
            errEl.style.display = 'block';
        }
    }
});

function editUser(userId) {
    const user = allUsers.find(function(u) { return u.id === userId; });
    if (!user) return;

    document.getElementById('user-modal-title').textContent = 'Editar Usuario';
    document.getElementById('edit-user-id').value = user.id;
    document.getElementById('user-name').value = user.username;
    document.getElementById('user-pin').value = '';
    document.getElementById('user-role').value = user.role;
    document.getElementById('pin-fields').style.display = 'none';
    document.getElementById('user-error').style.display = 'none';
    renderColorPicker(user.color);
    userOverlay.classList.add('visible');
}

async function toggleActive(userId, activate) {
    const action = activate ? 'activate' : 'deactivate';
    const msg = activate ? '¿Activar este usuario?' : '¿Desactivar este usuario?';
    if (!confirm(msg)) return;

    try {
        await fetch('/api/admin/users/' + userId + '/' + action, { method: 'PUT' });
        loadUsers();
    } catch {
        alert('Error de conexión');
    }
}

// Reset PIN modal
const pinOverlay = document.getElementById('pin-modal-overlay');

function openResetPin(userId) {
    const user = allUsers.find(function(u) { return u.id === userId; });
    if (!user) return;

    document.getElementById('reset-pin-user-id').value = userId;
    document.getElementById('reset-pin-username').textContent = 'Usuario: ' + user.name;
    document.getElementById('reset-pin-value').value = '';
    document.getElementById('pin-reset-error').style.display = 'none';
    pinOverlay.classList.add('visible');
}

document.getElementById('pin-modal-close').addEventListener('click', function() {
    pinOverlay.classList.remove('visible');
});
pinOverlay.addEventListener('click', function(e) {
    if (e.target === pinOverlay) pinOverlay.classList.remove('visible');
});

document.getElementById('reset-pin-btn').addEventListener('click', async function() {
    const userId = document.getElementById('reset-pin-user-id').value;
    const newPin = document.getElementById('reset-pin-value').value;
    const errEl = document.getElementById('pin-reset-error');

    if (!newPin || newPin.length !== 4) {
        errEl.textContent = 'El PIN debe ser de 4 dígitos';
        errEl.style.display = 'block';
        return;
    }

    try {
        const res = await fetch('/api/admin/users/' + userId + '/reset-pin', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ new_pin: newPin }),
        });
        if (res.ok) {
            pinOverlay.classList.remove('visible');
            alert('PIN reseteado correctamente');
        } else {
            const data = await res.json();
            errEl.textContent = data.error || 'Error';
            errEl.style.display = 'block';
        }
    } catch {
        errEl.textContent = 'Error de conexión';
        errEl.style.display = 'block';
    }
});

// Initialize
loadUsers();
