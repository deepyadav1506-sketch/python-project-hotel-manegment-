/**
 * StayHome Hotel Management System - Frontend Application Logic
 * File: public/assets/app.js
 * 
 * Architecture:
 * - Single Page Application (SPA) with hash-based routing.
 * - Communicates with FastAPI backend REST endpoints via async fetch().
 * - Real-time state synchronization for rooms, customers, bookings, and billing.
 */

// Global Application Controller Object
const app = {
    // Cached State
    currentView: 'dashboard',
    roomsCache: [],
    customersCache: [],
    reservationsCache: [],
    paymentsCache: [],
    availableRoomsCache: [],
    
    // API Base URL
    apiBase: '/api',

    /**
     * Application Initialization
     */
    init: function() {
        console.log('[StayHome] Initializing Frontend Application...');
        this.setupNavigation();
        this.setupClock();
        this.setupEventListeners();
        this.handleHashChange();
    },

    /**
     * Clock and Date Banner in Header
     */
    setupClock: function() {
        const updateClock = () => {
            const now = new Date();
            const options = { weekday: 'short', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' };
            const el = document.getElementById('liveClockDisplay');
            if (el) el.textContent = now.toLocaleDateString('en-US', options);
        };
        updateClock();
        setInterval(updateClock, 1000);
    },

    /**
     * Hash-based SPA Navigation Router
     */
    setupNavigation: function() {
        window.addEventListener('hashchange', () => this.handleHashChange());

        // Mobile drawer toggle
        const toggleBtn = document.getElementById('mobileToggleBtn');
        const closeBtn = document.getElementById('mobileCloseBtn');
        const sidebar = document.getElementById('sidebar');

        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => sidebar.classList.add('open'));
        }
        if (closeBtn) {
            closeBtn.addEventListener('click', () => sidebar.classList.remove('open'));
        }

        // Quick booking top button
        const btnQuick = document.getElementById('btnQuickBooking');
        if (btnQuick) {
            btnQuick.addEventListener('click', () => this.showModal('modalNewReservation'));
        }
    },

    handleHashChange: function() {
        const hash = window.location.hash.replace('#', '') || 'dashboard';
        const sidebar = document.getElementById('sidebar');
        if (sidebar) sidebar.classList.remove('open');

        // Check if placeholder view
        const placeholderModules = ['staff', 'housekeeping', 'restaurant', 'inventory', 'maintenance', 'offers', 'reports', 'settings'];
        if (placeholderModules.includes(hash)) {
            this.renderPlaceholderView(hash);
            this.setActiveNav(hash);
            return;
        }

        this.navigateTo(hash, false);
    },

    navigateTo: function(viewId, updateHash = true) {
        if (updateHash) {
            window.location.hash = viewId;
            return;
        }

        this.currentView = viewId;
        this.setActiveNav(viewId);

        // Hide all views, show targeted view
        document.querySelectorAll('.view-section').forEach(sec => sec.classList.remove('active'));
        const targetSec = document.getElementById(`view-${viewId}`);
        if (targetSec) {
            targetSec.classList.add('active');
        } else {
            document.getElementById('view-dashboard').classList.add('active');
        }

        // Update Header Titles
        this.updateHeaderTitle(viewId);

        // Load targeted view data from backend
        switch(viewId) {
            case 'dashboard':
                this.loadDashboardData();
                break;
            case 'rooms':
                this.loadRooms();
                break;
            case 'customers':
                this.loadCustomers();
                break;
            case 'reservations':
                this.loadReservations();
                break;
            case 'checkinout':
                this.loadCheckInOutData();
                break;
            case 'billing':
                this.loadBillingData();
                break;
            case 'history':
                this.loadBookingHistory();
                break;
        }
    },

    setActiveNav: function(id) {
        document.querySelectorAll('.nav-link').forEach(link => {
            const view = link.getAttribute('data-view');
            const mod = link.getAttribute('data-module');
            if (view === id || mod === id) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    },

    updateHeaderTitle: function(viewId) {
        const titleEl = document.getElementById('pageTitle');
        const subEl = document.getElementById('pageSubtitle');
        const titles = {
            'dashboard': { t: 'Dashboard Overview', s: 'Live property status and guest activity' },
            'rooms': { t: 'Room Management', s: 'Inventory, categories, pricing, and live room states' },
            'customers': { t: 'Customer Directory', s: 'Guest database, contact credentials, and stay history' },
            'reservations': { t: 'Reservation Management', s: 'Room bookings, availability checks, and scheduled stays' },
            'checkinout': { t: 'Front Desk Operations', s: 'Guest check-ins, key allocations, departures, and balance settlement' },
            'billing': { t: 'Billing & Invoices', s: 'Payment tracking, tax calculations, and printable invoices' },
            'history': { t: 'Booking History & Audit', s: 'Complete ledger of all past and current reservations' }
        };

        if (titles[viewId]) {
            titleEl.textContent = titles[viewId].t;
            subEl.textContent = titles[viewId].s;
        }
    },

    /**
     * Event Listeners Setup
     */
    setupEventListeners: function() {
        // Room filters
        const roomsSearch = document.getElementById('roomsSearchInput');
        const roomsCat = document.getElementById('roomsCategoryFilter');
        const roomsStat = document.getElementById('roomsStatusFilter');
        if (roomsSearch) roomsSearch.addEventListener('input', () => this.loadRooms());
        if (roomsCat) roomsCat.addEventListener('change', () => this.loadRooms());
        if (roomsStat) roomsStat.addEventListener('change', () => this.loadRooms());

        // Customer filters
        const custSearch = document.getElementById('customersSearchInput');
        if (custSearch) custSearch.addEventListener('input', () => this.loadCustomers());

        // Reservation filters
        const resSearch = document.getElementById('reservationsSearchInput');
        const resStatus = document.getElementById('reservationsStatusFilter');
        if (resSearch) resSearch.addEventListener('input', () => this.loadReservations());
        if (resStatus) resStatus.addEventListener('change', () => this.loadReservations());

        // Billing filters
        const billSearch = document.getElementById('billingSearchInput');
        const billStatus = document.getElementById('billingStatusFilter');
        if (billSearch) billSearch.addEventListener('input', () => this.loadBillingData());
        if (billStatus) billStatus.addEventListener('change', () => this.loadBillingData());

        // History search
        const histSearch = document.getElementById('historySearchInput');
        if (histSearch) histSearch.addEventListener('input', () => this.loadBookingHistory());
    },

    // =========================================================================
    // API HELPER
    // =========================================================================
    apiCall: async function(endpoint, method = 'GET', body = null) {
        try {
            const options = {
                method: method,
                headers: { 'Content-Type': 'application/json' }
            };
            if (body) {
                options.body = JSON.stringify(body);
            }

            const response = await fetch(`${this.apiBase}${endpoint}`, options);
            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                throw new Error(data.detail || `Server returned error status ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error(`API Error on ${endpoint}:`, error);
            throw error;
        }
    },

    // =========================================================================
    // TOAST NOTIFICATIONS
    // =========================================================================
    showToast: function(message, type = 'success') {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        let icon = 'fa-circle-check';
        if (type === 'danger') icon = 'fa-triangle-exclamation';
        if (type === 'warning') icon = 'fa-circle-exclamation';

        toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    },

    // =========================================================================
    // 1. DASHBOARD MODULE
    // =========================================================================
    loadDashboardData: async function() {
        try {
            const stats = await this.apiCall('/dashboard/stats');
            
            // Populate Metric Cards
            document.getElementById('kpiTotalRooms').textContent = stats.total_rooms;
            document.getElementById('kpiAvailableRooms').textContent = stats.available_rooms;
            document.getElementById('kpiOccupiedRooms').textContent = stats.occupied_rooms;
            document.getElementById('kpiTotalCustomers').textContent = stats.total_customers;
            document.getElementById('kpiActiveBookings').textContent = stats.active_reservations;
            document.getElementById('kpiTodayCheckins').textContent = stats.today_checkins;
            document.getElementById('kpiTodayCheckouts').textContent = stats.today_checkouts;
            document.getElementById('kpiTotalRevenue').textContent = `₹${stats.total_revenue.toLocaleString('en-IN')}`;

            // Render Recent Bookings Table
            const tbody = document.querySelector('#dashboardRecentTable tbody');
            if (!stats.recent_bookings || stats.recent_bookings.length === 0) {
                tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-muted">No reservations recorded yet. Click 'New Reservation' to create one.</td></tr>`;
                return;
            }

            tbody.innerHTML = stats.recent_bookings.map(b => {
                const guestName = b.customer ? b.customer.full_name : 'Unknown';
                const roomNum = b.room ? `Room ${b.room.room_number}` : 'N/A';
                const totalAmt = b.payment ? `₹${b.payment.total_amount.toLocaleString('en-IN')}` : '₹0';
                const payStatus = b.payment ? b.payment.payment_status : 'Pending';

                return `
                    <tr>
                        <td><strong>${b.booking_code}</strong></td>
                        <td>${guestName}</td>
                        <td><span class="badge pill-room-${(b.room?.room_type || 'standard').toLowerCase()}">${roomNum}</span></td>
                        <td>${b.check_in_date} &rarr; ${b.check_out_date}</td>
                        <td>${b.total_nights} night${b.total_nights > 1 ? 's' : ''}</td>
                        <td>${this.renderStatusBadge(b.booking_status)}</td>
                        <td><strong>${totalAmt}</strong></td>
                        <td>${this.renderPaymentBadge(payStatus)}</td>
                        <td>
                            <button class="btn btn-outline btn-sm" onclick="app.viewInvoice(${b.id})" title="View Invoice">
                                <i class="fa-solid fa-file-invoice"></i>
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');

        } catch (err) {
            this.showToast(`Failed to load dashboard: ${err.message}`, 'danger');
        }
    },

    // =========================================================================
    // 2. ROOM MANAGEMENT MODULE
    // =========================================================================
    loadRooms: async function() {
        try {
            const cat = document.getElementById('roomsCategoryFilter')?.value || 'all';
            const stat = document.getElementById('roomsStatusFilter')?.value || 'all';
            const search = document.getElementById('roomsSearchInput')?.value || '';

            let query = `?category=${encodeURIComponent(cat)}&status=${encodeURIComponent(stat)}`;
            if (search.trim()) query += `&search=${encodeURIComponent(search.trim())}`;

            const rooms = await this.apiCall(`/rooms${query}`);
            this.roomsCache = rooms;

            const tbody = document.querySelector('#roomsTable tbody');
            if (rooms.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No rooms match the selected criteria.</td></tr>`;
                return;
            }

            tbody.innerHTML = rooms.map(r => `
                <tr>
                    <td><strong>Room ${r.room_number}</strong></td>
                    <td><span class="badge pill-room-${r.room_type.toLowerCase()}">${r.room_type}</span></td>
                    <td><strong>₹${r.price_per_night.toLocaleString('en-IN')}</strong> / night</td>
                    <td><i class="fa-solid fa-user-group text-muted"></i> ${r.capacity} Guests</td>
                    <td>${this.renderRoomStatusBadge(r.status)}</td>
                    <td><small class="text-secondary">${r.amenities || 'Standard'}</small></td>
                    <td>
                        <button class="btn btn-outline btn-sm" onclick="app.editRoom(${r.id})" title="Edit Room">
                            <i class="fa-solid fa-pen-to-square"></i>
                        </button>
                        <button class="btn btn-outline btn-sm text-danger" onclick="app.deleteRoom(${r.id}, '${r.room_number}')" title="Delete Room">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    </td>
                </tr>
            `).join('');

        } catch (err) {
            this.showToast(`Error fetching rooms: ${err.message}`, 'danger');
        }
    },

    editRoom: function(roomId) {
        const room = this.roomsCache.find(r => r.id === roomId);
        if (!room) return;

        document.getElementById('roomEditId').value = room.id;
        document.getElementById('roomNumber').value = room.room_number;
        document.getElementById('roomType').value = room.room_type;
        document.getElementById('roomPrice').value = room.price_per_night;
        document.getElementById('roomCapacity').value = room.capacity;
        document.getElementById('roomStatus').value = room.status;
        document.getElementById('roomAmenities').value = room.amenities || '';

        document.getElementById('roomModalTitle').innerHTML = `<i class="fa-solid fa-pen-to-square"></i> Edit Room ${room.room_number}`;
        this.showModal('modalRoom');
    },

    handleRoomSubmit: async function(e) {
        e.preventDefault();
        const editId = document.getElementById('roomEditId').value;
        const payload = {
            room_number: document.getElementById('roomNumber').value.trim(),
            room_type: document.getElementById('roomType').value,
            price_per_night: parseFloat(document.getElementById('roomPrice').value),
            capacity: parseInt(document.getElementById('roomCapacity').value, 10),
            status: document.getElementById('roomStatus').value,
            amenities: document.getElementById('roomAmenities').value.trim()
        };

        try {
            if (editId) {
                await this.apiCall(`/rooms/${editId}`, 'PUT', payload);
                this.showToast(`Room ${payload.room_number} updated successfully!`);
            } else {
                await this.apiCall('/rooms', 'POST', payload);
                this.showToast(`Room ${payload.room_number} created successfully!`);
            }
            this.closeModal('modalRoom');
            this.loadRooms();
        } catch (err) {
            this.showToast(err.message, 'danger');
        }
    },

    deleteRoom: async function(roomId, roomNum) {
        if (!confirm(`Are you sure you want to permanently delete Room ${roomNum}?`)) return;

        try {
            await this.apiCall(`/rooms/${roomId}`, 'DELETE');
            this.showToast(`Room ${roomNum} deleted successfully.`);
            this.loadRooms();
        } catch (err) {
            this.showToast(err.message, 'danger');
        }
    },

    // =========================================================================
    // 3. CUSTOMER MANAGEMENT MODULE
    // =========================================================================
    loadCustomers: async function() {
        try {
            const search = document.getElementById('customersSearchInput')?.value || '';
            const query = search.trim() ? `?search=${encodeURIComponent(search.trim())}` : '';

            const customers = await this.apiCall(`/customers${query}`);
            this.customersCache = customers;

            const tbody = document.querySelector('#customersTable tbody');
            if (customers.length === 0) {
                tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">No customers found.</td></tr>`;
                return;
            }

            tbody.innerHTML = customers.map(c => `
                <tr>
                    <td><strong>#${c.id}</strong></td>
                    <td><strong>${c.full_name}</strong></td>
                    <td><a href="mailto:${c.email}" class="text-primary">${c.email}</a></td>
                    <td>${c.phone}</td>
                    <td><small>${c.address || 'Not provided'}</small></td>
                    <td><small class="badge badge-secondary">${c.id_proof || 'Unspecified'}</small></td>
                    <td><span class="badge badge-info">${c.total_bookings} Stay${c.total_bookings !== 1 ? 's' : ''}</span></td>
                    <td>
                        <button class="btn btn-outline btn-sm" onclick="app.editCustomer(${c.id})" title="Edit Profile">
                            <i class="fa-solid fa-pen-to-square"></i>
                        </button>
                        <button class="btn btn-outline btn-sm text-danger" onclick="app.deleteCustomer(${c.id}, '${c.full_name}')" title="Delete Customer">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    </td>
                </tr>
            `).join('');

        } catch (err) {
            this.showToast(`Error fetching customers: ${err.message}`, 'danger');
        }
    },

    editCustomer: function(customerId) {
        const c = this.customersCache.find(item => item.id === customerId);
        if (!c) return;

        document.getElementById('customerEditId').value = c.id;
        document.getElementById('customerFullName').value = c.full_name;
        document.getElementById('customerEmail').value = c.email;
        document.getElementById('customerPhone').value = c.phone;
        document.getElementById('customerIdProof').value = c.id_proof || '';
        document.getElementById('customerAddress').value = c.address || '';

        document.getElementById('customerModalTitle').innerHTML = `<i class="fa-solid fa-user-pen"></i> Edit Profile: ${c.full_name}`;
        this.showModal('modalCustomer');
    },

    handleCustomerSubmit: async function(e) {
        e.preventDefault();
        const editId = document.getElementById('customerEditId').value;
        const payload = {
            full_name: document.getElementById('customerFullName').value.trim(),
            email: document.getElementById('customerEmail').value.trim(),
            phone: document.getElementById('customerPhone').value.trim(),
            id_proof: document.getElementById('customerIdProof').value.trim(),
            address: document.getElementById('customerAddress').value.trim()
        };

        try {
            if (editId) {
                await this.apiCall(`/customers/${editId}`, 'PUT', payload);
                this.showToast(`Customer '${payload.full_name}' updated successfully!`);
            } else {
                const newCust = await this.apiCall('/customers', 'POST', payload);
                this.showToast(`Customer '${payload.full_name}' registered successfully!`);
                
                // If created from reservation dialog, refresh customer dropdown and select them
                const resCustomerSelect = document.getElementById('resCustomerSelect');
                if (resCustomerSelect) {
                    const opt = document.createElement('option');
                    opt.value = newCust.id;
                    opt.textContent = `${newCust.full_name} (${newCust.phone})`;
                    opt.selected = true;
                    resCustomerSelect.appendChild(opt);
                }
            }
            this.closeModal('modalCustomer');
            this.loadCustomers();
        } catch (err) {
            this.showToast(err.message, 'danger');
        }
    },

    deleteCustomer: async function(customerId, customerName) {
        if (!confirm(`Are you sure you want to remove customer profile for '${customerName}'?`)) return;

        try {
            await this.apiCall(`/customers/${customerId}`, 'DELETE');
            this.showToast(`Customer '${customerName}' was removed successfully.`);
            this.loadCustomers();
        } catch (err) {
            this.showToast(err.message, 'danger');
        }
    },

    // =========================================================================
    // 4. RESERVATIONS MODULE
    // =========================================================================
    loadReservations: async function() {
        try {
            const statusFilter = document.getElementById('reservationsStatusFilter')?.value || 'all';
            const search = document.getElementById('reservationsSearchInput')?.value || '';

            let query = `?status=${encodeURIComponent(statusFilter)}`;
            if (search.trim()) query += `&search=${encodeURIComponent(search.trim())}`;

            const bookings = await this.apiCall(`/reservations${query}`);
            this.reservationsCache = bookings;

            const tbody = document.querySelector('#reservationsTable tbody');
            if (bookings.length === 0) {
                tbody.innerHTML = `<tr><td colspan="11" class="text-center py-4 text-muted">No reservations found.</td></tr>`;
                return;
            }

            tbody.innerHTML = bookings.map(b => {
                const guestName = b.customer ? b.customer.full_name : 'N/A';
                const guestPhone = b.customer ? b.customer.phone : '';
                const roomNum = b.room ? `Room ${b.room.room_number}` : 'N/A';
                const totalAmt = b.payment ? `₹${b.payment.total_amount.toLocaleString('en-IN')}` : '₹0';
                const payStatus = b.payment ? b.payment.payment_status : 'Pending';

                let actionButtons = `
                    <button class="btn btn-outline btn-sm" onclick="app.viewInvoice(${b.id})" title="Print Invoice">
                        <i class="fa-solid fa-receipt"></i>
                    </button>
                `;

                if (b.booking_status === 'Confirmed') {
                    actionButtons += `
                        <button class="btn btn-outline btn-sm text-primary" onclick="app.quickCheckIn(${b.id})" title="Check In Guest">
                            <i class="fa-solid fa-door-open"></i>
                        </button>
                        <button class="btn btn-outline btn-sm text-danger" onclick="app.cancelBooking(${b.id}, '${b.booking_code}')" title="Cancel Booking">
                            <i class="fa-solid fa-ban"></i>
                        </button>
                    `;
                } else if (b.booking_status === 'Checked-In') {
                    actionButtons += `
                        <button class="btn btn-outline btn-sm text-warning" onclick="app.openCheckOutModal(${b.id})" title="Check Out Guest">
                            <i class="fa-solid fa-person-walking-luggage"></i>
                        </button>
                    `;
                }

                return `
                    <tr>
                        <td><strong>${b.booking_code}</strong></td>
                        <td>
                            <strong>${guestName}</strong>
                            <small class="d-block text-muted">${guestPhone}</small>
                        </td>
                        <td><span class="badge pill-room-${(b.room?.room_type || 'standard').toLowerCase()}">${roomNum}</span></td>
                        <td>${b.check_in_date}</td>
                        <td>${b.check_out_date}</td>
                        <td>${b.total_nights}</td>
                        <td>${b.guests_count}</td>
                        <td>${this.renderStatusBadge(b.booking_status)}</td>
                        <td><strong>${totalAmt}</strong></td>
                        <td>${this.renderPaymentBadge(payStatus)}</td>
                        <td>${actionButtons}</td>
                    </tr>
                `;
            }).join('');

        } catch (err) {
            this.showToast(`Error fetching reservations: ${err.message}`, 'danger');
        }
    },

    prepareReservationModal: async function() {
        // Populate Customer Dropdown
        try {
            const customers = await this.apiCall('/customers');
            const custSelect = document.getElementById('resCustomerSelect');
            custSelect.innerHTML = '<option value="">-- Choose registered customer --</option>' +
                customers.map(c => `<option value="${c.id}">${c.full_name} (${c.phone})</option>`).join('');

            // Set default dates: Today to Tomorrow
            const today = new Date();
            const tomorrow = new Date();
            tomorrow.setDate(today.getDate() + 1);

            document.getElementById('resCheckIn').value = today.toISOString().split('T')[0];
            document.getElementById('resCheckOut').value = tomorrow.toISOString().split('T')[0];

            this.onReservationDatesChanged();
        } catch (err) {
            this.showToast(`Failed to initialize reservation modal: ${err.message}`, 'danger');
        }
    },

    onReservationDatesChanged: async function() {
        const checkIn = document.getElementById('resCheckIn').value;
        const checkOut = document.getElementById('resCheckOut').value;
        const roomSelect = document.getElementById('resRoomSelect');
        const roomNote = document.getElementById('roomAvailabilityNote');

        if (!checkIn || !checkOut) return;

        if (checkIn >= checkOut) {
            roomNote.innerHTML = '<span class="text-danger"><i class="fa-solid fa-circle-xmark"></i> Check-in date must be strictly before check-out date.</span>';
            roomSelect.innerHTML = '<option value="">-- Select valid dates --</option>';
            return;
        }

        try {
            roomNote.innerHTML = '<span class="text-muted"><i class="fa-solid fa-spinner fa-spin"></i> Checking live room availability...</span>';
            const availableRooms = await this.apiCall(`/rooms/available/lookup?check_in=${checkIn}&check_out=${checkOut}`);
            this.availableRoomsCache = availableRooms;

            if (availableRooms.length === 0) {
                roomSelect.innerHTML = '<option value="">-- No rooms available for these dates --</option>';
                roomNote.innerHTML = '<span class="text-danger"><i class="fa-solid fa-triangle-exclamation"></i> All rooms are occupied or reserved for this date range.</span>';
            } else {
                roomSelect.innerHTML = '<option value="">-- Select an available room --</option>' +
                    availableRooms.map(r => `<option value="${r.id}" data-price="${r.price_per_night}">Room ${r.room_number} (${r.room_type} - ₹${r.price_per_night}/night - Max ${r.capacity} Guests)</option>`).join('');
                roomNote.innerHTML = `<span class="text-success"><i class="fa-solid fa-circle-check"></i> ${availableRooms.length} room(s) available with zero date conflicts.</span>`;
            }

            this.calculateReservationEstimates();
        } catch (err) {
            roomNote.innerHTML = `<span class="text-danger">${err.message}</span>`;
        }
    },

    calculateReservationEstimates: function() {
        const checkInVal = document.getElementById('resCheckIn').value;
        const checkOutVal = document.getElementById('resCheckOut').value;
        const roomSelect = document.getElementById('resRoomSelect');
        const discountInput = document.getElementById('resDiscount');

        if (!checkInVal || !checkOutVal || checkInVal >= checkOutVal) {
            document.getElementById('estimateNights').textContent = '0 Nights';
            document.getElementById('estimateRoomCharges').textContent = '₹0';
            document.getElementById('estimateTax').textContent = '₹0';
            document.getElementById('estimateTotalAmount').textContent = '₹0';
            return;
        }

        const date1 = new Date(checkInVal);
        const date2 = new Date(checkOutVal);
        const nights = Math.max(1, Math.round((date2 - date1) / (1000 * 60 * 60 * 24)));
        document.getElementById('estimateNights').textContent = `${nights} Night${nights > 1 ? 's' : ''}`;

        const selectedOption = roomSelect.options[roomSelect.selectedIndex];
        const pricePerNight = selectedOption ? parseFloat(selectedOption.getAttribute('data-price') || 0) : 0;

        document.getElementById('estimateRoomRate').textContent = `₹${pricePerNight.toLocaleString('en-IN')} / night`;
        const roomCharges = nights * pricePerNight;
        document.getElementById('estimateRoomCharges').textContent = `₹${roomCharges.toLocaleString('en-IN')}`;

        let discount = parseFloat(discountInput.value) || 0;
        if (discount > roomCharges) discount = roomCharges;

        const taxableAmount = roomCharges - discount;
        const taxAmount = Math.round(taxableAmount * 0.10); // 10%
        const totalAmount = taxableAmount + taxAmount;

        document.getElementById('estimateTax').textContent = `₹${taxAmount.toLocaleString('en-IN')}`;
        document.getElementById('estimateTotalAmount').textContent = `₹${totalAmount.toLocaleString('en-IN')}`;
    },

    handleReservationSubmit: async function(e) {
        e.preventDefault();
        const payload = {
            customer_id: parseInt(document.getElementById('resCustomerSelect').value, 10),
            room_id: parseInt(document.getElementById('resRoomSelect').value, 10),
            check_in_date: document.getElementById('resCheckIn').value,
            check_out_date: document.getElementById('resCheckOut').value,
            guests_count: parseInt(document.getElementById('resGuestsCount').value, 10),
            special_requests: document.getElementById('resSpecialRequests').value.trim(),
            discount_amount: parseFloat(document.getElementById('resDiscount').value) || 0.0,
            payment_method: document.getElementById('resPaymentMethod').value,
            initial_payment: parseFloat(document.getElementById('resInitialPayment').value) || 0.0
        };

        try {
            const booking = await this.apiCall('/reservations', 'POST', payload);
            this.showToast(`Reservation ${booking.booking_code} confirmed successfully!`);
            this.closeModal('modalNewReservation');
            this.loadReservations();
        } catch (err) {
            this.showToast(err.message, 'danger');
        }
    },

    cancelBooking: async function(bookingId, bookingCode) {
        const reason = prompt(`Please enter cancellation reason for reservation ${bookingCode}:`, 'Guest requested cancellation');
        if (reason === null) return;

        try {
            await this.apiCall(`/reservations/${bookingId}/cancel?reason=${encodeURIComponent(reason)}`, 'POST');
            this.showToast(`Reservation ${bookingCode} has been cancelled.`);
            this.loadReservations();
        } catch (err) {
            this.showToast(err.message, 'danger');
        }
    },

    openNewCustomerFromReservation: function() {
        document.getElementById('formCustomer').reset();
        document.getElementById('customerEditId').value = '';
        document.getElementById('customerModalTitle').innerHTML = '<i class="fa-solid fa-user-plus"></i> Quick Register Guest';
        this.showModal('modalCustomer');
    },

    // =========================================================================
    // 5. CHECK-IN / CHECK-OUT FRONT DESK MODULE
    // =========================================================================
    switchDeskTab: function(tabId) {
        document.querySelectorAll('.desk-tab').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.desk-tab-content').forEach(c => c.classList.remove('active'));

        document.querySelector(`.desk-tab[data-tab="${tabId}"]`).classList.add('active');
        document.getElementById(tabId).classList.add('active');
    },

    loadCheckInOutData: async function() {
        try {
            const allBookings = await this.apiCall('/reservations');

            // Filter Confirmed bookings for Check-In
            const confirmedBookings = allBookings.filter(b => b.booking_status === 'Confirmed');
            const checkinTbody = document.querySelector('#checkinTable tbody');

            if (confirmedBookings.length === 0) {
                checkinTbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">No confirmed arrivals awaiting check-in at this time.</td></tr>`;
            } else {
                checkinTbody.innerHTML = confirmedBookings.map(b => `
                    <tr>
                        <td><strong>${b.booking_code}</strong></td>
                        <td>${b.customer ? b.customer.full_name : 'N/A'}</td>
                        <td><span class="badge pill-room-${(b.room?.room_type || 'standard').toLowerCase()}">Room ${b.room?.room_number || 'N/A'}</span></td>
                        <td><strong>${b.check_in_date}</strong></td>
                        <td>${b.check_out_date}</td>
                        <td>${b.total_nights} Nights</td>
                        <td>${this.renderPaymentBadge(b.payment?.payment_status || 'Pending')}</td>
                        <td>
                            <button class="btn btn-primary btn-sm" onclick="app.quickCheckIn(${b.id})">
                                <i class="fa-solid fa-door-open"></i> Check In
                            </button>
                        </td>
                    </tr>
                `).join('');
            }

            // Filter Checked-In bookings for Check-Out
            const activeBookings = allBookings.filter(b => b.booking_status === 'Checked-In');
            const checkoutTbody = document.querySelector('#checkoutTable tbody');

            if (activeBookings.length === 0) {
                checkoutTbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-muted">No in-house guests currently checked in.</td></tr>`;
            } else {
                checkoutTbody.innerHTML = activeBookings.map(b => {
                    const total = b.payment ? b.payment.total_amount : 0;
                    const paid = b.payment ? b.payment.amount_paid : 0;
                    const balance = Math.max(0, total - paid);

                    return `
                        <tr>
                            <td><strong>${b.booking_code}</strong></td>
                            <td>${b.customer ? b.customer.full_name : 'N/A'}</td>
                            <td><span class="badge pill-room-${(b.room?.room_type || 'standard').toLowerCase()}">Room ${b.room?.room_number || 'N/A'}</span></td>
                            <td>${b.check_in_date}</td>
                            <td><strong>${b.check_out_date}</strong></td>
                            <td>₹${total.toLocaleString('en-IN')}</td>
                            <td class="text-success">₹${paid.toLocaleString('en-IN')}</td>
                            <td class="${balance > 0 ? 'text-danger font-weight-bold' : 'text-success'}"><strong>₹${balance.toLocaleString('en-IN')}</strong></td>
                            <td>
                                <button class="btn btn-warning btn-sm" onclick="app.openCheckOutModal(${b.id})">
                                    <i class="fa-solid fa-person-walking-luggage"></i> Check Out
                                </button>
                            </td>
                        </tr>
                    `;
                }).join('');
            }

        } catch (err) {
            this.showToast(`Error loading front desk: ${err.message}`, 'danger');
        }
    },

    quickCheckIn: async function(bookingId) {
        if (!confirm('Confirm guest identity and mark room as Occupied?')) return;

        try {
            const res = await this.apiCall('/operations/check-in', 'POST', { booking_id: bookingId });
            this.showToast(res.message);
            this.loadCheckInOutData();
            if (this.currentView === 'reservations') this.loadReservations();
        } catch (err) {
            this.showToast(err.message, 'danger');
        }
    },

    openCheckOutModal: async function(bookingId) {
        try {
            const b = await this.apiCall(`/reservations/${bookingId}`);
            const pay = b.payment;
            const balance = pay ? Math.max(0, pay.total_amount - pay.amount_paid) : 0;

            document.getElementById('checkoutBookingId').value = b.id;
            document.getElementById('coGuestName').textContent = b.customer ? b.customer.full_name : 'N/A';
            document.getElementById('coRoomNumber').textContent = `Room ${b.room ? b.room.room_number : 'N/A'} (${b.room ? b.room.room_type : ''})`;
            document.getElementById('coTotalBill').textContent = `₹${pay ? pay.total_amount.toLocaleString('en-IN') : 0}`;
            document.getElementById('coAmountPaid').textContent = `₹${pay ? pay.amount_paid.toLocaleString('en-IN') : 0}`;
            document.getElementById('coBalanceDue').textContent = `₹${balance.toLocaleString('en-IN')}`;
            document.getElementById('coPaymentNow').value = balance;

            this.showModal('modalCheckOut');
        } catch (err) {
            this.showToast(err.message, 'danger');
        }
    },

    handleCheckOutSubmit: async function(e) {
        e.preventDefault();
        const payload = {
            booking_id: parseInt(document.getElementById('checkoutBookingId').value, 10),
            amount_paid_now: parseFloat(document.getElementById('coPaymentNow').value) || 0.0,
            payment_method: document.getElementById('coPaymentMethod').value,
            notes: document.getElementById('coNotes').value.trim()
        };

        try {
            const res = await this.apiCall('/operations/check-out', 'POST', payload);
            this.showToast(res.message);
            this.closeModal('modalCheckOut');
            this.loadCheckInOutData();
            if (this.currentView === 'reservations') this.loadReservations();
        } catch (err) {
            this.showToast(err.message, 'danger');
        }
    },

    // =========================================================================
    // 6. BILLING & INVOICE MODULE
    // =========================================================================
    loadBillingData: async function() {
        try {
            const status = document.getElementById('billingStatusFilter')?.value || 'all';
            const search = document.getElementById('billingSearchInput')?.value || '';

            let query = `?status=${encodeURIComponent(status)}`;
            if (search.trim()) query += `&search=${encodeURIComponent(search.trim())}`;

            const payments = await this.apiCall(`/billing/payments${query}`);
            this.paymentsCache = payments;

            const tbody = document.querySelector('#billingTable tbody');
            if (payments.length === 0) {
                tbody.innerHTML = `<tr><td colspan="12" class="text-center py-4 text-muted">No invoices found.</td></tr>`;
                return;
            }

            tbody.innerHTML = payments.map(p => `
                <tr>
                    <td><strong>${p.invoice_number}</strong></td>
                    <td>${p.booking_code}</td>
                    <td><strong>${p.customer_name}</strong></td>
                    <td>Room ${p.room_number}</td>
                    <td>₹${p.room_charges.toLocaleString('en-IN')}</td>
                    <td class="text-success">-₹${p.discount_amount.toLocaleString('en-IN')}</td>
                    <td>₹${p.tax_amount.toLocaleString('en-IN')}</td>
                    <td><strong>₹${p.total_amount.toLocaleString('en-IN')}</strong></td>
                    <td class="text-success">₹${p.amount_paid.toLocaleString('en-IN')}</td>
                    <td class="${p.balance_due > 0 ? 'text-danger font-weight-bold' : 'text-success'}">₹${p.balance_due.toLocaleString('en-IN')}</td>
                    <td>${this.renderPaymentBadge(p.payment_status)}</td>
                    <td>
                        <button class="btn btn-outline btn-sm" onclick="app.viewInvoice(${p.booking_id})" title="Print Invoice">
                            <i class="fa-solid fa-print"></i>
                        </button>
                        ${p.balance_due > 0 ? `
                        <button class="btn btn-primary btn-sm" onclick="app.openRecordPaymentModal(${p.booking_id})" title="Record Payment">
                            <i class="fa-solid fa-money-bill-wave"></i>
                        </button>` : ''}
                    </td>
                </tr>
            `).join('');

        } catch (err) {
            this.showToast(`Error loading billing: ${err.message}`, 'danger');
        }
    },

    openRecordPaymentModal: async function(bookingId) {
        try {
            const b = await this.apiCall(`/reservations/${bookingId}`);
            const pay = b.payment;
            const balance = pay ? Math.max(0, pay.total_amount - pay.amount_paid) : 0;

            document.getElementById('payBookingId').value = b.id;
            document.getElementById('payInvoiceNum').textContent = pay ? pay.invoice_number : 'N/A';
            document.getElementById('payGuestName').textContent = b.customer ? b.customer.full_name : 'N/A';
            document.getElementById('payBalanceDue').textContent = `₹${balance.toLocaleString('en-IN')}`;
            document.getElementById('payAmount').value = balance;

            this.showModal('modalRecordPayment');
        } catch (err) {
            this.showToast(err.message, 'danger');
        }
    },

    handlePaymentSubmit: async function(e) {
        e.preventDefault();
        const bookingId = document.getElementById('payBookingId').value;
        const payload = {
            amount: parseFloat(document.getElementById('payAmount').value),
            payment_method: document.getElementById('payMethod').value,
            notes: document.getElementById('payNotes').value.trim()
        };

        try {
            await this.apiCall(`/billing/payments/${bookingId}`, 'POST', payload);
            this.showToast('Payment recorded successfully!');
            this.closeModal('modalRecordPayment');
            this.loadBillingData();
        } catch (err) {
            this.showToast(err.message, 'danger');
        }
    },

    viewInvoice: async function(bookingId) {
        try {
            const inv = await this.apiCall(`/billing/invoice/${bookingId}`);

            document.getElementById('invNumber').textContent = inv.invoice_number;
            document.getElementById('invDate').textContent = inv.invoice_date;
            document.getElementById('invBookingCode').textContent = inv.booking_code;
            document.getElementById('invStatusBadge').textContent = inv.payment_status;
            document.getElementById('invStatusBadge').className = `badge ${inv.payment_status === 'Paid' ? 'badge-success' : 'badge-danger'}`;

            document.getElementById('invCustomerName').textContent = inv.customer_name;
            document.getElementById('invCustomerEmail').textContent = inv.customer_email;
            document.getElementById('invCustomerPhone').textContent = inv.customer_phone;
            document.getElementById('invCustomerAddress').textContent = inv.customer_address || 'Address on file';

            document.getElementById('invRoom').textContent = `Room ${inv.room_number} (${inv.room_type})`;
            document.getElementById('invCheckIn').textContent = inv.check_in_date;
            document.getElementById('invCheckOut').textContent = inv.check_out_date;
            document.getElementById('invNights').textContent = inv.total_nights;
            document.getElementById('invGuests').textContent = inv.guests_count;

            document.getElementById('invRoomDesc').textContent = `${inv.room_type} Room Charges`;
            document.getElementById('invRoomSub').textContent = `Room ${inv.room_number} for ${inv.total_nights} night(s)`;
            document.getElementById('invRate').textContent = `₹${inv.price_per_night.toLocaleString('en-IN')}`;
            document.getElementById('invNightsCount').textContent = inv.total_nights;
            document.getElementById('invRoomCharges').textContent = `₹${inv.room_charges.toLocaleString('en-IN')}`;

            document.getElementById('invSubtotal').textContent = `₹${inv.room_charges.toLocaleString('en-IN')}`;
            document.getElementById('invDiscount').textContent = `-₹${inv.discount_amount.toLocaleString('en-IN')}`;
            document.getElementById('invTax').textContent = `₹${inv.tax_amount.toLocaleString('en-IN')}`;
            document.getElementById('invNetTotal').textContent = `₹${inv.total_amount.toLocaleString('en-IN')}`;
            document.getElementById('invAmountPaid').textContent = `₹${inv.amount_paid.toLocaleString('en-IN')}`;
            document.getElementById('invBalanceDue').textContent = `₹${inv.balance_due.toLocaleString('en-IN')}`;

            document.getElementById('invPayMethod').textContent = inv.payment_method;
            document.getElementById('invNotes').textContent = inv.notes || 'Standard stay folio terms apply.';

            this.showModal('modalInvoice');
        } catch (err) {
            this.showToast(`Failed to load invoice: ${err.message}`, 'danger');
        }
    },

    // =========================================================================
    // 7. BOOKING HISTORY MODULE
    // =========================================================================
    loadBookingHistory: async function() {
        try {
            const search = document.getElementById('historySearchInput')?.value || '';
            const query = search.trim() ? `?search=${encodeURIComponent(search.trim())}` : '';

            const history = await this.apiCall(`/reservations${query}`);
            const tbody = document.querySelector('#historyTable tbody');

            if (history.length === 0) {
                tbody.innerHTML = `<tr><td colspan="10" class="text-center py-4 text-muted">No historical records found.</td></tr>`;
                return;
            }

            tbody.innerHTML = history.map(b => `
                <tr>
                    <td><strong>${b.booking_code}</strong></td>
                    <td>${b.customer ? b.customer.full_name : 'N/A'}</td>
                    <td>Room ${b.room ? b.room.room_number : 'N/A'}</td>
                    <td>${b.check_in_date}</td>
                    <td>${b.check_out_date}</td>
                    <td>${b.total_nights} Nights</td>
                    <td>${this.renderStatusBadge(b.booking_status)}</td>
                    <td>${this.renderPaymentBadge(b.payment?.payment_status || 'Pending')}</td>
                    <td><strong>₹${(b.payment ? b.payment.total_amount : 0).toLocaleString('en-IN')}</strong></td>
                    <td>
                        <button class="btn btn-outline btn-sm" onclick="app.viewInvoice(${b.id})" title="View Folio">
                            <i class="fa-solid fa-receipt"></i>
                        </button>
                    </td>
                </tr>
            `).join('');

        } catch (err) {
            this.showToast(`Error loading history: ${err.message}`, 'danger');
        }
    },

    // =========================================================================
    // 8. ADVANCED MODULES PLACEHOLDERS
    // =========================================================================
    renderPlaceholderView: function(moduleKey) {
        const titleEl = document.getElementById('placeholderTitle');
        const descEl = document.getElementById('placeholderDesc');
        const iconEl = document.getElementById('placeholderIcon');
        const spec1 = document.getElementById('placeholderSpec1');
        const spec2 = document.getElementById('placeholderSpec2');
        const spec3 = document.getElementById('placeholderSpec3');

        const configs = {
            'staff': {
                title: 'Staff & Shift Management',
                desc: 'Employee rosters, duty schedules, payroll tracking, and role-based permissions.',
                icon: 'fa-user-tie',
                s1: 'Staff schema with roles: Front Desk, Housekeeping, Concierge, Maintenance',
                s2: 'Shift scheduler with check-in timestamping and attendance tracking',
                s3: 'Role-based access controls (RBAC) integration'
            },
            'housekeeping': {
                title: 'Housekeeping & Room Turnaround',
                desc: 'Real-time room cleaning requests, linen changes, and housekeeping dispatch.',
                icon: 'fa-broom',
                s1: 'Live room cleanliness state tracking (Clean, Dirty, Inspected)',
                s2: 'Automatic dirty state trigger upon guest checkout',
                s3: 'Housekeeper task queue and mobile assignment panel'
            },
            'restaurant': {
                title: 'Restaurant & Bar Point-of-Sale (POS)',
                desc: 'Table reservations, dine-in ordering, and room-service billing integrated with guest folio.',
                icon: 'fa-utensils',
                s1: 'Menu management with item categories and real-time inventory deduction',
                s2: 'Table mapping and dining reservation scheduling',
                s3: 'Direct charge-to-room capability posting to guest invoice'
            },
            'inventory': {
                title: 'Hotel Inventory & Asset Management',
                desc: 'Toiletries, minibar stocks, linen lifecycle, and supplier purchase orders.',
                icon: 'fa-boxes-stacked',
                s1: 'Asset category tree with low-stock automatic reorder warnings',
                s2: 'Room minibar stock audits during guest checkout',
                s3: 'Vendor catalog and procurement invoice management'
            },
            'maintenance': {
                title: 'Facility Maintenance & Work Orders',
                desc: 'Preventative equipment maintenance, plumbing/HVAC tickets, and room downtime logs.',
                icon: 'fa-screwdriver-wrench',
                s1: 'Automatic room state transition to Maintenance blocking bookings',
                s2: 'Maintenance technician ticket assignments with priority flags',
                s3: 'Equipment maintenance history and service logs'
            },
            'offers': {
                title: 'Promotions, Offers & Loyalty Engine',
                desc: 'Coupon codes, seasonal discounts, corporate discount packages, and guest reward points.',
                icon: 'fa-tags',
                s1: 'Coupon code validator with expiry and minimum spend checks',
                s2: 'Frequent flyer and repeat guest points ledger',
                s3: 'Dynamic weekend and holiday pricing rules'
            },
            'reports': {
                title: 'Executive Reports & Analytics',
                desc: 'RevPAR, ADR, occupancy trends, and financial year-end statements.',
                icon: 'fa-file-chart-column',
                s1: 'Occupancy rate (OR) and Average Daily Rate (ADR) calculator',
                s2: 'Revenue Per Available Room (RevPAR) monthly breakdown',
                s3: 'Automated PDF summary generator for hotel owners'
            },
            'settings': {
                title: 'Property & System Settings',
                desc: 'Hotel contact particulars, tax rates (GST/VAT), currency units, and database backups.',
                icon: 'fa-gear',
                s1: 'Configurable hotel name, address, logo, and phone contact on invoices',
                s2: 'Custom tax percentage and invoice serial number formatting',
                s3: 'Neon cloud database synchronization and backup controls'
            }
        };

        const config = configs[moduleKey] || configs['staff'];
        titleEl.textContent = config.title;
        descEl.textContent = config.desc;
        iconEl.className = `fa-solid ${config.icon}`;
        spec1.textContent = config.s1;
        spec2.textContent = config.s2;
        spec3.textContent = config.s3;

        document.querySelectorAll('.view-section').forEach(sec => sec.classList.remove('active'));
        document.getElementById('view-placeholder').classList.add('active');

        document.getElementById('pageTitle').textContent = config.title;
        document.getElementById('pageSubtitle').textContent = 'Enterprise Roadmap Module (Coming Soon)';
    },

    // =========================================================================
    // MODAL HELPERS
    // =========================================================================
    showModal: function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');

            if (modalId === 'modalRoom' && !document.getElementById('roomEditId').value) {
                document.getElementById('formRoom').reset();
                document.getElementById('roomModalTitle').innerHTML = '<i class="fa-solid fa-bed"></i> Add New Room';
            }
            if (modalId === 'modalCustomer' && !document.getElementById('customerEditId').value) {
                document.getElementById('formCustomer').reset();
                document.getElementById('customerModalTitle').innerHTML = '<i class="fa-solid fa-user-plus"></i> Register Customer';
            }
            if (modalId === 'modalNewReservation') {
                this.prepareReservationModal();
            }
        }
    },

    closeModal: function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
            if (modalId === 'modalRoom') document.getElementById('roomEditId').value = '';
            if (modalId === 'modalCustomer') document.getElementById('customerEditId').value = '';
        }
    },

    // =========================================================================
    // BADGE RENDERING HELPERS
    // =========================================================================
    renderStatusBadge: function(status) {
        switch(status) {
            case 'Confirmed':
                return '<span class="badge badge-info"><i class="fa-solid fa-clock"></i> Confirmed</span>';
            case 'Checked-In':
                return '<span class="badge badge-success"><i class="fa-solid fa-key"></i> Checked-In</span>';
            case 'Checked-Out':
                return '<span class="badge badge-secondary"><i class="fa-solid fa-check"></i> Checked-Out</span>';
            case 'Cancelled':
                return '<span class="badge badge-danger"><i class="fa-solid fa-ban"></i> Cancelled</span>';
            default:
                return `<span class="badge badge-secondary">${status}</span>`;
        }
    },

    renderPaymentBadge: function(status) {
        switch(status) {
            case 'Paid':
                return '<span class="badge badge-success"><i class="fa-solid fa-circle-check"></i> Paid</span>';
            case 'Partially Paid':
                return '<span class="badge badge-warning"><i class="fa-solid fa-circle-half-stroke"></i> Partially Paid</span>';
            case 'Pending':
                return '<span class="badge badge-danger"><i class="fa-solid fa-hourglass-half"></i> Pending</span>';
            default:
                return `<span class="badge badge-secondary">${status}</span>`;
        }
    },

    renderRoomStatusBadge: function(status) {
        switch(status) {
            case 'Available':
                return '<span class="badge badge-success"><i class="fa-solid fa-check-circle"></i> Available</span>';
            case 'Occupied':
                return '<span class="badge badge-danger"><i class="fa-solid fa-user-lock"></i> Occupied</span>';
            case 'Maintenance':
                return '<span class="badge badge-warning"><i class="fa-solid fa-wrench"></i> Maintenance</span>';
            default:
                return `<span class="badge badge-secondary">${status}</span>`;
        }
    }
};

// Initialize when DOM content is ready
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});
