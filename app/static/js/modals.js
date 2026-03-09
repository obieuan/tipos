function openModal(title, bodyHTML) {
    const overlay = document.getElementById('modal-overlay');
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = bodyHTML;
    overlay.classList.add('visible');
}

function closeModal() {
    document.getElementById('modal-overlay').classList.remove('visible');
}

document.getElementById('modal-close').addEventListener('click', closeModal);
document.getElementById('modal-overlay').addEventListener('click', function(e) {
    if (e.target === this) closeModal();
});

function showBlockedDayModal(blocked) {
    var d = new Date(blocked.date + 'T12:00:00');
    var dateDisplay = d.toLocaleDateString('es-MX', {
        weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
    });
    var reason = blocked.reason || 'No se especificó un motivo';
    var html = '<p style="font-size:1.15rem;font-weight:600;margin-bottom:1rem;">' + dateDisplay + '</p>' +
        '<p style="margin-bottom:0.5rem;color:var(--text-light);">Este día está bloqueado</p>' +
        '<p style="font-size:1.05rem;"><strong>Motivo:</strong> ' + reason + '</p>' +
        '<div class="detail-actions">' +
            '<button class="btn btn-secondary btn-large" onclick="closeModal()">Cerrar</button>' +
        '</div>';
    openModal('Día Bloqueado', html);
}

function showReservationCreateModal(dateStr) {
    const d = new Date(dateStr + 'T12:00:00');
    const dateDisplay = d.toLocaleDateString('es-MX', {
        weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
    });

    const html =
        '<p style="font-size:1.15rem;font-weight:600;margin-bottom:1rem;">' + dateDisplay + '</p>' +
        '<label class="form-label">Notas (opcional)</label>' +
        '<textarea id="reservation-notes" class="form-input form-textarea" rows="2" placeholder="Agrega una nota..."></textarea>' +
        '<div class="checkbox-label" style="margin:1rem 0;">' +
            '<input type="checkbox" id="disclaimer-check">' +
            '<span>' + (window.DISCLAIMER_URL
                ? 'Al aceptar la reserva, confirmo que he leído y acepto los <a href="' + window.DISCLAIMER_URL + '" target="_blank" rel="noopener noreferrer">términos del uso del inmueble</a>.'
                : window.DISCLAIMER_TEXT) + '</span>' +
        '</div>' +
        '<div class="error-message" id="create-error"></div>' +
        '<div class="detail-actions">' +
            '<button class="btn btn-primary btn-large" id="confirm-reserve-btn">Reservar</button>' +
            '<button class="btn btn-secondary btn-large" onclick="closeModal()">Cancelar</button>' +
        '</div>';

    openModal('Nueva Reserva', html);

    document.getElementById('confirm-reserve-btn').addEventListener('click', async function() {
        const errEl = document.getElementById('create-error');
        if (!document.getElementById('disclaimer-check').checked) {
            errEl.textContent = 'Debes aceptar el disclaimer para continuar';
            errEl.style.display = 'block';
            return;
        }

        this.disabled = true;
        this.textContent = 'Reservando...';

        try {
            const res = await fetch('/api/reservations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    date: dateStr,
                    notes: document.getElementById('reservation-notes').value.trim(),
                }),
            });
            const data = await res.json();
            if (res.ok) {
                closeModal();
                if (typeof loadCalendar === 'function') loadCalendar();
            } else {
                errEl.textContent = data.error || 'Error al reservar';
                errEl.style.display = 'block';
            }
        } catch {
            errEl.textContent = 'Error de conexión';
            errEl.style.display = 'block';
        } finally {
            this.disabled = false;
            this.textContent = 'Reservar';
        }
    });
}

function showReservationDetailModal(reservation) {
    const d = new Date(reservation.date + 'T12:00:00');
    const dateDisplay = d.toLocaleDateString('es-MX', {
        weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
    });

    const currentUserId = window.CURRENT_USER.id;
    const isOwner = reservation.owner_id === currentUserId;
    const isGuest = reservation.guests && reservation.guests.some(g => g.id === currentUserId);

    let html = '<p style="font-size:1.15rem;font-weight:600;margin-bottom:1rem;">' + dateDisplay + '</p>';

    // Owner info
    html += '<div class="detail-owner">' +
        '<div class="detail-owner-color" style="background-color:' + reservation.owner_color + '"></div>' +
        '<span>Reserva de <strong>' + reservation.owner_name + '</strong></span>' +
    '</div>';

    // Notes
    if (reservation.notes) {
        html += '<div class="detail-notes">' + reservation.notes + '</div>';
    }

    // Guests
    html += '<div class="detail-guests"><h3 style="font-size:1rem;margin-bottom:0.5rem;">Invitados</h3>';
    if (reservation.guests && reservation.guests.length > 0) {
        reservation.guests.forEach(function(g) {
            html += '<div class="detail-guest"><span>' + g.name + '</span>';
            if (isOwner) {
                html += '<button class="btn btn-small btn-danger" onclick="removeGuest(' +
                    reservation.id + ',' + g.id + ')">Quitar</button>';
            }
            html += '</div>';
        });
    } else {
        html += '<p class="empty-text">Sin invitados</p>';
    }
    html += '</div>';

    // Actions
    html += '<div class="detail-actions">';
    if (isOwner) {
        html += '<button class="btn btn-primary btn-large" onclick="showAddGuestUI(' + reservation.id + ')">Agregar Invitado</button>';
        html += '<button class="btn btn-secondary btn-large" onclick="showReassignUI(' + reservation.id + ')">Reasignar a otro</button>';
        html += '<button class="btn btn-danger btn-large" onclick="cancelReservation(' + reservation.id + ')">Cancelar mi reserva</button>';
    } else if (isGuest) {
        html += '<button class="btn btn-danger btn-large" onclick="removeSelfAsGuest(' + reservation.id + ')">Ya no asistiré</button>';
    }
    html += '</div>';

    openModal('Detalle de Reserva', html);
}

