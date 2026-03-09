# Tipos Beach House — Instrucciones para Desarrollo

## Resumen del Proyecto

Aplicación web para gestionar la reserva de un espacio físico familiar (casa de playa). Es un sistema tipo Calendly simplificado y personalizado, donde una familia coordina quién ocupa el espacio y en qué fechas. El público objetivo son personas mayores, por lo que la UX debe ser extremadamente simple, con fuentes grandes, alto contraste y flujos mínimos.

**Nombre de la app:** Tipos Beach House  
**Hosting:** VPS OVH con Docker/Portainer (auto-hosteado)  
**Acceso principal:** Celular (prioritario), PC (secundario)  
**Concepto:** Puramente agenda, sin pagos ni cuotas

---

## Stack Tecnológico

- **Backend:** Python Flask (API REST con JSON)
- **Base de datos:** PostgreSQL (correr en Docker)
- **Frontend:** HTML/CSS/JS vanilla con diseño responsive mobile-first (NO usar frameworks JS pesados — la simplicidad es clave para mantenimiento a largo plazo)
- **Autenticación:** PIN numérico por usuario + nombre de usuario (sin passwords complejos)
- **Contenedorización:** Docker Compose (Flask app + PostgreSQL + Nginx como reverse proxy)
- **Migraciones:** Flask-Migrate (Alembic)

---

## Arquitectura General

```
docker-compose.yml
├── nginx (reverse proxy, SSL termination)
├── flask-app (API + frontend templates)
└── postgres (base de datos)
```

El frontend se sirve desde el mismo Flask app usando Jinja2 templates + vanilla JS. No es SPA, son páginas server-rendered con interactividad JS ligera para el calendario y modales. Esto simplifica el deploy y mantenimiento.

---

## Modelo de Datos

