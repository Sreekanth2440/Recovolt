/* ============================================
   RecoVolt — Main JavaScript
   ============================================ */

document.addEventListener("DOMContentLoaded", function () {

    // ── Dark mode toggle ──
    const themeToggle = document.getElementById("themeToggle");
    const themeIcon = document.getElementById("themeIcon");

    function updateThemeIcon(theme) {
        if (!themeIcon) return;
        themeIcon.className = theme === "dark" ? "bi bi-sun-fill" : "bi bi-moon-fill";
    }

    updateThemeIcon(document.documentElement.getAttribute("data-theme") || "light");

    if (themeToggle) {
        themeToggle.addEventListener("click", function () {
            const html = document.documentElement;
            const current = html.getAttribute("data-theme") || "light";
            const next = current === "dark" ? "light" : "dark";
            html.setAttribute("data-theme", next);
            localStorage.setItem("recovolt-theme", next);
            updateThemeIcon(next);
        });
    }

    // ── Auto-dismiss flash messages after 5 seconds ──
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.style.transition = "opacity 0.5s ease, transform 0.5s ease";
            alert.style.opacity = "0";
            alert.style.transform = "translateY(-10px)";
            setTimeout(function () {
                alert.remove();
            }, 500);
        }, 5000);
    });

    // ── Confirm dialogs for dangerous actions ──
    const confirmBtns = document.querySelectorAll("[data-confirm]");
    confirmBtns.forEach(function (btn) {
        btn.addEventListener("click", function (e) {
            const message = btn.getAttribute("data-confirm") || "Are you sure?";
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // ── Sidebar toggle for mobile ──
    const sidebarToggle = document.getElementById("sidebarToggle");
    const sidebar = document.querySelector(".sidebar");
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener("click", function () {
            sidebar.classList.toggle("show");
        });

        // Close sidebar on outside click (mobile)
        document.addEventListener("click", function (e) {
            if (
                sidebar.classList.contains("show") &&
                !sidebar.contains(e.target) &&
                e.target !== sidebarToggle
            ) {
                sidebar.classList.remove("show");
            }
        });
    }

    // ── Image preview on file upload ──
    const imageInput = document.getElementById("image");
    const imagePreview = document.getElementById("imagePreview");
    if (imageInput && imagePreview) {
        imageInput.addEventListener("change", function () {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    imagePreview.src = e.target.result;
                    imagePreview.style.display = "block";
                };
                reader.readAsDataURL(file);
            }
        });
    }

});