async function cancelReservation(id) {
    if (!confirm('¿Estás seguro de cancelar esta reserva?')) return;
    try {
        const res = await fetch('/api/reservations/' + id, { method: 'DELETE' });
        if (res.ok) {
            closeModal();
            if (typeof loadCalendar === 'function') loadCalendar();
        } else {
            const data = await res.json();
            alert(data.error || 'Error al cancelar');
        }
    } catch {
        alert('Error de conexión');
    }
}

async function removeSelfAsGuest(id) {
    if (!confirm('¿Estás seguro de que ya no asistirás?')) return;
    try {
        const res = await fetch('/api/reservations/' + id + '/guests/me', { method: 'DELETE' });
        if (res.ok) {
            closeModal();
            if (typeof loadCalendar === 'function') loadCalendar();
        } else {
            const data = await res.json();
            alert(data.error || 'Error');
        }
    } catch {
        alert('Error de conexión');
    }
}

async function removeGuest(reservationId, userId) {
    if (!confirm('¿Quitar a este invitado?')) return;
    try {
        const res = await fetch('/api/reservations/' + reservationId + '/guests/' + userId, {
            method: 'DELETE',
        });
        if (res.ok) {
            closeModal();
            if (typeof loadCalendar === 'function') loadCalendar();
        } else {
            const data = await res.json();
            alert(data.error || 'Error');
        }
    } catch {
        alert('Error de conexión');
    }
}

async function showAddGuestUI(reservationId) {
    try {
        const res = await fetch('/api/admin/users');
        if (!res.ok) return;
        const users = await res.json();
        const activeUsers = users.filter(function(u) {
            return u.is_active && u.id !== window.CURRENT_USER.id;
        });

        let html = '<label class="form-label">Selecciona un usuario</label>';
        html += '<select id="guest-select" class="form-input">';
        activeUsers.forEach(function(u) {
            html += '<option value="' + u.id + '">' + u.name + '</option>';
        });
        html += '</select>';
        html += '<div class="error-message" id="guest-error"></div>';
        html += '<div class="detail-actions">';
        html += '<button class="btn btn-primary btn-large" id="confirm-add-guest">Agregar</button>';
        html += '<button class="btn btn-secondary btn-large" onclick="closeModal()">Cancelar</button>';
        html += '</div>';

        openModal('Agregar Invitado', html);

        document.getElementById('confirm-add-guest').addEventListener('click', async function() {
            const userId = document.getElementById('guest-select').value;
            const errEl = document.getElementById('guest-error');
            try {
                const r = await fetch('/api/reservations/' + reservationId + '/guests', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: parseInt(userId) }),
                });
                if (r.ok) {
                    closeModal();
                    if (typeof loadCalendar === 'function') loadCalendar();
                } else {
                    const d = await r.json();
                    errEl.textContent = d.error || 'Error';
                    errEl.style.display = 'block';
                }
            } catch {
                errEl.textContent = 'Error de conexión';
                errEl.style.display = 'block';
            }
        });
    } catch {
        alert('Error al cargar usuarios');
    }
}

async function showReassignUI(reservationId) {
    try {
        const res = await fetch('/api/admin/users');
        if (!res.ok) return;
        const users = await res.json();
        const activeUsers = users.filter(function(u) {
            return u.is_active && u.id !== window.CURRENT_USER.id;
        });

        let html = '<label class="form-label">Reasignar a</label>';
        html += '<select id="reassign-select" class="form-input">';
        activeUsers.forEach(function(u) {
            html += '<option value="' + u.id + '">' + u.name + '</option>';
        });
        html += '</select>';
        html += '<div class="error-message" id="reassign-error"></div>';
        html += '<div class="detail-actions">';
        html += '<button class="btn btn-primary btn-large" id="confirm-reassign">Reasignar</button>';
        html += '<button class="btn btn-secondary btn-large" onclick="closeModal()">Cancelar</button>';
        html += '</div>';

        openModal('Reasignar Reserva', html);

        document.getElementById('confirm-reassign').addEventListener('click', async function() {
            if (!confirm('¿Estás seguro de reasignar esta reserva?')) return;
            const userId = document.getElementById('reassign-select').value;
            const errEl = document.getElementById('reassign-error');
            try {
                const r = await fetch('/api/reservations/' + reservationId + '/reassign', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ new_owner_id: parseInt(userId) }),
                });
                if (r.ok) {
                    closeModal();
                    if (typeof loadCalendar === 'function') loadCalendar();
                } else {
                    const d = await r.json();
                    errEl.textContent = d.error || 'Error';
                    errEl.style.display = 'block';
                }
            } catch {
                errEl.textContent = 'Error de conexión';
                errEl.style.display = 'block';
            }
        });
    } catch {
        alert('Error al cargar usuarios');
    }
}
