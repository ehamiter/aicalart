// Constants
const baseImageUrl = "https://aicalart.s3.amazonaws.com/images/";
const swipeXThreshold = 100;
const swipeYThreshold = 110;

// Calendar state variables
let calendarDisplayMonth;
let calendarDisplayYear;

// Orientation override state variable
let manualOrientationOverride = null; // null = use device orientation, 'portrait' or 'landscape' = forced

// Function to get current orientation (considering manual override)
function getCurrentOrientation() {
  if (manualOrientationOverride) {
    return manualOrientationOverride;
  }
  return window.matchMedia("(orientation: portrait)").matches ? 'portrait' : 'landscape';
}

// Function to toggle orientation override
function toggleOrientation() {
  if (manualOrientationOverride === null) {
    // First toggle: set to opposite of current device orientation
    const currentDeviceOrientation = window.matchMedia("(orientation: portrait)").matches ? 'portrait' : 'landscape';
    manualOrientationOverride = currentDeviceOrientation === 'portrait' ? 'landscape' : 'portrait';
  } else if (manualOrientationOverride === 'portrait') {
    manualOrientationOverride = 'landscape';
  } else {
    manualOrientationOverride = 'portrait';
  }
  
  // Update the image immediately
  updateImageTitleAndBackground();
  console.log('Orientation toggled to:', manualOrientationOverride);
}

// Date and URL functions
// Function to check if Daylight Saving Time (DST) is in effect
function isDST(date = new Date()) {
  const january = new Date(date.getFullYear(), 0, 1).getTimezoneOffset();
  const july = new Date(date.getFullYear(), 6, 1).getTimezoneOffset();
  return Math.min(january, july) !== date.getTimezoneOffset();
}

// Function to get the current date with a buffer to account for cron job timing
function getCurrentDateWithBuffer(bufferHours = 2) {
  let currentDate = new Date();
  if (isDST(currentDate)) {
    bufferHours += 1; // Add extra hour during DST
  }
  currentDate.setHours(currentDate.getHours() - bufferHours);
  return currentDate;
}

