/* ============================================
   RecoVolt — Admin-specific JavaScript
   ============================================ */

document.addEventListener("DOMContentLoaded", function () {

    // ── Worker assignment confirmation ──
    const assignForm = document.querySelector("form[action*='assign']");
    if (assignForm) {
        assignForm.addEventListener("submit", function (e) {
            const workerSelect = assignForm.querySelector("select[name='worker_id']");
            if (workerSelect && !workerSelect.value) {
                e.preventDefault();
                alert("Please select a worker to assign.");
                return;
            }
            const selectedText = workerSelect.options[workerSelect.selectedIndex].text;
            if (!confirm("Assign " + selectedText + " to this complaint?\nThey will be notified via email.")) {
                e.preventDefault();
            }
        });
    }

    // ── Reports: highlight highest values ──
    const reportCards = document.querySelectorAll(".card-body .d-flex");
    let maxVal = 0;
    let maxEl = null;
    reportCards.forEach(function (row) {
        const strong = row.querySelector("strong");
        if (strong) {
            const val = parseInt(strong.textContent, 10);
            if (val > maxVal) {
                maxVal = val;
                maxEl = strong;
            }
        }
    });
    if (maxEl && maxVal > 0) {
        maxEl.style.color = "#d32f2f";
        maxEl.style.fontSize = "1.1rem";
    }

});
