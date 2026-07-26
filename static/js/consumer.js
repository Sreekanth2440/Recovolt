/* ============================================
   RecoVolt — Consumer-specific JavaScript
   ============================================ */

document.addEventListener("DOMContentLoaded", function () {

    // ── Character counter for complaint description ──
    const description = document.querySelector("textarea[name='description']");
    if (description) {
        const counter = document.createElement("small");
        counter.className = "text-muted";
        counter.textContent = "0 characters";
        description.parentNode.appendChild(counter);

        description.addEventListener("input", function () {
            const len = description.value.length;
            counter.textContent = len + " characters";
            if (len < 20) {
                counter.className = "text-danger";
            } else {
                counter.className = "text-success";
            }
        });
    }

    // ── Star rating hover preview ──
    const starLabels = document.querySelectorAll(".star-rating label");
    starLabels.forEach(function (label) {
        label.addEventListener("mouseenter", function () {
            label.style.transform = "scale(1.2)";
        });
        label.addEventListener("mouseleave", function () {
            label.style.transform = "scale(1)";
        });
    });

});