// Function to format date to YYYY-MM-DD
function formatDate(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

// Function to format date to a long date string (e.g., November 25, 2023)
function formatToLongDate(date) {
  const options = { year: 'numeric', month: 'long', day: 'numeric' };
  return date.toLocaleDateString('en-US', options);
}

// Get the current date with the buffer
let currentDate = getCurrentDateWithBuffer();

// Format and log the date (you can use these functions wherever needed in your code)
let formattedDate = formatDate(currentDate); // Outputs: YYYY-MM-DD
let longFormattedDate = formatToLongDate(currentDate); // Outputs: Month Day, Year

// console.log(formattedDate);
// console.log(longFormattedDate);

function extractDateFromUrl() {
  const hash = window.location.hash;
  const datePattern = /^#(\d{4}-\d{2}-\d{2})$/;
  const match = hash.match(datePattern);
  if (!match) return;

  const [year, month, day] = match[1].split('-').map(num => parseInt(num, 10));
  currentDate = new Date(year, month - 1, day);
}

async function loadPrompts(dateString, orientation) {
  const promptUrl = `https://aicalart.s3.amazonaws.com/prompts/${dateString}-prompt.json`;
  try {
    const response = await fetch(promptUrl);
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    const promptData = await response.json();
    return {
      bgFile: `url('${baseImageUrl}${dateString}-${orientation}.webp')`,
      text: promptData[orientation],
      holidays: promptData["holidays"],
      style: promptData["style"] || ''
    };
  } catch (error) {
    console.error("Error fetching or parsing data:", error);
    return null;
  }
}

function generateCalendar(year, month) {
  const calendarGrid = document.querySelector('#jumpToDateModal .calendar-grid');
  const monthYearDisplay = document.getElementById('currentMonthYear');
  if (!calendarGrid || !monthYearDisplay) return;

  // Update month/year display
  const displayDate = new Date(year, month);
  monthYearDisplay.textContent = displayDate.toLocaleString('default', { month: 'long', year: 'numeric' });

  // Store weekday headers and then clear grid
  const weekdayHeaders = calendarGrid.querySelectorAll('.calendar-weekday');
  const weekdayHeaderHTML = Array.from(weekdayHeaders)
                                 .map(node => node.outerHTML).join('');
  calendarGrid.innerHTML = ''; // Clear all content
  calendarGrid.innerHTML = weekdayHeaderHTML; // Re-add headers first

  const firstDayOfMonth = new Date(year, month, 1).getDay(); // 0 (Sun) - 6 (Sat)
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const earliestAllowedDate = new Date('2023-11-25T00:00:00-06:00');
  earliestAllowedDate.setHours(0, 0, 0, 0);
  const latestAllowedDate = getCurrentDateWithBuffer();
  latestAllowedDate.setHours(0, 0, 0, 0);

  const currentViewDateNormalized = new Date(currentDate.getTime());
  currentViewDateNormalized.setHours(0, 0, 0, 0);

  // Add empty cells for days before the 1st of the month
  for (let i = 0; i < firstDayOfMonth; i++) {
    const emptyCell = document.createElement('div');
    emptyCell.classList.add('calendar-day', 'empty');
    calendarGrid.appendChild(emptyCell);
  }

  // Add day cells
  for (let day = 1; day <= daysInMonth; day++) {
    const cell = document.createElement('div');
    cell.classList.add('calendar-day');
    cell.textContent = day;
    const cellDate = new Date(year, month, day);
    cellDate.setHours(0,0,0,0); // Normalize cell date for comparison

    cell.dataset.date = formatDate(cellDate); // YYYY-MM-DD

    if (cellDate < earliestAllowedDate || cellDate > latestAllowedDate) {
      cell.classList.add('disabled');
    }

    if (cellDate.getTime() === currentViewDateNormalized.getTime()) {
      cell.classList.add('current-view-date');
    }

    if (!cell.classList.contains('disabled')) {
      cell.addEventListener('click', () => {
        const [y, m, d] = cell.dataset.date.split('-').map(Number);
        currentDate = new Date(y, m - 1, d);

        updateImageTitleAndBackground();
        updateNavigationArrowStates();
        updatePromptButtonText(); // Ensure prompt button text is correct
        toggleModal('jumpToDateModal', false);
        // window.location.hash = formatDate(currentDate); // Optional: update URL hash
      });
    }
    calendarGrid.appendChild(cell);
  }

  // Add empty cells to fill the grid (total cells = weekdays + days + empty_before)
  const totalCells = weekdayHeaders.length + firstDayOfMonth + daysInMonth;
  const remainingCells = (Math.ceil(totalCells / 7) * 7) - totalCells;
  for (let i = 0; i < remainingCells; i++) {
     const emptyCell = document.createElement('div');
     emptyCell.classList.add('calendar-day', 'empty');
     calendarGrid.appendChild(emptyCell);
  }

  // Update month navigation button states
  const prevMonthBtn = document.getElementById('prevMonthBtn');
  const nextMonthBtn = document.getElementById('nextMonthBtn');
  if (!prevMonthBtn || !nextMonthBtn) return;

  // Disable prev if current month/year is at or before earliest allowed month/year
  if (year < earliestAllowedDate.getFullYear() || (year === earliestAllowedDate.getFullYear() && month <= earliestAllowedDate.getMonth())) {
    prevMonthBtn.disabled = true;
  } else {
    prevMonthBtn.disabled = false;
  }

  // Disable next if current month/year is at or after latest allowed month/year
  if (year > latestAllowedDate.getFullYear() || (year === latestAllowedDate.getFullYear() && month >= latestAllowedDate.getMonth())) {
    nextMonthBtn.disabled = true;
  } else {
    nextMonthBtn.disabled = false;
  }
}

// Function to update the text of the prompt toggle button
function updatePromptButtonText() {
  const promptModal = document.getElementById('promptModal');
  const promptButton = document.getElementById('promptToggleButton');
  if (!promptButton || !promptModal) return; // Safety check

  if (promptModal.classList.contains('modal-visible')) {
    promptButton.textContent = 'Hide Prompt';
  } else {
    promptButton.textContent = 'View Prompt';
  }
}

async function updateImageTitleAndBackground() {
  const dateString = formatDate(currentDate);
  const orientation = getCurrentOrientation();

  try {
    const prompts = await loadPrompts(dateString, orientation);
    if (!prompts) return;

    document.querySelector('.bg-image').style.backgroundImage = prompts.bgFile;
    document.getElementById('modalDate').textContent = formatToLongDate(currentDate);
    document.getElementById('modalText').textContent = prompts.text;
    document.getElementById('modalHolidays').textContent = prompts.holidays;
    document.getElementById('modalStyle').textContent = prompts.style || '';
    
    // Reset prompt modal scroll position to top when content changes
    const promptModal = document.getElementById('promptModal');
    if (promptModal) {
      promptModal.scrollTop = 0;
    }
  } catch (error) {
    console.error('Fetch failed: ', error);
  }
}

// Date navigation functions
function changeDate(days) {
  const newDate = new Date(currentDate.getTime());
  newDate.setDate(newDate.getDate() + days);

  // Determine the valid date range
  const maxDate = getCurrentDateWithBuffer(); // Latest accessible date based on buffer
  maxDate.setHours(23, 59, 59, 999); // Compare against the end of that day

  const minDate = new Date('2023-11-25T00:00:00-06:00');
  minDate.setHours(0, 0, 0, 0); // Compare against the start of that day

  // Update currentDate only if newDate is within the valid range
  if (newDate >= minDate && newDate <= maxDate) {
    currentDate = newDate;
    updateImageTitleAndBackground();
  } else {
    // If newDate is outside the range, currentDate does not change.
    // Log if we are trying to go out of bounds.
    // This can happen if a user rapidly clicks, or if there's a logic flaw elsewhere.
    // We don't return, so updateNavigationArrowStates is still called.
    console.error('Attempted to navigate out of bounds. Date not changed. newDate:', newDate, 'minDate:', minDate, 'maxDate:', maxDate);
  }

  updateNavigationArrowStates(); // Always update arrow states
}

// Modal handling functions
function toggleModal(modalId, forceShow) {
  const modal = document.getElementById(modalId);
  if (!modal) {
    console.error("Modal not found: ", modalId);
    return;
  }

  // Get the modal container
  const modalContainer = modal.closest('.modal-container');

  // Remove any existing event listeners to prevent duplicates
  modal.removeEventListener('animationend', onAnimationEnd);

  // Determine current visibility to toggle or use the provided forceShow value
  const isVisible = modal.classList.contains('modal-visible');
  forceShow = forceShow !== undefined ? forceShow : !isVisible;

  // Prepare the modal by clearing any previously set animations
  modal.style.animation = 'none';
  modal.offsetHeight; // Trigger reflow

  function onAnimationEnd() {
    // Only update visibility when hiding
    if (!forceShow) {
      modal.classList.remove('modal-visible');
      modalContainer.classList.remove('active'); // Remove active class from container
    }
    modal.removeEventListener('animationend', onAnimationEnd);
  }

  if (forceShow) {
    modal.classList.add('modal-show', 'modal-visible');
    modal.classList.remove('modal-hide');
    modalContainer.classList.add('active'); // Add active class to container
  } else {
    modal.classList.add('modal-hide');
    modal.classList.remove('modal-show');
    // Listen for the end of the hide animation to remove visibility
    modal.addEventListener('animationend', onAnimationEnd);
  }

  // Reapply animation after setup
  modal.style.animation = '';
}

// Clipboard function
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    console.log('Copied URL to clipboard: ', text);
  }).catch(err => {
    console.error('Failed to copy text: ', err);
  });
}

