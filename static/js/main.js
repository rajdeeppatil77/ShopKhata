/* ============================================================
   ShopKhata — Main Application JavaScript
   Mobile Responsive Navigation & Dynamic Interactions
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {

  /* ---- Mobile Sidebar Drawer Controller ---- */
  const sidebar = document.getElementById('sidebar');
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
  let overlay = document.getElementById('sidebarOverlay');

  // Fallback: create backdrop overlay if not in HTML
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'sidebarOverlay';
    document.body.appendChild(overlay);
  }

  function openSidebar() {
    if (sidebar) {
      sidebar.classList.add('show');
      overlay.classList.add('show');
      document.body.style.overflow = 'hidden';
    }
  }

  function closeSidebar() {
    if (sidebar) {
      sidebar.classList.remove('show');
      overlay.classList.remove('show');
      document.body.style.overflow = '';
    }
  }

  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function (e) {
      e.preventDefault();
      if (sidebar && sidebar.classList.contains('show')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
  }

  if (sidebarCloseBtn) {
    sidebarCloseBtn.addEventListener('click', function (e) {
      e.preventDefault();
      closeSidebar();
    });
  }

  overlay.addEventListener('click', closeSidebar);

  // Close sidebar on pressing Escape
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && sidebar && sidebar.classList.contains('show')) {
      closeSidebar();
    }
  });

  // Close mobile drawer when clicking any navigation link
  if (sidebar) {
    sidebar.querySelectorAll('.nav-link, .btn').forEach(function (link) {
      link.addEventListener('click', function () {
        if (window.innerWidth < 992) {
          closeSidebar();
        }
      });
    });
  }

  /* ---- Auto-Dismiss Flash Alerts after 4 Seconds ---- */
  document.querySelectorAll('[data-auto-dismiss]').forEach(function (el) {
    setTimeout(function () {
      try {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
        if (bsAlert) bsAlert.close();
      } catch (err) {}
    }, 4000);
  });

  /* ---- Confirmation Dialogs ---- */
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      const msg = el.getAttribute('data-confirm') || 'Are you sure?';
      if (!window.confirm(msg)) {
        e.preventDefault();
      }
    });
  });

  /* ---- Default Date Inputs to Today ---- */
  document.querySelectorAll('input[type="date"][data-default-today], input[type="date"].today-default').forEach(function (el) {
    if (!el.value) {
      const today = new Date().toISOString().split('T')[0];
      el.value = today;
    }
  });

});
