/* ============================================
   RecoVolt — Worker-specific JavaScript
   ============================================ */

document.addEventListener("DOMContentLoaded", function () {

    // ── Status update confirmation ──
    const statusForm = document.querySelector("form");
    const statusSelect = document.querySelector("select[name='status']");
    if (statusForm && statusSelect) {
        statusSelect.addEventListener("change", function () {
            const val = statusSelect.value;
            if (val === "resolved") {
                const notesField = document.querySelector("textarea[name='notes']");
                if (notesField) {
                    notesField.setAttribute("placeholder",
                        "Please describe the work done to resolve this complaint...");
                }
            }
        });
    }

    // ── Highlight high priority jobs ──
    const priorityHighCells = document.querySelectorAll(".priority-high");
    priorityHighCells.forEach(function (cell) {
        const row = cell.closest("tr");
        if (row) {
            row.style.borderLeft = "3px solid #d32f2f";
        }
    });

});