// Initialization and event bindings
document.addEventListener('DOMContentLoaded', () => {
  extractDateFromUrl();
  updateImageTitleAndBackground();
  updateNavigationArrowStates(); // Initial call to set arrow states
  updatePromptButtonText(); // Initial call for prompt button text
  document.querySelector('.bg-image').style.animationPlayState = 'paused';

  document.addEventListener('keydown', handleKeyPress);
  document.addEventListener('touchstart', handleTouchStart);
  document.addEventListener('touchend', handleSwipeGesture);
  window.addEventListener("resize", updateImageTitleAndBackground);

  // Event listener for the prompt toggle button
  const promptToggleButton = document.getElementById('promptToggleButton');
  if (promptToggleButton) {
    promptToggleButton.addEventListener('click', () => {
      const modal = document.getElementById('promptModal');
      const button = document.getElementById('promptToggleButton');
      const isVisible = modal.classList.contains('modal-visible');
      toggleModal('promptModal', !isVisible);
      // Text update is now part of the listener itself.
      if (!isVisible) { // If it WASN'T visible, it is NOW visible
        button.textContent = 'Hide Prompt';
      } else { // If it WAS visible, it is NOW hidden
        button.textContent = 'View Prompt';
      }
    });
  }

  // Event listeners for navigation arrows
  const prevDayButton = document.getElementById('prevDayButton');
  if (prevDayButton) {
    prevDayButton.addEventListener('click', () => changeDate(-1));
  }

  const nextDayButton = document.getElementById('nextDayButton');
  if (nextDayButton) {
    nextDayButton.addEventListener('click', () => changeDate(1));
  }

  // Event listeners for Jump To Date Modal
  const prevMonthBtn = document.getElementById('prevMonthBtn');
  if (prevMonthBtn) {
    prevMonthBtn.addEventListener('click', () => {
      calendarDisplayMonth--;
      if (calendarDisplayMonth < 0) {
        calendarDisplayMonth = 11;
        calendarDisplayYear--;
      }
      generateCalendar(calendarDisplayYear, calendarDisplayMonth);
    });
  }
  const nextMonthBtn = document.getElementById('nextMonthBtn');
  if (nextMonthBtn) {
    nextMonthBtn.addEventListener('click', () => {
      calendarDisplayMonth++;
      if (calendarDisplayMonth > 11) {
        calendarDisplayMonth = 0;
        calendarDisplayYear++;
      }
      generateCalendar(calendarDisplayYear, calendarDisplayMonth);
    });
  }
  const jumpToDateModal = document.getElementById('jumpToDateModal');
  if (jumpToDateModal) {
    const closeJumpModalButton = jumpToDateModal.querySelector('.close');
    if (closeJumpModalButton) {
      closeJumpModalButton.onclick = function() {
        toggleModal('jumpToDateModal', false); // Explicitly hide
      }
    }
  }
});

