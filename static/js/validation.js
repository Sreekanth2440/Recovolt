/* ============================================
   RecoVolt — Form Validation
   ============================================ */

document.addEventListener("DOMContentLoaded", function () {

    // ── Registration Form ──
    const registerForm = document.getElementById("registerForm");
    if (registerForm) {
        registerForm.addEventListener("submit", function (e) {
            const password = registerForm.querySelector("[name='password']");
            if (password && password.value.length < 6) {
                e.preventDefault();
                alert("Password must be at least 6 characters long.");
                password.focus();
                return;
            }

            const phone = registerForm.querySelector("[name='phone']");
            if (phone && !/^\d{10}$/.test(phone.value.replace(/\D/g, ''))) {
                e.preventDefault();
                alert("Please enter a valid 10-digit phone number.");
                phone.focus();
                return;
            }
        });
    }

    // ── Complaint Form ──
    const complaintForm = document.getElementById("complaintForm");
    if (complaintForm) {
        complaintForm.addEventListener("submit", function (e) {
            const title = complaintForm.querySelector("[name='title']");
            if (title && title.value.trim().length < 5) {
                e.preventDefault();
                alert("Title must be at least 5 characters.");
                title.focus();
                return;
            }

            const description = complaintForm.querySelector("[name='description']");
            if (description && description.value.trim().length < 20) {
                e.preventDefault();
                alert("Please provide a more detailed description (at least 20 characters).");
                description.focus();
                return;
            }

            const imageInput = complaintForm.querySelector("[name='image']");
            if (imageInput && imageInput.files.length > 0) {
                const file = imageInput.files[0];
                const allowed = ["image/png", "image/jpeg", "image/jpg", "image/gif", "image/webp"];
                if (!allowed.includes(file.type)) {
                    e.preventDefault();
                    alert("Only image files (PNG, JPG, GIF, WEBP) are allowed.");
                    return;
                }
                if (file.size > 5 * 1024 * 1024) {
                    e.preventDefault();
                    alert("Image must be smaller than 5 MB.");
                    return;
                }
            }
        });
    }

    // ── Feedback Form ──
    const feedbackForm = document.getElementById("feedbackForm");
    if (feedbackForm) {
        feedbackForm.addEventListener("submit", function (e) {
            const rating = feedbackForm.querySelector("[name='rating']:checked");
            if (!rating) {
                e.preventDefault();
                alert("Please select a rating.");
                return;
            }
        });
    }

    // ── Add Worker Form ──
    const workerForm = document.getElementById("workerForm");
    if (workerForm) {
        workerForm.addEventListener("submit", function (e) {
            const password = workerForm.querySelector("[name='password']");
            if (password && password.value && password.value.length < 6) {
                e.preventDefault();
                alert("Password must be at least 6 characters long.");
                password.focus();
                return;
            }
        });
    }

});