### Tabla: `users`
| Campo | Tipo | Notas |
|-------|------|-------|
| id | SERIAL PK | |
| username | VARCHAR(50) UNIQUE NOT NULL | Nombre para mostrar y login |
| pin_hash | VARCHAR(255) NOT NULL | PIN numérico hasheado (bcrypt) |
| role | VARCHAR(20) NOT NULL DEFAULT 'user' | 'admin' o 'user' |
| is_active | BOOLEAN DEFAULT TRUE | Para desactivar sin borrar |
| created_at | TIMESTAMP DEFAULT NOW() | |
| color | VARCHAR(7) NOT NULL | Color hex asignado para el calendario (ej: #4A90D9) |

### Tabla: `reservations`
| Campo | Tipo | Notas |
|-------|------|-------|
| id | SERIAL PK | |
| owner_id | FK → users.id NOT NULL | Usuario dueño de la reserva |
| date | DATE NOT NULL | Día reservado |
| block | VARCHAR(20) DEFAULT 'full_day' | 'full_day', 'morning', 'afternoon' (preparado para bloques futuros) |
| disclaimer_accepted | BOOLEAN DEFAULT FALSE | Si aceptó el disclaimer al reservar |
| notes | TEXT | Nota opcional del usuario |
| created_at | TIMESTAMP DEFAULT NOW() | |
| UNIQUE(date, block) | | No puede haber dos reservas en la misma fecha+bloque |

### Tabla: `reservation_guests`
| Campo | Tipo | Notas |
|-------|------|-------|
| id | SERIAL PK | |
| reservation_id | FK → reservations.id ON DELETE CASCADE | |
| guest_user_id | FK → users.id NOT NULL | Usuario invitado (registrado) |
| added_at | TIMESTAMP DEFAULT NOW() | |
| UNIQUE(reservation_id, guest_user_id) | | No duplicar invitados |

### Tabla: `activity_log`
| Campo | Tipo | Notas |
|-------|------|-------|
| id | SERIAL PK | |
| user_id | FK → users.id | Quién realizó la acción |
| action | VARCHAR(50) NOT NULL | Tipo de acción (ver catálogo abajo) |
| reservation_id | FK → reservations.id NULL | Reserva afectada (si aplica) |
| target_user_id | FK → users.id NULL | Usuario afectado (para reasignaciones/invitaciones) |
| details | JSONB | Detalles adicionales en JSON |
| created_at | TIMESTAMP DEFAULT NOW() | |

**Catálogo de acciones para `activity_log.action`:**
- `reservation_created` — Usuario apartó una fecha
- `reservation_cancelled` — Usuario desistió de su reserva
- `reservation_reassigned` — Dueño reasignó su reserva a otro usuario
- `guest_added` — Dueño agregó un invitado
- `guest_removed` — Dueño removió un invitado
- `guest_self_removed` — Invitado se removió a sí mismo
- `day_blocked` — Admin bloqueó un día
- `day_unblocked` — Admin desbloqueó un día
- `user_created` — Admin creó un usuario
- `user_deactivated` — Admin desactivó un usuario
- `settings_updated` — Admin actualizó configuración

### Tabla: `blocked_days`
| Campo | Tipo | Notas |
|-------|------|-------|
| id | SERIAL PK | |
| date | DATE UNIQUE NOT NULL | Día bloqueado |
| reason | VARCHAR(255) | Motivo (ej: "Mantenimiento") |
| blocked_by | FK → users.id | Admin que bloqueó |
| created_at | TIMESTAMP DEFAULT NOW() | |

### Tabla: `app_settings`
| Campo | Tipo | Notas |
|-------|------|-------|
| key | VARCHAR(100) PK | Nombre de la configuración |
| value | TEXT NOT NULL | Valor (serializado como JSON string si es complejo) |
| updated_at | TIMESTAMP DEFAULT NOW() | |

**Configuraciones iniciales (`app_settings`):**
| Key | Default | Descripción |
|-----|---------|-------------|
| `disclaimer_text` | "Al reservar, acepto respetar las reglas del espacio y dejarlo en condiciones adecuadas." | Texto del disclaimer editable |
| `booking_mode` | "full_day" | Modo de reserva: "full_day" o "blocks" (mañana/tarde) |
| `min_days_ahead` | 0 | Mínimo de días de anticipación para reservar (0 = mismo día) |
| `max_days_ahead` | 365 | Máximo de días hacia adelante permitidos |
| `site_name` | "Tipos Beach House" | Nombre del espacio mostrado en la UI |

---

## Autenticación y Sesiones

- Login con **nombre de usuario + PIN numérico** (4–6 dígitos, configurable por admin)
- El PIN se hashea con bcrypt antes de almacenar
- Sesiones con Flask-Login o JWT simple en cookie httpOnly
- Timeout de sesión: 30 días (es app familiar, no necesita ser restrictivo)
- El admin crea todos los usuarios y les asigna su PIN inicial
- Los usuarios pueden cambiar su propio PIN desde su perfil

**Pantalla de login:**
- Campo de texto para nombre de usuario
- Teclado numérico grande en pantalla para ingresar PIN (NO input de texto normal)
- Botón grande "Entrar"
- Sin opción de registro (solo el admin crea cuentas)

---

## Vistas y Funcionalidades

### 1. Login (`/login`)
- Nombre de usuario (texto)
- Teclado numérico en pantalla para PIN (botones grandes, mínimo 48px tap target)
- Mensaje de error amigable si falla

### 2. Calendario Principal (`/` — Vista principal post-login)
- Vista de calendario mensual (mes actual por defecto)
- Navegación entre meses con flechas grandes (< Anterior | Siguiente >)
- Cada día muestra:
  - **Libre:** Fondo blanco/claro, tappable
  - **Reservado por mí:** Fondo con MI color, muestra mi nombre
  - **Reservado por otro:** Fondo con SU color, muestra su nombre
  - **Bloqueado:** Fondo gris con ícono de candado
  - **Pasado:** Fondo ligeramente opaco, no interactivo
- Al tocar un día libre (futuro): abre modal de reserva
- Al tocar un día reservado: abre detalle de la reserva
- Leyenda de colores en la parte inferior

### 3. Modal de Reserva (al tocar día libre)
- Fecha seleccionada (grande, claro)
- Campo de notas (opcional, textarea corto)
- Checkbox obligatorio: "[disclaimer configurable]" ✓
- Botón grande "Reservar"
- Botón "Cancelar"

### 4. Detalle de Reserva (al tocar día reservado)
**Si soy el dueño:**
- Fecha y mi nombre como dueño
- Lista de invitados (si hay)
- Botón "Agregar Invitado" → selector de usuarios del sistema
- Botón "Quitar Invitado" (por cada invitado, con confirmación)
- Botón "Reasignar a otro usuario" → selector de usuarios, con confirmación
- Botón "Cancelar mi reserva" (con confirmación "¿Estás seguro?")
- Notas de la reserva

**Si soy invitado:**
- Fecha y nombre del dueño
- Lista de invitados (me incluye a mí)
- Botón "Ya no asistiré" (para removerme como invitado, con confirmación)

**Si no soy dueño ni invitado:**
- Fecha y nombre del dueño
- Lista de invitados
- Solo lectura, sin acciones

### 5. Historial (`/historial`)
- Dos sub-vistas con tabs:
  - **Por día:** Selector de fecha → muestra todos los movimientos de ese día
  - **Mensual:** Selector de mes → muestra todos los movimientos del mes
- Cada entrada del historial muestra:
  - Fecha y hora
  - Quién hizo la acción
  - Qué hizo (texto legible, no código)
  - A quién afectó (si aplica)
- Formato de texto legible: "**Juan** reservó el **15 de marzo**", "**María** se removió como invitada del **20 de abril**"
- Paginado si hay muchos registros (20 por página)
- Accesible tanto para usuarios normales como admins

### 6. Mi Perfil (`/perfil`)
- Mi nombre y color asignado
- Mis próximas reservas (lista simple)
- Fechas donde soy invitado
- Botón "Cambiar PIN"
- Botón "Cerrar sesión"

---

## Vistas de Administrador

### 7. Panel Admin (`/admin`)
- Solo accesible si `role == 'admin'`
- Secciones con navegación clara:

#### 7a. Gestión de Usuarios (`/admin/usuarios`)
- Lista de usuarios con: nombre, rol, color, estado (activo/inactivo)
- Botón "Crear Usuario" → formulario: nombre, PIN, rol, color
- Por cada usuario: Editar, Desactivar/Activar, Resetear PIN
- NO se borran usuarios (solo desactivar para preservar historial)

#### 7b. Configuración (`/admin/configuracion`)
- Editar texto del disclaimer (textarea)
- Modo de reserva: "Día completo" / "Bloques (Mañana/Tarde)" — radio buttons
- Días mínimos de anticipación (input numérico)
- Días máximos hacia adelante (input numérico)
- Nombre del sitio (texto)
- Botón "Guardar cambios"

#### 7c. Bloquear Días (`/admin/bloquear`)
- Calendario similar al principal pero para seleccionar días a bloquear
- Al tocar un día: modal para escribir motivo y confirmar bloqueo
- Días ya bloqueados se muestran con opción de desbloquear
- Si hay una reserva existente en un día que se quiere bloquear: advertencia y opción de cancelar la reserva automáticamente (registrando en el log)

#### 7d. Historial Completo (`/admin/historial`)
- Mismo historial que usuarios pero con filtros adicionales:
  - Filtrar por usuario
  - Filtrar por tipo de acción
  - Rango de fechas

---

## Diseño y UX — Lineamientos Clave

### Principios Generales (PERSONAS MAYORES)
- **Fuentes grandes:** Mínimo 18px para texto normal, 24px+ para títulos y botones
- **Alto contraste:** Texto oscuro (#1a1a1a) sobre fondos claros (#ffffff, #f5f5f5)
- **Botones grandes:** Mínimo 48px de altura, idealmente 56px+, con padding generoso
- **Tap targets amplios:** Mínimo 48x48px para cualquier elemento interactivo
- **Espaciado generoso:** Separación clara entre elementos, no amontonar
- **Colores distinguibles:** Los colores asignados a usuarios deben ser fácilmente distinguibles entre sí (evitar tonos muy similares)
- **Sin jerga técnica:** Textos claros y directos. "Reservar" no "Agendar slot"
- **Confirmaciones claras:** Siempre confirmar acciones destructivas con modal explícito
- **Feedback visual:** Indicar claramente cuándo algo se guardó, falló, o está cargando
- **Sin scroll horizontal:** Todo debe caber en el ancho del celular
- **Navegación simple:** Menú inferior fijo con íconos grandes: Calendario | Historial | Perfil (y Admin si aplica)

### Paleta de Colores Sugerida
- **Primario:** #2E7D6F (verde azulado cálido — evoca playa)
- **Secundario:** #F5A623 (naranja cálido para acciones/CTAs)
- **Fondo:** #FAFAFA
- **Texto:** #1A1A1A
- **Libre:** #FFFFFF con borde suave
- **Bloqueado:** #E0E0E0 con ícono candado
- **Error:** #D32F2F
- **Éxito:** #388E3C

### Colores para Usuarios (pool predefinido)
Asignar de este pool al crear usuarios:
```
#4A90D9 (azul)
#E07B4C (naranja)
#7BC47F (verde)
#D4A843 (dorado)
#9B6BB0 (morado)
#D96B7A (rosa)
#5BBCBF (turquesa)
#8B8B5E (olivo)
```

### Tipografía
- Font family: `'Inter', 'Segoe UI', system-ui, sans-serif`
- Cargar Inter desde Google Fonts
- Font sizes: 18px base, 14px mínimo absoluto (solo para metadata secundaria)

### Responsive
- **Mobile first** (< 768px): Una columna, calendario compacto pero legible
- **Tablet/Desktop** (≥ 768px): Más espacio, calendario más amplio
- El calendario en mobile muestra los días como cuadros con nombre abreviado del dueño
- En desktop muestra nombre completo

---

## API Endpoints

### Auth
- `POST /api/auth/login` — `{username, pin}` → `{token, user}`
- `POST /api/auth/logout` — Cerrar sesión
- `POST /api/auth/change-pin` — `{current_pin, new_pin}`

### Reservations
- `GET /api/reservations?month=YYYY-MM` — Reservas del mes (para el calendario)
- `POST /api/reservations` — `{date, notes}` → Crear reserva (valida disclaimer, fecha, bloqueos)
- `DELETE /api/reservations/:id` — Cancelar mi reserva
- `PUT /api/reservations/:id/reassign` — `{new_owner_id}` → Reasignar
- `POST /api/reservations/:id/guests` — `{user_id}` → Agregar invitado
- `DELETE /api/reservations/:id/guests/:user_id` — Quitar invitado
- `DELETE /api/reservations/:id/guests/me` — Auto-removerse como invitado

### Calendar
- `GET /api/calendar?month=YYYY-MM` — Vista combinada: reservas + bloqueos del mes
- `GET /api/blocked-days?month=YYYY-MM` — Días bloqueados

### History
- `GET /api/history?date=YYYY-MM-DD` — Historial por día
- `GET /api/history?month=YYYY-MM` — Historial mensual
- `GET /api/history?month=YYYY-MM&user_id=X&action=Y` — Con filtros (admin)

### Admin
- `GET /api/admin/users` — Lista de usuarios
- `POST /api/admin/users` — Crear usuario
- `PUT /api/admin/users/:id` — Editar usuario
- `PUT /api/admin/users/:id/deactivate` — Desactivar
- `PUT /api/admin/users/:id/activate` — Activar
- `PUT /api/admin/users/:id/reset-pin` — `{new_pin}`
- `GET /api/admin/settings` — Configuraciones
- `PUT /api/admin/settings` — Actualizar configuraciones
- `POST /api/admin/blocked-days` — `{date, reason}` → Bloquear día
- `DELETE /api/admin/blocked-days/:id` — Desbloquear

---

## Reglas de Negocio

1. **Solo el admin crea usuarios.** No hay registro público.
2. **Un usuario puede reservar un día si:**
   - La fecha no ha pasado
   - La fecha no está bloqueada
   - La fecha no tiene ya una reserva (en modo día completo)
   - La diferencia en días cumple con `min_days_ahead` y `max_days_ahead`
   - Acepta el disclaimer
3. **El dueño de una reserva puede:**
   - Cancelarla (si la fecha no ha pasado)
   - Reasignarla a otro usuario activo (la reserva cambia de dueño)
   - Agregar invitados (usuarios registrados activos)
   - Quitar invitados
4. **Un invitado puede:**
   - Auto-removerse de la reserva
5. **El admin puede:**
   - Todo lo que un usuario normal, más:
   - Crear/editar/desactivar usuarios
   - Bloquear/desbloquear días
   - Editar configuración global
   - Ver historial con filtros avanzados
   - Si bloquea un día con reserva existente, se le advierte y puede cancelar la reserva
6. **Toda acción se registra en `activity_log`** para el historial
7. **No se borran registros**, solo se desactivan (soft delete para usuarios, los logs son permanentes)

---

## Estructura del Proyecto

```
tipos-beach-house/
├── docker-compose.yml
├── Dockerfile
├── nginx/
│   └── nginx.conf
├── requirements.txt
├── .env.example
├── migrations/              # Flask-Migrate
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuración desde env vars
│   ├── extensions.py        # db, migrate, login_manager
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── reservation.py
│   │   ├── blocked_day.py
│   │   ├── activity_log.py
│   │   └── app_setting.py
│   ├── api/
│   │   ├── __init__.py      # Blueprint registration
│   │   ├── auth.py
│   │   ├── reservations.py
│   │   ├── calendar.py
│   │   ├── history.py
│   │   └── admin.py
│   ├── services/
│   │   ├── reservation_service.py  # Lógica de negocio
│   │   ├── user_service.py
│   │   └── log_service.py
│   ├── templates/
│   │   ├── base.html        # Layout base con nav inferior
│   │   ├── login.html
│   │   ├── calendar.html    # Vista principal
│   │   ├── history.html
│   │   ├── profile.html
│   │   └── admin/
│   │       ├── dashboard.html
│   │       ├── users.html
│   │       ├── settings.html
│   │       └── blocked_days.html
│   └── static/
│       ├── css/
│       │   └── style.css    # UN solo archivo CSS, mobile-first
│       ├── js/
│       │   ├── calendar.js  # Lógica del calendario interactivo
│       │   ├── modals.js    # Modales de reserva/detalle
│       │   ├── pin-pad.js   # Teclado numérico del login
│       │   └── admin.js     # Funciones admin
│       └── icons/           # Íconos SVG simples
├── seed.py                  # Script para crear admin inicial y datos de prueba
└── README.md
```

---

## Docker Compose

```yaml
version: '3.8'
services:
  app:
    build: .
    environment:
      - DATABASE_URL=postgresql://beach:${DB_PASSWORD}@db:5432/beachhouse
      - SECRET_KEY=${SECRET_KEY}
      - FLASK_ENV=production
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=beach
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=beachhouse
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - app
    restart: unless-stopped

volumes:
  pgdata:
```

---

## Seed Data (seed.py)

Al ejecutar `python seed.py`, crear:
- Un usuario admin: username="Admin", pin="1234", role="admin", color="#333333"
- Configuraciones default en `app_settings`
- (Opcional) 2-3 usuarios de prueba

---

## Notas Importantes para el Desarrollo

1. **Mobile first en todo momento.** Probar cada vista primero en viewport de 375px.
2. **El calendario es el corazón de la app.** Debe ser intuitivo y rápido. Usar vanilla JS, no librerías de calendario pesadas.
3. **Los modales deben ser fullscreen en mobile** para evitar problemas de scroll.
4. **El teclado numérico del PIN debe ser custom** (no depender del teclado del OS) para garantizar una experiencia consistente y botones grandes.
5. **Todas las fechas se manejan en zona horaria de México (America/Merida, CST UTC-6).**
6. **El campo `block` en reservations está preparado para uso futuro.** Por ahora solo se usa "full_day". Cuando `booking_mode` sea "blocks", la UI mostrará dos slots por día.
7. **Colores de usuario:** Al crear un usuario, mostrar el pool de colores disponibles (que no estén asignados) para elegir. Si se acaban, permitir repetir pero advertir.
8. **Los textos legibles del historial se generan en el backend**, no en el frontend. El API devuelve el texto ya formateado.
9. **Rate limiting básico** en el endpoint de login (máximo 5 intentos por IP cada 15 minutos).
10. **Gunicorn** como servidor WSGI en producción (en el Dockerfile).