function updateNavigationArrowStates() {
  const prevButton = document.getElementById('prevDayButton');
  const nextButton = document.getElementById('nextDayButton');
  if (!prevButton || !nextButton) return; // Safety check

  // Normalize currentDate for comparison (ignore time part)
  const currentNormalizedDate = new Date(currentDate.getTime());
  currentNormalizedDate.setHours(0, 0, 0, 0);

  const earliestDate = new Date('2023-11-25T00:00:00-06:00');
  earliestDate.setHours(0,0,0,0); // Normalize earliest date

  // Previous button state
  if (currentNormalizedDate <= earliestDate) {
    prevButton.classList.add('disabled');
  } else {
    prevButton.classList.remove('disabled');
  }

  // Next button state
  // getCurrentDateWithBuffer() gives today - buffer, which is the latest accessible date.
  let comparisonDateForNext = getCurrentDateWithBuffer();
  comparisonDateForNext.setHours(0,0,0,0); // Normalize it

  if (currentNormalizedDate >= comparisonDateForNext) {
    nextButton.classList.add('disabled');
  } else {
    nextButton.classList.remove('disabled');
  }
}

function handleKeyPress(event) {
  const modalMap = { 'p': 'promptModal', '?' : 'aboutModal' };

  if (event.key === 'Escape') {
    // Master dismissal for all modals
    const allModals = ['aboutModal', 'promptModal', 'jumpToDateModal'];
    for (const modalId of allModals) {
      const modal = document.getElementById(modalId);
      if (modal && modal.classList.contains('modal-visible')) {
        toggleModal(modalId, false);
        // Update prompt button text if we're closing the prompt modal
        if (modalId === 'promptModal') {
          const promptButton = document.getElementById('promptToggleButton');
          if (promptButton) {
            promptButton.textContent = 'View Prompt';
          }
        }
      }
    }
  } else if (event.key === 'j') {
    const jumpModal = document.getElementById('jumpToDateModal');
    // Check if jumpModal exists to prevent errors if HTML is somehow missing
    if (!jumpModal) return;

    if (jumpModal.classList.contains('modal-visible')) {
      toggleModal('jumpToDateModal', false); // Hide if already visible
    } else {
      calendarDisplayYear = currentDate.getFullYear();
      calendarDisplayMonth = currentDate.getMonth();
      generateCalendar(calendarDisplayYear, calendarDisplayMonth);
      toggleModal('jumpToDateModal', true); // Show
    }
  } else if (modalMap[event.key]) {
    const modal = document.getElementById(modalMap[event.key]);
    // Check if modal exists before trying to access its classList
    if (!modal) return;
    const isModalVisible = modal.classList.contains('modal-visible');
    toggleModal(modalMap[event.key], !isModalVisible);
  } else if (['k', 'q'].includes(event.key)) {
    handleKenBurnsEffect(event.key);
  } else if (['ArrowLeft', 'ArrowRight'].includes(event.key)) {
    changeDate(event.key === 'ArrowRight' ? 1 : -1);
  } else if (event.key === 'c') {
    const dateString = formatDate(currentDate);
    const orientation = getCurrentOrientation();
    const imageUrl = `${baseImageUrl}${dateString}-${orientation}.webp`;
    copyToClipboard(imageUrl);
  } else if (event.key === 't' || event.key === 'T') {
    toggleOrientation();
  }
}

