const MONTH_NAMES = [
    'Enero','Febrero','Marzo','Abril','Mayo','Junio',
    'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'
];

let currentYear, currentMonth;
let calendarData = { reservations: [], blocked_days: [] };

const grid = document.getElementById('calendar-grid');
const monthTitle = document.getElementById('month-title');
const legend = document.getElementById('calendar-legend');

function init() {
    const now = new Date();
    currentYear = now.getFullYear();
    currentMonth = now.getMonth();
    loadCalendar();
}

document.getElementById('prev-month').addEventListener('click', function() {
    currentMonth--;
    if (currentMonth < 0) { currentMonth = 11; currentYear--; }
    loadCalendar();
});

document.getElementById('next-month').addEventListener('click', function() {
    currentMonth++;
    if (currentMonth > 11) { currentMonth = 0; currentYear++; }
    loadCalendar();
});

async function loadCalendar() {
    const monthStr = currentYear + '-' + String(currentMonth + 1).padStart(2, '0');
    monthTitle.textContent = MONTH_NAMES[currentMonth] + ' ' + currentYear;

    try {
        const res = await fetch('/api/calendar?month=' + monthStr);
        calendarData = await res.json();
        renderCalendar();
    } catch {
        grid.innerHTML = '<p style="grid-column:1/-1;text-align:center;">Error al cargar el calendario.</p>';
    }
}

function renderCalendar() {
    grid.innerHTML = '';

    const firstDay = new Date(currentYear, currentMonth, 1);
    let startDay = firstDay.getDay() - 1; // Monday = 0
    if (startDay < 0) startDay = 6;

    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    const today = new Date();
    const todayStr = today.getFullYear() + '-' +
        String(today.getMonth() + 1).padStart(2, '0') + '-' +
        String(today.getDate()).padStart(2, '0');

    // Empty cells before first day
    for (let i = 0; i < startDay; i++) {
        const empty = document.createElement('div');
        empty.className = 'calendar-day empty';
        grid.appendChild(empty);
    }

    const usersInMonth = {};

    for (let d = 1; d <= daysInMonth; d++) {
        const dateStr = currentYear + '-' +
            String(currentMonth + 1).padStart(2, '0') + '-' +
            String(d).padStart(2, '0');

        const cell = document.createElement('div');
        cell.className = 'calendar-day';
        cell.innerHTML = '<span class="day-number">' + d + '</span>';

        if (dateStr === todayStr) {
            cell.classList.add('today');
        }

        const blocked = calendarData.blocked_days.find(function(b) { return b.date === dateStr; });
        const reservation = calendarData.reservations.find(function(r) { return r.date === dateStr; });

        if (dateStr < todayStr) {
            cell.classList.add('past');
            if (reservation) {
                cell.style.backgroundColor = reservation.owner_color + '33';
                cell.innerHTML += '<span class="day-label">' + reservation.owner_name + '</span>';
                usersInMonth[reservation.owner_id] = {
                    name: reservation.owner_name,
                    color: reservation.owner_color
                };
            }
        } else if (blocked) {
            cell.classList.add('blocked');
            cell.innerHTML += '<span class="day-label">Bloqueado</span>';
            cell.addEventListener('click', function() {
                showBlockedDayModal(blocked);
            });
        } else if (reservation) {
            cell.style.backgroundColor = reservation.owner_color + '33';
            cell.innerHTML += '<span class="day-label">' + reservation.owner_name + '</span>';
            usersInMonth[reservation.owner_id] = {
                name: reservation.owner_name,
                color: reservation.owner_color
            };
            cell.addEventListener('click', function() {
                showReservationDetailModal(reservation);
            });
        } else {
            // Free day
            cell.addEventListener('click', function() {
                showReservationCreateModal(dateStr);
            });
        }

        grid.appendChild(cell);
    }

    // Render legend
    renderLegend(usersInMonth);
}

function renderLegend(usersInMonth) {
    let html = '<div class="legend-item"><div class="legend-color" style="background:var(--white);border:1px solid var(--border);"></div>Libre</div>';
    html += '<div class="legend-item"><div class="legend-color" style="background:var(--blocked);"></div>Bloqueado</div>';

    Object.values(usersInMonth).forEach(function(u) {
        html += '<div class="legend-item"><div class="legend-color" style="background:' + u.color + ';"></div>' + u.name + '</div>';
    });

    legend.innerHTML = html;
}

init();
