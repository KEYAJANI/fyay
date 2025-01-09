const scrollers = document.querySelectorAll(".scroller");

if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
  addAnimation();
}

function addAnimation() {
  scrollers.forEach((scroller) => {
    scroller.setAttribute("data-animated", true);

    // Use `querySelectorAll` scoped to the current scroller
    const scrollerInner = scroller.querySelectorAll(".scroller-inner");

    // Ensure scrollerInner is properly processed
    scrollerInner.forEach((inner) => {
      // Collect all children of scrollerInner
      const scrollerContent = Array.from(inner.children);

      // Clone and append the content
      scrollerContent.forEach((item) => {
        const duplicatedItem = item.cloneNode(true);
        duplicatedItem.setAttribute("aria-hidden", true);
        inner.appendChild(duplicatedItem);
      });
    });
  });
}

const sliders = document.querySelectorAll(".question-card");

function questionSlider() {
  sliders.forEach((slider) => {
    slider.addEventListener("click", () => {
      // Check if the current slider is active
      const isActive = slider.getAttribute("data-set") === "true";

      // Remove "data-set" and reset icons for all sliders
      sliders.forEach((otherSlider) => {
        otherSlider.setAttribute("data-set", false);
        const icon = otherSlider.querySelector(
          ".question-container-second-column-question-icon"
        );
        if (icon) icon.textContent = "+"; // Reset to "+"
      });

      // If the current slider wasn't active, activate it
      if (!isActive) {
        slider.setAttribute("data-set", true);
        const icon = slider.querySelector(
          ".question-container-second-column-question-icon"
        );
        if (icon) icon.textContent = "-"; // Change to "-"
      }
    });
  });
}

questionSlider();

addAnimation();