function handleKenBurnsEffect(key) {
  const image = document.querySelector('.bg-image');
  const isPaused = image.style.animationPlayState === 'paused';
  if (key === 'k') image.style.animationPlayState = isPaused ? 'running' : 'paused';
  else resetKenBurnsEffect(image);
}

function resetKenBurnsEffect(image) {
  image.style.animation = 'none';
  image.offsetHeight; // Trigger reflow
  image.style.transform = 'scale(1)';
  image.style.backgroundPosition = '50% 50%';
  image.style.animation = 'kenburns 88s linear infinite';
  image.style.animationPlayState = 'paused';
}

function handleTouchStart(event) {
  if (event.touches.length !== 1) return;
  [touchstartX, touchstartY] = [event.touches[0].screenX, event.touches[0].screenY];
}

function handleSwipeGesture(event) {
  if (event.changedTouches.length !== 1) return;

  const touchendX = event.changedTouches[0].screenX;
  const touchendY = event.changedTouches[0].screenY;

  const swipeXDistance = Math.abs(touchendX - touchstartX);
  const swipeYDistance = Math.abs(touchendY - touchstartY);

  if (swipeXDistance > swipeYDistance && swipeXDistance > swipeXThreshold) {
    changeDate(touchendX < touchstartX ? 1 : -1);
  }
}
